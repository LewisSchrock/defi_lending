#!/usr/bin/env python3
"""
Parallel TVL Collector

Collects TVL snapshots for all CSUs across a date range using cached blocks.
Uses ThreadPoolExecutor for parallel collection with rate limiting.

Usage:
    python scripts/collect_tvl_parallel.py --start-date 2024-12-01 --end-date 2024-12-31
    python scripts/collect_tvl_parallel.py --start-date 2024-12-01 --end-date 2024-12-31 --csus aave_v3_ethereum compound_v3_ethereum
    python scripts/collect_tvl_parallel.py --resume  # Resume from checkpoint
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add parent to path BEFORE importing project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import Dict, List, Tuple, Optional
import yaml
from config.rpc_pool import get_web3

# Import TVL adapters
from adapters.tvl.aave_v3 import get_aave_v3_tvl
from adapters.tvl.compound_v3 import get_compound_v3_tvl
from adapters.tvl.compound_v2_style import (
    get_compound_style_tvl,
    get_venus_tvl as get_venus_compound_style,
    get_benqi_tvl,
    get_moonwell_tvl,
    get_kinetic_tvl,
    get_tectonic_tvl,
    get_sumer_tvl
)
from adapters.tvl.fluid import get_fluid_tvl
from adapters.tvl.gearbox import get_gearbox_tvl
from adapters.tvl.cap import get_cap_tvl
from adapters.tvl.lista import get_lista_tvl
from adapters.tvl.venus import get_venus_tvl

# Import POA middleware
try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        from web3.middleware import geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None

# Chain configurations
POA_CHAINS = ['binance', 'polygon', 'gnosis', 'avalanche', 'optimism', 'linea', 'scroll', 'xdai']
CHAIN_ALIASES = {
    'xdai': 'gnosis',
}

# Adapter mapping
ADAPTER_MAP = {
    'aave': get_aave_v3_tvl,
    'compound': get_compound_v3_tvl,
    'compound_v2': get_compound_style_tvl,
    'fluid': get_fluid_tvl,
    'gearbox': get_gearbox_tvl,
    'cap': get_cap_tvl,
    'lista': get_lista_tvl,
    'venus': get_venus_tvl,
    'sparklend': get_aave_v3_tvl,  # SparkLend is an Aave V3 fork
    'benqi': get_benqi_tvl,
    'moonwell': get_moonwell_tvl,
    'kinetic': get_kinetic_tvl,
    'tectonic': get_tectonic_tvl,
    'sumer': get_sumer_tvl,
}


def load_block_cache(chain: str, start_date: str, end_date: str) -> Dict[str, Dict]:
    """
    Load block cache for a specific chain and date range.
    Will try to find any cache file that covers the requested date range.

    Args:
        chain: Chain name (will be aliased if needed, e.g., xdai -> gnosis)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Dict mapping date strings to block info
    """
    # Apply chain alias if needed (e.g., xdai -> gnosis)
    cache_chain = CHAIN_ALIASES.get(chain, chain)

    # First try exact match
    cache_file = Path(f'data/cache/{cache_chain}_blocks_{start_date}_{end_date}.json')

    # If not found, try to find any cache file for this chain
    if not cache_file.exists():
        cache_dir = Path('data/cache')
        cache_pattern = f'{cache_chain}_blocks_*.json'
        matching_caches = list(cache_dir.glob(cache_pattern))

        if matching_caches:
            # Sort by file size (descending) to prefer larger/fuller caches
            matching_caches.sort(key=lambda p: p.stat().st_size, reverse=True)
            cache_file = matching_caches[0]
        else:
            raise FileNotFoundError(f"No block cache found for {chain} (looked for {cache_chain})")

    with open(cache_file) as f:
        cache = json.load(f)

    # Filter cache to only requested dates if needed
    if start_date != end_date or len(cache) > len(list(iterate_dates(start_date, end_date))):
        requested_dates = set(iterate_dates(start_date, end_date))
        cache = {date: info for date, info in cache.items() if date in requested_dates}

    return cache


def load_csu_config() -> Dict:
    """Load CSU configuration from YAML file."""
    config_file = Path('code/config/csu_config.yaml')

    with open(config_file) as f:
        config = yaml.safe_load(f)

    return config.get('csus', config)


def load_deployment_dates() -> Dict[str, str]:
    """
    Load deployment dates from YAML file.

    Returns:
        Dict mapping CSU names to deployment dates (YYYY-MM-DD)
    """
    deployment_file = Path('code/config/deployment_dates.yaml')

    if not deployment_file.exists():
        return {}

    with open(deployment_file) as f:
        config = yaml.safe_load(f)

    return config.get('csus', {})


def should_collect_date(csu_name: str, date_str: str, deployment_dates: Dict[str, str]) -> bool:
    """
    Check if we should collect data for this CSU on this date.

    Returns False if the contract wasn't deployed yet on this date.
    """
    if csu_name not in deployment_dates:
        # No deployment date recorded, assume it existed before our collection period
        return True

    deployment_date = deployment_dates[csu_name]
    return date_str >= deployment_date


def iterate_dates(start_str: str, end_str: str):
    """Yield YYYY-MM-DD strings from start to end (inclusive)"""
    d0 = date.fromisoformat(start_str)
    d1 = date.fromisoformat(end_str)
    d = d0
    while d <= d1:
        yield d.isoformat()
        d += timedelta(days=1)


def get_adapter_for_csu(csu_config: Dict) -> Optional[callable]:
    """
    Get the appropriate TVL adapter function for a CSU.

    Args:
        csu_config: CSU configuration dict

    Returns:
        Adapter function or None if not found
    """
    protocol = csu_config.get('protocol', '').lower()
    version = csu_config.get('version', '').lower()

    # Try exact protocol match
    if protocol in ADAPTER_MAP:
        return ADAPTER_MAP[protocol]

    # Try protocol_version match
    protocol_version = f"{protocol}_{version}"
    if protocol_version in ADAPTER_MAP:
        return ADAPTER_MAP[protocol_version]

    # Special cases
    if protocol == 'compound' and version == 'v2':
        return ADAPTER_MAP['compound_v2']

    return None


def setup_web3_for_chain(chain: str):
    """
    Setup Web3 instance for a chain with appropriate middleware.

    Args:
        chain: Chain name

    Returns:
        Web3 instance
    """
    # Resolve chain alias
    rpc_chain = CHAIN_ALIASES.get(chain, chain)

    # Get web3 instance
    w3 = get_web3(rpc_chain)

    # Inject POA middleware if needed
    if chain in POA_CHAINS and geth_poa_middleware:
        try:
            if hasattr(w3, 'middleware_onion'):
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except Exception as e:
            print(f"[Warning] Could not inject POA middleware for {chain}: {e}")

    return w3


def is_retryable_error(error_str: str) -> bool:
    """
    Check if an error is retryable (rate limit or connection error).

    Args:
        error_str: Error message string

    Returns:
        True if the error is retryable
    """
    retryable_patterns = [
        '429',
        'Too Many Requests',
        'rate limit',
        'Connection aborted',
        'RemoteDisconnected',
        'Remote end closed',
        '503',
        '502',
        'Service Unavailable',
        'timeout',
        'timed out',
    ]
    error_lower = error_str.lower()
    return any(pattern.lower() in error_lower for pattern in retryable_patterns)


def collect_tvl_snapshot_with_retry(
    csu_name: str,
    csu_config: Dict,
    date_str: str,
    block_info: Dict,
    w3_cache: Dict,
    max_retries: int = 3,
    max_backoff: float = 5.0
) -> Tuple[str, str, Optional[Dict], Optional[str]]:
    """
    Collect TVL snapshot with automatic retry for rate limits and connection errors.

    Uses exponential backoff: 1s, 2s, 4s... capped at max_backoff.

    Args:
        csu_name: CSU identifier
        csu_config: CSU configuration
        date_str: Date string (YYYY-MM-DD)
        block_info: Block information for the date
        w3_cache: Cache of Web3 instances by chain (NOT USED - kept for compatibility)
        max_retries: Maximum number of retry attempts
        max_backoff: Maximum backoff time in seconds (default 5s)

    Returns:
        Tuple of (csu_name, date_str, data_dict, error_message)
    """
    last_error = None

    for attempt in range(max_retries + 1):
        result = collect_tvl_snapshot(csu_name, csu_config, date_str, block_info, w3_cache)
        _csu, _date, data, error = result

        # Success
        if data is not None:
            return result

        # Check if error is retryable
        if error and is_retryable_error(error):
            last_error = error
            if attempt < max_retries:
                # Exponential backoff: 1s, 2s, 4s... capped at max_backoff
                backoff = min(2 ** attempt, max_backoff)
                time.sleep(backoff)
                continue

        # Non-retryable error or max retries exceeded
        return result

    # Should not reach here, but just in case
    return (csu_name, date_str, None, last_error or "Max retries exceeded")


def collect_tvl_snapshot(
    csu_name: str,
    csu_config: Dict,
    date_str: str,
    block_info: Dict,
    w3_cache: Dict
) -> Tuple[str, str, Optional[Dict], Optional[str]]:
    """
    Collect TVL snapshot for a single CSU on a specific date.

    Args:
        csu_name: CSU identifier
        csu_config: CSU configuration
        date_str: Date string (YYYY-MM-DD)
        block_info: Block information for the date
        w3_cache: Cache of Web3 instances by chain (NOT USED - kept for compatibility)

    Returns:
        Tuple of (csu_name, date_str, data_dict, error_message)
    """
    try:
        chain = csu_config['chain']
        registry = csu_config['registry']
        block_number = block_info['block']
        protocol = csu_config.get('protocol', '')

        # CRITICAL: Get a FRESH Web3 instance on every call to rotate through API keys
        # This ensures we distribute load across all 5 Alchemy accounts
        w3 = setup_web3_for_chain(chain)

        # Get appropriate adapter
        adapter = get_adapter_for_csu(csu_config)
        if not adapter:
            return (csu_name, date_str, None, f"No adapter found for protocol: {protocol}")

        # Call adapter to get TVL data
        tvl_data = adapter(w3, registry, block_number)

        # Build bronze output
        output = {
            'csu': csu_name,
            'chain': chain,
            'protocol': protocol,
            'version': csu_config.get('version', ''),
            'date': date_str,
            'block': block_number,
            'timestamp': block_info['timestamp'],
            'ts_start_utc': block_info['ts_start_utc'],
            'ts_end_utc': block_info['ts_end_utc'],
            'num_markets': len(tvl_data) if isinstance(tvl_data, list) else 0,
            'data': tvl_data
        }

        return (csu_name, date_str, output, None)

    except Exception as e:
        return (csu_name, date_str, None, str(e))


def save_bronze_data(csu_name: str, date_str: str, data: Dict):
    """
    Save TVL data to bronze format.

    Args:
        csu_name: CSU identifier
        date_str: Date string
        data: TVL data dict
    """
    output_dir = Path(f'data/bronze/tvl/{csu_name}')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f'{date_str}.json'

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)


def load_checkpoint(checkpoint_file: Path) -> Dict:
    """Load checkpoint state."""
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            return json.load(f)
    return {'completed': [], 'failed': []}


def save_checkpoint(checkpoint_file: Path, state: Dict):
    """Save checkpoint state."""
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_file, 'w') as f:
        json.dump(state, f, indent=2)


def filter_csus_by_cache_availability(
    csus_config: Dict,
    start_date: str,
    end_date: str
) -> Tuple[Dict, List[str]]:
    """
    Filter CSUs to only those with available block caches.

    Args:
        csus_config: Full CSU configuration
        start_date: Start date
        end_date: End date

    Returns:
        Tuple of (filtered_config, skipped_csus)
    """
    filtered = {}
    skipped = []

    for csu_name, csu_config in csus_config.items():
        chain = csu_config.get('chain')
        if not chain:
            skipped.append(f"{csu_name} (no chain specified)")
            continue

        # Apply chain alias if needed (e.g., xdai -> gnosis)
        cache_chain = CHAIN_ALIASES.get(chain, chain)

        # Try to find any cache file for this chain
        cache_dir = Path('data/cache')
        cache_pattern = f'{cache_chain}_blocks_*.json'
        matching_caches = list(cache_dir.glob(cache_pattern))

        if matching_caches:
            # Check if cache covers the requested dates
            # Sort by file size (descending) to prefer larger/fuller caches
            matching_caches.sort(key=lambda p: p.stat().st_size, reverse=True)

            try:
                with open(matching_caches[0]) as f:
                    cache = json.load(f)
                    requested_dates = set(iterate_dates(start_date, end_date))
                    cached_dates = set(cache.keys())

                    if requested_dates.issubset(cached_dates):
                        filtered[csu_name] = csu_config
                    else:
                        missing = requested_dates - cached_dates
                        skipped.append(f"{csu_name} (cache missing {len(missing)} dates)")
            except Exception as e:
                skipped.append(f"{csu_name} (invalid cache: {e})")
        else:
            skipped.append(f"{csu_name} (no cache for {cache_chain})")

    return filtered, skipped


def main():
    parser = argparse.ArgumentParser(description='Collect TVL snapshots in parallel')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--csus', nargs='+', help='Specific CSUs to collect (default: all)')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers (default: 5)')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--checkpoint-file', default='data/.checkpoint_tvl.json', help='Checkpoint file path')

    args = parser.parse_args()

    checkpoint_file = Path(args.checkpoint_file)

    # Load or initialize checkpoint
    if args.resume:
        checkpoint = load_checkpoint(checkpoint_file)
        if not checkpoint.get('start_date') or not checkpoint.get('end_date'):
            print("❌ No checkpoint found or checkpoint missing date range. Please specify --start-date and --end-date")
            return
        start_date = checkpoint['start_date']
        end_date = checkpoint['end_date']
        print(f"📂 Resuming from checkpoint: {len(checkpoint['completed'])} completed, {len(checkpoint['failed'])} failed")
    else:
        if not args.start_date or not args.end_date:
            parser.error("--start-date and --end-date are required (unless using --resume)")
        start_date = args.start_date
        end_date = args.end_date
        checkpoint = {
            'start_date': start_date,
            'end_date': end_date,
            'completed': [],
            'failed': []
        }

    print("="*80)
    print("TVL Parallel Collection")
    print("="*80)
    print(f"Date range: {start_date} → {end_date}")
    print(f"Workers: {args.workers}")
    print("="*80)
    print()

    # Load CSU configuration
    print("Loading CSU configuration...")
    all_csus_config = load_csu_config()

    # Filter by specified CSUs if provided
    if args.csus:
        csus_config = {name: cfg for name, cfg in all_csus_config.items() if name in args.csus}
        if not csus_config:
            print(f"❌ None of the specified CSUs found in config: {args.csus}")
            return
    else:
        csus_config = all_csus_config

    # Filter by cache availability
    print("Checking block cache availability...")
    csus_config, skipped_csus = filter_csus_by_cache_availability(csus_config, start_date, end_date)

    print(f"✅ {len(csus_config)} CSUs with complete block caches")
    if skipped_csus:
        print(f"⚠️  Skipped {len(skipped_csus)} CSUs:")
        for skip_reason in skipped_csus[:10]:  # Show first 10
            print(f"   • {skip_reason}")
        if len(skipped_csus) > 10:
            print(f"   ... and {len(skipped_csus) - 10} more")
    print()

    # Load deployment dates to skip tasks before contracts were deployed
    deployment_dates = load_deployment_dates()
    skipped_by_deployment = 0

    # Build task list
    dates = list(iterate_dates(start_date, end_date))
    tasks = []

    for csu_name, csu_config in csus_config.items():
        chain = csu_config['chain']

        # Load block cache for this chain
        try:
            block_cache = load_block_cache(chain, start_date, end_date)
        except FileNotFoundError as e:
            print(f"⚠️  Skipping {csu_name}: {e}")
            continue

        for date_str in dates:
            task_id = f"{csu_name}:{date_str}"

            # Skip if already completed
            if task_id in checkpoint['completed']:
                continue

            # Skip if contract wasn't deployed yet on this date
            if not should_collect_date(csu_name, date_str, deployment_dates):
                skipped_by_deployment += 1
                continue

            block_info = block_cache.get(date_str)
            if not block_info:
                print(f"⚠️  No block info for {csu_name} on {date_str}")
                continue

            tasks.append((csu_name, csu_config, date_str, block_info))

    total_tasks = len(csus_config) * len(dates)
    remaining_tasks = len(tasks)
    completed_count = len(checkpoint['completed'])

    print(f"📊 Collection Plan:")
    print(f"   Total tasks: {total_tasks} ({len(csus_config)} CSUs × {len(dates)} days)")
    print(f"   Already completed: {completed_count}")
    if skipped_by_deployment > 0:
        print(f"   Skipped (pre-deployment): {skipped_by_deployment}")
    print(f"   Remaining: {remaining_tasks}")
    print(f"   Failed (will retry): {len(checkpoint['failed'])}")
    print()

    if remaining_tasks == 0:
        print("✅ All tasks already completed!")
        return

    # Execute collection in parallel
    print(f"🚀 Starting parallel collection with {args.workers} workers...")
    print()

    w3_cache = {}  # Reuse Web3 instances
    completed = 0
    failed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks (using retry wrapper for automatic 429/connection error handling)
        future_to_task = {
            executor.submit(collect_tvl_snapshot_with_retry, csu_name, csu_config, date_str, block_info, w3_cache):
            (csu_name, date_str)
            for csu_name, csu_config, date_str, block_info in tasks
        }

        # Process results as they complete
        for future in as_completed(future_to_task):
            csu_name, date_str = future_to_task[future]
            task_id = f"{csu_name}:{date_str}"

            try:
                csu_name_result, date_str_result, data, error = future.result()

                if error:
                    print(f"❌ [{completed + failed + 1}/{remaining_tasks}] {csu_name}:{date_str} - {error}")
                    failed += 1
                    checkpoint['failed'].append({'task': task_id, 'error': error})
                else:
                    # Save to bronze
                    save_bronze_data(csu_name, date_str, data)
                    completed += 1
                    checkpoint['completed'].append(task_id)

                    # Progress update every 10 tasks
                    if completed % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        eta = (remaining_tasks - completed - failed) / rate if rate > 0 else 0
                        print(f"✅ [{completed + failed}/{remaining_tasks}] {csu_name}:{date_str} "
                              f"({rate:.1f} tasks/sec, ETA: {eta/60:.1f}m)")

                # Save checkpoint every 50 tasks
                if (completed + failed) % 50 == 0:
                    save_checkpoint(checkpoint_file, checkpoint)

            except Exception as e:
                print(f"❌ [{completed + failed + 1}/{remaining_tasks}] {csu_name}:{date_str} - Exception: {e}")
                failed += 1
                checkpoint['failed'].append({'task': task_id, 'error': str(e)})

    # Final checkpoint save
    save_checkpoint(checkpoint_file, checkpoint)

    # Summary
    elapsed = time.time() - start_time
    print()
    print("="*80)
    print("Collection Complete!")
    print("="*80)
    print(f"✅ Completed: {completed}/{remaining_tasks}")
    print(f"❌ Failed: {failed}/{remaining_tasks}")
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    print(f"📊 Rate: {(completed + failed)/elapsed:.1f} tasks/second")
    print(f"💾 Output: data/bronze/tvl/{{csu}}/{{date}}.json")

    if failed > 0:
        print(f"\n⚠️  {failed} tasks failed. Run with --resume to retry.")
        print(f"   Failed tasks saved in: {checkpoint_file}")

    print("="*80)


if __name__ == '__main__':
    main()
