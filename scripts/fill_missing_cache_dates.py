#!/usr/bin/env python3
"""
Fill Missing Block Cache Dates

Identifies missing dates in existing block caches and fills them in.
Uses retry logic to handle transient RPC failures.

Usage:
    python3 scripts/fill_missing_cache_dates.py
    python3 scripts/fill_missing_cache_dates.py --chains gnosis scroll
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import time
from datetime import datetime, timedelta, timezone
import pytz
from config.rpc_pool import get_web3

# Import POA middleware
try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        from web3.middleware import geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None

NY_TZ = pytz.timezone("America/New_York")
POA_CHAINS = ['binance', 'polygon', 'gnosis', 'avalanche', 'optimism', 'linea', 'scroll', 'xdai', 'cronos', 'meter', 'flare', 'sonic']

CHAIN_ALIASES = {
    'xdai': 'gnosis',
}


def to_dt(ts: int) -> datetime:
    """Convert unix timestamp to aware UTC datetime."""
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


def block_for_ts(w3, ts):
    """Binary search to find block at or after given timestamp."""
    lo, hi = 1, w3.eth.block_number
    ans = hi
    while lo <= hi:
        mid = (lo + hi) // 2
        t = w3.eth.get_block(mid)["timestamp"]
        if t >= ts:
            ans = mid
            hi = mid - 1
        else:
            lo = mid + 1
    return ans


def ny_date_to_utc_window(date_str: str):
    """Convert NY date to UTC timestamp window."""
    d = datetime.fromisoformat(date_str).date()
    start_ny = NY_TZ.localize(datetime(d.year, d.month, d.day, 0, 0, 0))
    end_ny = start_ny + timedelta(days=1)
    ts_start_utc = int(start_ny.astimezone(timezone.utc).timestamp())
    ts_end_utc = int(end_ny.astimezone(timezone.utc).timestamp())
    return ts_start_utc, ts_end_utc


def find_missing_dates(cache_file: Path, target_year: int = 2024):
    """
    Find missing dates in a block cache.

    Returns:
        (missing_dates, total_expected)
    """
    if not cache_file.exists():
        return [], 0

    with open(cache_file) as f:
        cache = json.load(f)

    # Generate all dates for target year
    start = datetime(target_year, 1, 1)
    days = 366 if target_year == 2024 else 365  # 2024 is leap year
    all_dates = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]

    # Find missing
    missing = [d for d in all_dates if d not in cache]

    return missing, len(all_dates)


def fill_missing_date(w3, chain: str, date_str: str, max_retries: int = 3):
    """
    Fill in a single missing date with retry logic.

    Returns:
        (success, cache_entry_or_error)
    """
    for attempt in range(max_retries):
        try:
            # Get UTC window for this NY date
            ts_start_utc, ts_end_utc = ny_date_to_utc_window(date_str)

            # Find block at end of day
            block_num = block_for_ts(w3, ts_end_utc)

            # Safety: subtract 1 to ensure block is from target day
            block_num = max(1, block_num - 1)

            # Get block timestamp for verification
            block = w3.eth.get_block(block_num)
            block_ts = block['timestamp']

            cache_entry = {
                'block': block_num,
                'timestamp': block_ts,
                'ts_start_utc': ts_start_utc,
                'ts_end_utc': ts_end_utc,
            }

            return True, cache_entry

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                print(f"   ⚠️  Attempt {attempt + 1} failed: {e}")
                print(f"   Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                return False, str(e)

    return False, "Max retries exceeded"


def fill_cache_for_chain(chain: str, cache_file: Path, target_year: int = 2024):
    """
    Fill missing dates in a chain's block cache.
    """
    print(f"\n{'='*70}")
    print(f"Filling Missing Dates: {chain}")
    print(f"{'='*70}")

    # Find missing dates
    missing_dates, total_expected = find_missing_dates(cache_file, target_year)

    if len(missing_dates) == 0:
        print(f"✅ Cache complete: {total_expected}/{total_expected} dates")
        return

    print(f"Missing dates: {len(missing_dates)}/{total_expected}")
    print(f"Dates to fill: {missing_dates}")
    print()

    # Load existing cache
    with open(cache_file) as f:
        cache = json.load(f)

    # Setup Web3
    rpc_chain = CHAIN_ALIASES.get(chain, chain)
    w3 = get_web3(rpc_chain)

    # Inject POA middleware if needed
    if chain in POA_CHAINS and geth_poa_middleware:
        try:
            if hasattr(w3, 'middleware_onion'):
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            print(f"[POA] Injected POA middleware")
        except Exception as e:
            print(f"[POA] Warning: {e}")

    # Test connection
    try:
        latest = w3.eth.block_number
        print(f"Connected to {chain}: block {latest}\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # Fill each missing date
    filled_count = 0
    failed_dates = []

    for i, date_str in enumerate(missing_dates, 1):
        print(f"[{i}/{len(missing_dates)}] Filling {date_str}...", end=' ')

        success, result = fill_missing_date(w3, chain, date_str)

        if success:
            cache[date_str] = result
            filled_count += 1
            print(f"✅ block {result['block']}")
        else:
            failed_dates.append((date_str, result))
            print(f"❌ {result}")

    # Save updated cache
    if filled_count > 0:
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
        print(f"\n✅ Saved {filled_count} new dates to cache")

    # Summary
    print(f"\n{'='*70}")
    print(f"Summary for {chain}")
    print(f"{'='*70}")
    print(f"Total dates:    {total_expected}")
    print(f"Previously had: {total_expected - len(missing_dates)}")
    print(f"Filled:         {filled_count}")
    print(f"Still missing:  {len(failed_dates)}")

    if failed_dates:
        print(f"\nFailed dates:")
        for date_str, error in failed_dates:
            print(f"  {date_str}: {error}")


def main():
    parser = argparse.ArgumentParser(description='Fill missing block cache dates')
    parser.add_argument('--chains', nargs='+',
                       default=['gnosis', 'scroll'],
                       help='Chains to check and fill')
    parser.add_argument('--target-year', type=int, default=2024,
                       help='Target year')
    parser.add_argument('--cache-dir', default='data/cache',
                       help='Cache directory')

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"Fill Missing Block Cache Dates")
    print(f"{'='*70}")
    print(f"Target year: {args.target_year}")
    print(f"Chains: {', '.join(args.chains)}")
    print(f"{'='*70}")

    cache_dir = Path(args.cache_dir)

    for chain in args.chains:
        cache_file = cache_dir / f"{chain}_blocks_{args.target_year}-01-01_{args.target_year}-12-31.json"

        if not cache_file.exists():
            print(f"\n⚠️  {chain}: Cache file not found at {cache_file}")
            continue

        fill_cache_for_chain(chain, cache_file, args.target_year)

    print(f"\n{'='*70}")
    print("✅ Done!")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
