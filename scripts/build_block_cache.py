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
from pathlib import Path

# Add parent to path BEFORE importing project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
from datetime import date, datetime, timedelta, timezone
import argparse
import pytz
from config.rpc_pool import get_web3, get_web3_with_key_info

# Import POA middleware (path changed in web3.py v6+)
try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        from web3.middleware import geth_poa_middleware
    except ImportError:
        # Fallback for very old versions
        geth_poa_middleware = None

NY_TZ = pytz.timezone("America/New_York")

# Chains that use POA (Proof of Authority) or have non-standard extraData
POA_CHAINS = ['binance', 'polygon', 'gnosis', 'avalanche', 'optimism', 'linea', 'scroll', 'xdai', 'cronos', 'meter', 'flare', 'sonic']

# Chain name aliases (config name -> RPC pool name)
CHAIN_ALIASES = {
    'xdai': 'gnosis',  # xdai in config, but gnosis in RPC pool
}

# Track which Web3 instances have POA middleware injected
_poa_injected = set()


def get_web3_with_poa(chain: str, rpc_chain: str = None):
    """
    Get a Web3 connection with POA middleware injected if needed.

    This ensures every connection returned has proper middleware for POA chains.
    """
    if rpc_chain is None:
        rpc_chain = CHAIN_ALIASES.get(chain, chain)

    w3 = get_web3(rpc_chain)

    # Inject POA middleware if this chain needs it and this instance hasn't been configured
    if chain in POA_CHAINS and geth_poa_middleware:
        # Use id() to track which Web3 instances have been configured
        w3_id = id(w3)
        if w3_id not in _poa_injected:
            try:
                if hasattr(w3, 'middleware_onion'):
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    _poa_injected.add(w3_id)
            except Exception:
                pass  # May already be injected or not supported

    return w3


def to_dt(ts: int) -> datetime:
    """
    Convert a unix timestamp to an aware UTC datetime.
    Behavior mirrors liquidation utilities.
    """
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)

def block_for_ts(w3, ts, chain=None, rpc_chain=None, rotate_keys=True):
    """
    Binary search for block at timestamp.

    Args:
        w3: Web3 instance (used if rotate_keys=False)
        ts: Target timestamp
        chain: Chain name for POA detection (required if rotate_keys=True)
        rpc_chain: RPC chain name if different from chain
        rotate_keys: If True, rotate to fresh connection every few RPC calls
    """
    lo, hi = 1, w3.eth.block_number
    ans = hi
    call_count = 0

    while lo <= hi:
        mid = (lo + hi) // 2

        # Rotate to fresh connection every 3 calls to distribute load across keys
        if rotate_keys and chain and call_count > 0 and call_count % 3 == 0:
            w3 = get_web3_with_poa(chain, rpc_chain)  # Gets connection with POA middleware

        t = w3.eth.get_block(mid)["timestamp"]
        call_count += 1

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


def load_existing_cache(output_file: Path) -> dict:
    """Load existing cache from file if it exists."""
    if output_file.exists():
        try:
            with open(output_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"[Warning] Could not load existing cache: {e}")
    return {}


def build_cache_for_chain(chain: str, dates: list, output_file: Path, save_interval: int = 10):
    """
    Build date→block cache for a specific chain with incremental support.

    Args:
        chain: Chain name (e.g., 'ethereum')
        dates: List of date strings (YYYY-MM-DD)
        output_file: Path to save cache JSON
        save_interval: Save cache to disk every N dates (for crash recovery)
    """
    print(f"\n{'='*60}")
    print(f"Building block cache for {chain}")
    print(f"{'='*60}\n")

    # Load existing cache (incremental support)
    cache = load_existing_cache(output_file)
    existing_count = len(cache)
    if existing_count > 0:
        print(f"[Incremental] Loaded {existing_count} existing dates from cache")

    # Filter to only dates we don't have yet
    missing_dates = [d for d in dates if d not in cache]
    if not missing_dates:
        print(f"[Complete] All {len(dates)} dates already cached!")
        return

    print(f"[Missing] Need to fetch {len(missing_dates)}/{len(dates)} dates\n")

    # Resolve chain alias if needed
    rpc_chain = CHAIN_ALIASES.get(chain, chain)
    if chain != rpc_chain:
        print(f"[Alias] Using RPC chain name '{rpc_chain}' for config chain '{chain}'\n")

    # Test connection with POA middleware
    w3 = get_web3_with_poa(chain, rpc_chain)
    if chain in POA_CHAINS:
        print(f"[POA] Using POA middleware for {chain}")

    try:
        latest = w3.eth.block_number
        print(f"Connected to {chain}: latest block = {latest}\n")
    except Exception as e:
        print(f"❌ Failed to connect to {chain}: {e}")
        return

    fetched_count = 0
    error_count = 0

    for i, date_str in enumerate(missing_dates, 1):
        try:
            # Get fresh connection with POA middleware (rotates through API keys)
            w3 = get_web3_with_poa(chain, rpc_chain)

            # Get UTC window for this NY date
            ts_start_utc, ts_end_utc = ny_date_to_utc_window(date_str)

            # Find block at end of day (snapshot time) - rotates keys during binary search
            block_num = block_for_ts(w3, ts_end_utc, chain=chain, rpc_chain=rpc_chain, rotate_keys=True)

            # Safety: subtract 1 to ensure block is from target day
            block_num = max(1, block_num - 1)

            # Get block timestamp for verification (rotates to next key)
            w3 = get_web3_with_poa(chain, rpc_chain)
            block = w3.eth.get_block(block_num)
            block_ts = block['timestamp']

            cache[date_str] = {
                'block': block_num,
                'timestamp': block_ts,
                'ts_start_utc': ts_start_utc,
                'ts_end_utc': ts_end_utc,
            }

            fetched_count += 1
            print(f"[{i}/{len(missing_dates)}] {date_str} → block {block_num} (ts={block_ts})")

            # Periodic save for crash recovery
            if fetched_count % save_interval == 0:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(cache, f, indent=2)
                print(f"    [Checkpoint] Saved {len(cache)} dates to cache")

        except Exception as e:
            error_count += 1
            print(f"❌ [{i}/{len(missing_dates)}] Failed to get block for {date_str}: {e}")
            # Save on error too, to preserve progress
            if fetched_count > 0:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w') as f:
                    json.dump(cache, f, indent=2)
            continue

    # Final save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cache, f, indent=2)

    print(f"\n✅ Saved cache to {output_file}")
    print(f"   Total cached: {len(cache)}/{len(dates)} dates")
    print(f"   This run: +{fetched_count} fetched, {error_count} errors\n")


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
