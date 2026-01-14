#!/usr/bin/env python3
"""
Parallel TVL Collector

Collects TVL snapshots for all CSUs across a date range using cached blocks.
Uses ThreadPoolExecutor for parallel collection with rate limiting.

Features:
- Puzzle-piece collection: Run any date range, fills in missing pieces
- Global completion tracking: Scans data/bronze/tvl/ for existing data
- Automatic key blacklisting: 401 errors permanently remove keys from rotation

Usage:
    python scripts/collect_tvl_parallel.py --start-date 2024-01-01 --end-date 2024-12-31
    python scripts/collect_tvl_parallel.py --start-date 2024-06-01 --end-date 2024-06-30 --csus aave_v3_ethereum
    python scripts/collect_tvl_parallel.py --start-date 2024-01-01 --end-date 2024-12-31 --workers 3
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
from typing import Dict, List, Tuple, Optional, Set
import yaml
from config.rpc_pool import get_web3_with_key_info, blacklist_key, report_rpc_error, is_chain_backing_off

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

# Bronze data directory
BRONZE_DIR = Path('data/bronze/tvl')


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


def scan_existing_data() -> Set[str]:
    """
    Scan bronze data directory to find all completed tasks.

    Returns:
        Set of task IDs like "aave_v3_ethereum:2024-01-15"
    """
    completed = set()

    if not BRONZE_DIR.exists():
        return completed

    # Scan all CSU directories
    for csu_dir in BRONZE_DIR.iterdir():
        if not csu_dir.is_dir():
            continue

        csu_name = csu_dir.name

        # Scan all date files
        for json_file in csu_dir.glob('*.json'):
            # Extract date from filename (e.g., "2024-01-15.json" -> "2024-01-15")
            date_str = json_file.stem

            # Validate it looks like a date
            if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                task_id = f"{csu_name}:{date_str}"
                completed.add(task_id)

    return completed


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


def setup_web3_for_chain(chain: str) -> Tuple:
    """
    Setup Web3 instance for a chain with appropriate middleware.

    Args:
        chain: Chain name

    Returns:
        Tuple of (Web3 instance, key_name or None for public RPC)
    """
    # Resolve chain alias
    rpc_chain = CHAIN_ALIASES.get(chain, chain)

    # Get web3 instance with key info (returns w3, key_name, rate_limiter)
    w3, key_name, _ = get_web3_with_key_info(rpc_chain)

    # Inject POA middleware if needed
    if chain in POA_CHAINS and geth_poa_middleware:
        try:
            if hasattr(w3, 'middleware_onion'):
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except Exception as e:
            pass  # May already be injected

    return w3, key_name


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


def is_auth_error(error_str: str) -> bool:
    """Check if error is an authentication/authorization error (401)."""
    return '401' in error_str or 'Unauthorized' in error_str


def collect_tvl_snapshot_with_retry(
    csu_name: str,
    csu_config: Dict,
    date_str: str,
    block_info: Dict,
    max_retries: int = 5,
    max_backoff: float = 10.0
) -> Tuple[str, str, Optional[Dict], Optional[str]]:
    """
    Collect TVL snapshot with automatic retry for rate limits and connection errors.

    Uses exponential backoff: 1s, 2s, 4s... capped at max_backoff.
    Automatically blacklists keys that return 401 Unauthorized.
    Skips chains that are currently in backoff mode (returns special error).

    Args:
        csu_name: CSU identifier
        csu_config: CSU configuration
        date_str: Date string (YYYY-MM-DD)
        block_info: Block information for the date
        max_retries: Maximum number of retry attempts
        max_backoff: Maximum backoff time in seconds (default 5s)

    Returns:
        Tuple of (csu_name, date_str, data_dict, error_message)
    """
    last_error = None
    chain = csu_config['chain']

    # Check if chain is in backoff mode - skip immediately to let other chains proceed
    is_backing_off, remaining = is_chain_backing_off(chain)
    if is_backing_off:
        return (csu_name, date_str, None, f"DEFERRED:chain_backoff:{remaining:.0f}s")

    for attempt in range(max_retries + 1):
        result = collect_tvl_snapshot(csu_name, csu_config, date_str, block_info)
        _csu, _date, data, error = result

        # Success
        if data is not None:
            return result

        # Check for 401 Unauthorized - blacklist the key
        if error and is_auth_error(error):
            # We need to figure out which key was used
            # The error message from requests often contains the URL
            # For now, just log and don't retry 401s
            print(f"  ⚠️  Auth error detected for {chain}. Check your API keys.")
            return result

        # Check if error is retryable
        if error and is_retryable_error(error):
            last_error = error
            # Report rate limit errors to trigger RPC pool backoff
            if '429' in error or '503' in error or 'too many' in error.lower():
                report_rpc_error(chain, error)
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
    block_info: Dict
) -> Tuple[str, str, Optional[Dict], Optional[str]]:
    """
    Collect TVL snapshot for a single CSU on a specific date.

    Args:
        csu_name: CSU identifier
        csu_config: CSU configuration
        date_str: Date string (YYYY-MM-DD)
        block_info: Block information for the date

    Returns:
        Tuple of (csu_name, date_str, data_dict, error_message)
    """
    try:
        chain = csu_config['chain']
        registry = csu_config['registry']
        block_number = block_info['block']
        protocol = csu_config.get('protocol', '')

        # Get a fresh Web3 instance with key info
        w3, key_name = setup_web3_for_chain(chain)

        # Get appropriate adapter
        adapter = get_adapter_for_csu(csu_config)
        if not adapter:
            return (csu_name, date_str, None, f"No adapter found for protocol: {protocol}")

        # Call adapter to get TVL data
        try:
            tvl_data = adapter(w3, registry, block_number)
        except Exception as e:
            error_str = str(e)

            # Check for 401 - blacklist the key
            if is_auth_error(error_str) and key_name:
                blacklist_key(chain, key_name, error_str[:100])

            raise

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
    output_dir = BRONZE_DIR / csu_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f'{date_str}.json'

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)


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
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--csus', nargs='+', help='Specific CSUs to collect (default: all)')
    parser.add_argument('--chains', nargs='+', help='Only collect CSUs on these chains (e.g., --chains ethereum base)')
    parser.add_argument('--exclude-chains', nargs='+', help='Exclude CSUs on these chains')
    parser.add_argument('--workers', type=int, default=2, help='Number of parallel workers (default: 2)')

    args = parser.parse_args()

    start_date = args.start_date
    end_date = args.end_date

    print("="*80)
    print("TVL Parallel Collection")
    print("="*80)
    print(f"Date range: {start_date} → {end_date}")
    print(f"Workers: {args.workers}")
    print("="*80)
    print()

    # Step 1: Scan existing data to find completed tasks
    print("Scanning existing data...")
    completed_tasks = scan_existing_data()
    print(f"Found {len(completed_tasks)} existing data files")
    print()

    # Step 2: Load CSU configuration
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

    # Filter by chain if specified
    if args.chains:
        chains_set = set(args.chains)
        csus_config = {name: cfg for name, cfg in csus_config.items()
                       if cfg.get('chain') in chains_set}
        print(f"Filtering to chains: {', '.join(args.chains)}")

    # Exclude chains if specified
    if args.exclude_chains:
        exclude_set = set(args.exclude_chains)
        csus_config = {name: cfg for name, cfg in csus_config.items()
                       if cfg.get('chain') not in exclude_set}
        print(f"Excluding chains: {', '.join(args.exclude_chains)}")

    # Step 3: Filter by cache availability
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

    # Step 4: Load deployment dates to skip tasks before contracts were deployed
    deployment_dates = load_deployment_dates()
    skipped_by_deployment = 0

    # Step 5: Build task list (only tasks not already completed)
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

            # Skip if already completed (found in existing data)
            if task_id in completed_tasks:
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

    # Calculate stats
    total_possible = len(csus_config) * len(dates)
    already_completed = sum(1 for csu in csus_config for d in dates
                            if f"{csu}:{d}" in completed_tasks)
    remaining_tasks = len(tasks)

    print(f"📊 Collection Plan:")
    print(f"   Total possible: {total_possible} ({len(csus_config)} CSUs × {len(dates)} days)")
    print(f"   Already completed: {already_completed}")
    if skipped_by_deployment > 0:
        print(f"   Skipped (pre-deployment): {skipped_by_deployment}")
    print(f"   Remaining to collect: {remaining_tasks}")
    print()

    if remaining_tasks == 0:
        print("✅ All tasks already completed!")
        return

    # Step 6: Execute collection in parallel
    print(f"🚀 Starting parallel collection with {args.workers} workers...")
    print()

    completed = 0
    failed = 0
    deferred = 0
    failed_tasks = []
    deferred_tasks = []  # Tasks to retry after backoff clears
    start_time = time.time()

    # Build a lookup for task data
    task_data = {f"{t[0]}:{t[2]}": t for t in tasks}  # key: "csu:date", value: (csu, config, date, block)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks (using retry wrapper for automatic 429/connection error handling)
        future_to_task = {
            executor.submit(collect_tvl_snapshot_with_retry, csu_name, csu_config, date_str, block_info):
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
                    # Check if this was deferred due to backoff
                    if error.startswith("DEFERRED:"):
                        deferred += 1
                        deferred_tasks.append(task_id)
                        # Don't print every deferred task - too noisy
                        if deferred <= 3:
                            print(f"⏸️  [{completed + failed + deferred}/{remaining_tasks}] {csu_name}:{date_str} - {error}")
                        elif deferred == 4:
                            print(f"⏸️  ... more tasks deferred (chain in backoff)")
                    else:
                        print(f"❌ [{completed + failed + deferred}/{remaining_tasks}] {csu_name}:{date_str} - {error[:80]}")
                        failed += 1
                        failed_tasks.append({'task': task_id, 'error': error})
                else:
                    # Save to bronze
                    save_bronze_data(csu_name, date_str, data)
                    completed += 1

                    # Progress update every 10 tasks
                    if completed % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        remaining = remaining_tasks - completed - failed - deferred
                        eta = remaining / rate if rate > 0 else 0
                        print(f"✅ [{completed + failed + deferred}/{remaining_tasks}] {csu_name}:{date_str} "
                              f"({rate:.1f} tasks/sec, ETA: {eta/60:.1f}m)")

            except Exception as e:
                print(f"❌ [{completed + failed + deferred}/{remaining_tasks}] {csu_name}:{date_str} - Exception: {e}")
                failed += 1
                failed_tasks.append({'task': task_id, 'error': str(e)})

    # Retry deferred tasks if any (backoff should have cleared by now)
    if deferred_tasks:
        print(f"\n🔄 Retrying {len(deferred_tasks)} deferred tasks...")
        retry_completed = 0
        retry_failed = 0

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            retry_futures = {}
            for task_id in deferred_tasks:
                if task_id in task_data:
                    csu_name, csu_config, date_str, block_info = task_data[task_id]
                    future = executor.submit(collect_tvl_snapshot_with_retry, csu_name, csu_config, date_str, block_info)
                    retry_futures[future] = (csu_name, date_str)

            for future in as_completed(retry_futures):
                csu_name, date_str = retry_futures[future]
                try:
                    _, _, data, error = future.result()
                    if data:
                        save_bronze_data(csu_name, date_str, data)
                        retry_completed += 1
                    else:
                        retry_failed += 1
                        if error and not error.startswith("DEFERRED:"):
                            failed_tasks.append({'task': f"{csu_name}:{date_str}", 'error': error})
                except Exception as e:
                    retry_failed += 1

        completed += retry_completed
        failed += retry_failed
        deferred = deferred - retry_completed - retry_failed
        print(f"   Retry results: {retry_completed} completed, {retry_failed} failed")

    # Summary
    elapsed = time.time() - start_time
    print()
    print("="*80)
    print("Collection Complete!")
    print("="*80)
    print(f"✅ Completed: {completed}/{remaining_tasks}")
    print(f"❌ Failed: {failed}/{remaining_tasks}")
    if deferred > 0:
        print(f"⏸️  Still deferred: {deferred}/{remaining_tasks}")
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    if elapsed > 0:
        print(f"📊 Rate: {(completed + failed)/elapsed:.1f} tasks/second")
    print(f"💾 Output: data/bronze/tvl/{{csu}}/{{date}}.json")

    if failed > 0 or deferred > 0:
        print(f"\n⚠️  {failed + deferred} tasks need retry. Re-run to retry.")

        # Categorize failures
        auth_errors = [t for t in failed_tasks if is_auth_error(t['error'])]
        if auth_errors:
            print(f"\n🔐 {len(auth_errors)} authentication errors (401):")
            print("   Check your API keys in .env")

    print("="*80)


if __name__ == '__main__':
    main()
