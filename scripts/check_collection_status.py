#!/usr/bin/env python3
"""
Collection Status Checker

Validates TVL collection results:
- Counts total snapshots collected
- Shows progress vs target (30 CSUs × 366 days = 10,980)
- Lists CSU coverage with date ranges
- Validates no empty files (checks size > 0 and valid JSON)
- Shows checkpoint summary
- Displays cache availability

Run multiple times to track progress.

Usage:
    python3 scripts/check_collection_status.py
    python3 scripts/check_collection_status.py --target-year 2024
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# Expected working chains (excluding Polygon, Plasma, Sonic, Binance)
WORKING_CHAINS = {'ethereum', 'arbitrum', 'base', 'optimism', 'avalanche', 'linea', 'gnosis', 'scroll'}

# Target CSUs (based on configuration)
TARGET_CSU_COUNT = 30  # Realistic target (exclude problematic chains)
DAYS_PER_YEAR = 366  # 2024 is a leap year
TARGET_SNAPSHOTS = TARGET_CSU_COUNT * DAYS_PER_YEAR


def load_checkpoint(checkpoint_file: Path) -> Dict:
    """Load checkpoint if exists."""
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            return json.load(f)
    return {'completed': [], 'failed': []}


def validate_json_file(file_path: Path) -> Tuple[bool, str]:
    """
    Validate JSON file is not empty and contains valid data.

    Returns:
        (is_valid, error_message)
    """
    # Check file size
    if file_path.stat().st_size == 0:
        return False, "Empty file (0 bytes)"

    # Check valid JSON
    try:
        with open(file_path) as f:
            data = json.load(f)

        # Check has expected structure (at minimum should be a dict)
        if not isinstance(data, dict):
            return False, "Invalid structure (not a dict)"

        # Check has some data
        if len(data) == 0:
            return False, "Empty data (no fields)"

        return True, ""

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Error reading: {str(e)}"


def scan_data_directory(data_dir: Path) -> Dict:
    """
    Scan data/bronze/tvl directory for collected snapshots.

    Returns:
        {
            'total_files': int,
            'valid_files': int,
            'invalid_files': [(file_path, error_msg), ...],
            'csu_coverage': {
                'csu_name': {
                    'count': int,
                    'dates': [date_str, ...],
                    'chains': set,
                }
            }
        }
    """
    tvl_dir = data_dir / 'bronze' / 'tvl'

    if not tvl_dir.exists():
        return {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': [],
            'csu_coverage': {}
        }

    total_files = 0
    valid_files = 0
    invalid_files = []
    csu_coverage = defaultdict(lambda: {'count': 0, 'dates': [], 'chains': set()})

    # Scan each CSU directory
    for csu_dir in sorted(tvl_dir.iterdir()):
        if not csu_dir.is_dir():
            continue

        csu_name = csu_dir.name

        # Scan JSON files in this CSU
        for json_file in csu_dir.glob('*.json'):
            total_files += 1

            # Validate file
            is_valid, error_msg = validate_json_file(json_file)

            if is_valid:
                valid_files += 1

                # Extract date from filename (format: YYYY-MM-DD.json)
                date_str = json_file.stem
                csu_coverage[csu_name]['dates'].append(date_str)
                csu_coverage[csu_name]['count'] += 1
            else:
                invalid_files.append((str(json_file), error_msg))

    # Load config to get chain info
    try:
        import yaml
        config_file = Path('code/config/csu_config.yaml')
        with open(config_file) as f:
            config = yaml.safe_load(f)

        csus = config.get('csus', config)

        # Add chain info to coverage
        for csu_name in csu_coverage:
            if csu_name in csus:
                chain = csus[csu_name].get('chain', 'unknown')
                csu_coverage[csu_name]['chains'].add(chain)
    except Exception as e:
        print(f"Warning: Could not load config for chain info: {e}")

    return {
        'total_files': total_files,
        'valid_files': valid_files,
        'invalid_files': invalid_files,
        'csu_coverage': dict(csu_coverage)
    }


def check_block_caches(cache_dir: Path, year: int = 2024) -> Dict:
    """
    Check availability of block caches for target year.

    Returns:
        {
            'chain_name': {
                'exists': bool,
                'date_count': int,
                'date_range': (start, end)
            }
        }
    """
    caches = {}

    for chain in WORKING_CHAINS:
        # Look for cache file matching pattern
        cache_pattern = f"{chain}_blocks_{year}-01-01_{year}-12-31.json"
        cache_file = cache_dir / cache_pattern

        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    cache_data = json.load(f)

                dates = sorted(cache_data.keys())
                caches[chain] = {
                    'exists': True,
                    'date_count': len(dates),
                    'date_range': (dates[0], dates[-1]) if dates else (None, None)
                }
            except Exception as e:
                caches[chain] = {
                    'exists': True,
                    'date_count': 0,
                    'date_range': (None, None),
                    'error': str(e)
                }
        else:
            caches[chain] = {
                'exists': False,
                'date_count': 0,
                'date_range': (None, None)
            }

    return caches


def print_summary(scan_results: Dict, checkpoint_data: Dict, cache_info: Dict, target_year: int):
    """Print comprehensive status summary."""

    print("\n" + "=" * 80)
    print(f"TVL Collection Status - {target_year}")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Overall Progress
    print("=" * 80)
    print("OVERALL PROGRESS")
    print("=" * 80)

    valid_files = scan_results['valid_files']
    total_files = scan_results['total_files']
    progress_pct = (valid_files / TARGET_SNAPSHOTS * 100) if TARGET_SNAPSHOTS > 0 else 0

    print(f"Valid snapshots:  {valid_files:,} / {TARGET_SNAPSHOTS:,} ({progress_pct:.1f}%)")
    print(f"Total files:      {total_files:,}")
    print(f"Invalid files:    {len(scan_results['invalid_files'])}")
    print()

    # Checkpoint Summary
    completed_tasks = len(checkpoint_data.get('completed', []))
    failed_tasks = len(checkpoint_data.get('failed', []))
    total_tasks = completed_tasks + failed_tasks

    if total_tasks > 0:
        print("Checkpoint Status:")
        print(f"  Completed: {completed_tasks:,}")
        print(f"  Failed:    {failed_tasks:,}")
        print(f"  Total:     {total_tasks:,}")
        print()

    # CSU Coverage
    print("=" * 80)
    print("CSU COVERAGE")
    print("=" * 80)

    csu_coverage = scan_results['csu_coverage']

    if len(csu_coverage) == 0:
        print("No data collected yet")
    else:
        # Sort by count descending
        sorted_csus = sorted(csu_coverage.items(), key=lambda x: x[1]['count'], reverse=True)

        print(f"{'CSU':<40} {'Days':<8} {'Chain':<15} {'Date Range'}")
        print("-" * 80)

        for csu_name, info in sorted_csus:
            count = info['count']
            dates = sorted(info['dates'])
            chains = ', '.join(info['chains']) if info['chains'] else 'unknown'

            if dates:
                date_range = f"{dates[0]} → {dates[-1]}"
            else:
                date_range = "N/A"

            print(f"{csu_name:<40} {count:<8} {chains:<15} {date_range}")

        print()
        print(f"Total CSUs with data: {len(csu_coverage)}")
        print()

    # Invalid Files
    if len(scan_results['invalid_files']) > 0:
        print("=" * 80)
        print("INVALID FILES")
        print("=" * 80)

        for file_path, error_msg in scan_results['invalid_files']:
            print(f"❌ {file_path}")
            print(f"   Error: {error_msg}")
        print()

    # Block Cache Status
    print("=" * 80)
    print("BLOCK CACHE STATUS")
    print("=" * 80)

    cache_ok_count = sum(1 for info in cache_info.values() if info['exists'] and info['date_count'] == DAYS_PER_YEAR)

    print(f"{'Chain':<15} {'Status':<10} {'Days':<8} {'Date Range'}")
    print("-" * 80)

    for chain in sorted(WORKING_CHAINS):
        info = cache_info.get(chain, {'exists': False})

        if info['exists']:
            if info['date_count'] == DAYS_PER_YEAR:
                status = "✅ OK"
            elif info['date_count'] > 0:
                status = "⚠️  Partial"
            else:
                status = "❌ Invalid"

            date_range = f"{info['date_range'][0]} → {info['date_range'][1]}" if info['date_range'][0] else "N/A"
            print(f"{chain:<15} {status:<10} {info['date_count']:<8} {date_range}")
        else:
            print(f"{chain:<15} {'❌ Missing':<10} {0:<8} {'N/A'}")

    print()
    print(f"Complete caches: {cache_ok_count}/{len(WORKING_CHAINS)} chains")
    print()

    # Failed Tasks Summary (from checkpoint)
    failed = checkpoint_data.get('failed', [])
    if len(failed) > 0:
        print("=" * 80)
        print("FAILURE BREAKDOWN")
        print("=" * 80)

        # Categorize failures
        rate_limit_failures = []
        archive_failures = []
        connection_failures = []
        decode_failures = []
        execution_reverted = []
        other_failures = []

        for task in failed:
            error = task.get('error', '')

            if '429' in error or 'Too Many Requests' in error:
                rate_limit_failures.append(task)
            elif 'state' in error.lower() and 'not available' in error.lower():
                archive_failures.append(task)
            elif 'Could not transact' in error or 'Could not call' in error:
                archive_failures.append(task)
            elif 'Could not decode contract function call' in error:
                decode_failures.append(task)
            elif 'execution reverted' in error.lower():
                execution_reverted.append(task)
            elif 'Connection aborted' in error or 'Remote end closed' in error or 'RemoteDisconnected' in error:
                connection_failures.append(task)
            else:
                other_failures.append(task)

        print(f"Rate Limiting (429):        {len(rate_limit_failures)} (retry-able)")
        print(f"Archive State Unavailable:  {len(archive_failures)} (permanent)")
        print(f"Decode Errors:              {len(decode_failures)} (config/contract issue)")
        print(f"Execution Reverted:         {len(execution_reverted)} (contract error)")
        print(f"Connection Failures:        {len(connection_failures)} (retry-able)")
        print(f"Other Errors:               {len(other_failures)}")
        print()

        if len(rate_limit_failures) > 0:
            print("⏱️  Rate limit errors can be retried with:")
            print("   python3 scripts/collect_tvl_parallel.py --resume --workers 2")
            print()

        if len(connection_failures) > 0:
            print("🔌 Connection failures are retry-able (RPC timeouts/disconnects)")
            print()

        if len(decode_failures) > 0:
            print("⚠️  Decode errors indicate contract/config issues:")
            print(f"   {len(decode_failures)} tasks failed to decode contract responses")
            print("   This may indicate wrong contract addresses or incompatible ABIs")
            print()

    # Recommendations
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)

    if valid_files == 0:
        print("📋 No data collected yet. Start collection with:")
        print("   python3 scripts/collect_tvl_parallel.py --start-date 2024-01-01 --end-date 2024-12-31 --workers 2")
    elif progress_pct < 50:
        print("🚀 Collection in progress. Current coverage is low.")
        if failed_tasks > 0:
            print("   Resume collection with:")
            print("   python3 scripts/collect_tvl_parallel.py --resume --workers 2")
    elif progress_pct < 80:
        print("📈 Good progress! You're over halfway there.")
        if len(rate_limit_failures) > 0:
            print("   Wait 1 hour for rate limits to reset, then:")
            print("   python3 scripts/collect_tvl_parallel.py --resume --workers 2")
    else:
        print("✅ Excellent coverage! You're almost done.")
        if failed_tasks > 0:
            print("   Clean up remaining tasks with:")
            print("   python3 scripts/collect_tvl_parallel.py --resume --workers 2")

    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Check TVL collection status')
    parser.add_argument('--target-year', type=int, default=2024, help='Target year for analysis')
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    cache_dir = data_dir / 'cache'
    checkpoint_file = data_dir / '.checkpoint_tvl.json'

    # Scan data directory
    print("Scanning data directory...")
    scan_results = scan_data_directory(data_dir)

    # Load checkpoint
    print("Loading checkpoint...")
    checkpoint_data = load_checkpoint(checkpoint_file)

    # Check block caches
    print("Checking block caches...")
    cache_info = check_block_caches(cache_dir, args.target_year)

    # Print summary
    print_summary(scan_results, checkpoint_data, cache_info, args.target_year)


if __name__ == '__main__':
    main()
