#!/usr/bin/env python3
"""
Block Cache Builder

Pre-computes date→block mappings for a date range.
Saves to JSON for fast lookups during collection.

Usage:
    python scripts/build_block_cache.py --start-date 2024-12-01 --end-date 2024-12-31
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
import json
from datetime import date, timedelta
import argparse
from config.rpc_pool import get_web3
from datetime import datetime, timedelta, timezone
import pytz

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

NY_TZ = pytz.timezone("America/New_York")


def to_dt(ts: int) -> datetime:
    """
    Convert a unix timestamp to an aware UTC datetime.
    Behavior mirrors liquidation utilities.
    """
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)

def block_for_ts(w3, ts):
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


def to_date_ny(ts: int) -> str:
    """
    Convert a unix timestamp to a NY-calendar date (YYYY-MM-DD).
    This is exactly the day-bucketing definition used in liquidations.
    """
    return to_dt(ts).astimezone(NY_TZ).date().isoformat()


def ny_date_to_utc_window(date_str: str) -> tuple[int, int]:
    """
    Given a NY date string 'YYYY-MM-DD', return a pair of UTC timestamps:

        (ts_start_utc, ts_end_utc)

    where:
      ts_start_utc = NY midnight at start of that date
      ts_end_utc   = NY midnight at start of next date

    This will be used to anchor daily TVL sampling blocks:
    - daily snapshot target will be near ts_end_utc
    - block_for_ts(ts_end_utc) will produce a block whose timestamp >= ts_end_utc
    """
    d = datetime.fromisoformat(date_str).date()

    # NY midnight start of day
    start_ny = NY_TZ.localize(datetime(d.year, d.month, d.day, 0, 0, 0))
    end_ny = start_ny + timedelta(days=1)

    ts_start_utc = int(start_ny.astimezone(timezone.utc).timestamp())
    ts_end_utc = int(end_ny.astimezone(timezone.utc).timestamp())
    return ts_start_utc, ts_end_utc


def iterate_dates(start_str: str, end_str: str):
    """Yield YYYY-MM-DD strings from start to end (inclusive)"""
    d0 = date.fromisoformat(start_str)
    d1 = date.fromisoformat(end_str)
    d = d0
    while d <= d1:
        yield d.isoformat()
        d += timedelta(days=1)


def build_cache_for_chain(chain: str, dates: list, output_file: Path):
    """
    Build date→block cache for a specific chain.
    
    Args:
        chain: Chain name (e.g., 'ethereum')
        dates: List of date strings (YYYY-MM-DD)
        output_file: Path to save cache JSON
    """
    print(f"\n{'='*60}")
    print(f"Building block cache for {chain}")
    print(f"{'='*60}\n")
    
    w3 = get_web3(chain)
    
    # Test connection
    try:
        latest = w3.eth.block_number
        print(f"Connected to {chain}: latest block = {latest}\n")
    except Exception as e:
        print(f"❌ Failed to connect to {chain}: {e}")
        return
    
    cache = {}
    
    for i, date_str in enumerate(dates, 1):
        try:
            # Get UTC window for this NY date
            ts_start_utc, ts_end_utc = ny_date_to_utc_window(date_str)
            
            # Find block at end of day (snapshot time)
            block_num = block_for_ts(w3, ts_end_utc)
            
            # Safety: subtract 1 to ensure block is from target day
            block_num = max(1, block_num - 1)
            
            # Get block timestamp for verification
            block = w3.eth.get_block(block_num)
            block_ts = block['timestamp']
            
            cache[date_str] = {
                'block': block_num,
                'timestamp': block_ts,
                'ts_start_utc': ts_start_utc,
                'ts_end_utc': ts_end_utc,
            }
            
            print(f"[{i}/{len(dates)}] {date_str} → block {block_num} (ts={block_ts})")
            
        except Exception as e:
            print(f"❌ Failed to get block for {date_str}: {e}")
            continue
    
    # Save to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f"\n✅ Saved cache to {output_file}")
    print(f"   Cached {len(cache)}/{len(dates)} dates\n")


def main():
    parser = argparse.ArgumentParser(description='Build date→block cache')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--chains', nargs='+', 
                       default=['ethereum', 'arbitrum', 'base', 'optimism'],
                       help='Chains to build cache for')
    parser.add_argument('--output-dir', default='data/cache',
                       help='Output directory for cache files')
    
    args = parser.parse_args()
    
    # Generate date list
    dates = list(iterate_dates(args.start_date, args.end_date))
    
    print(f"\n{'='*60}")
    print(f"Block Cache Builder")
    print(f"{'='*60}")
    print(f"Date range: {args.start_date} → {args.end_date}")
    print(f"Total dates: {len(dates)}")
    print(f"Chains: {', '.join(args.chains)}")
    print(f"{'='*60}\n")
    
    output_dir = Path(args.output_dir)
    
    # Build cache for each chain
    for chain in args.chains:
        output_file = output_dir / f"{chain}_blocks_{args.start_date}_{args.end_date}.json"
        build_cache_for_chain(chain, dates, output_file)
    
    print(f"\n{'='*60}")
    print("✅ Block cache building complete!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
