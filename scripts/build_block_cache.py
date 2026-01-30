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
import time
from datetime import date, datetime, timedelta, timezone
import argparse
import pytz
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

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
POA_CHAINS = ['binance', 'polygon', 'gnosis', 'avalanche', 'optimism', 'linea', 'scroll', 'xdai', 'cronos', 'meter', 'flare', 'sonic', 'plasma']

# Chain name aliases (config name -> RPC pool name)
CHAIN_ALIASES = {
    'xdai': 'gnosis',  # xdai in config, but gnosis in RPC pool
}

# Alchemy chain slugs
ALCHEMY_CHAIN_SLUGS = {
    'ethereum': 'eth-mainnet',
    'arbitrum': 'arb-mainnet',
    'optimism': 'opt-mainnet',
    'base': 'base-mainnet',
    'polygon': 'polygon-mainnet',
    'avalanche': 'avax-mainnet',
    'binance': 'bnb-mainnet',
    'linea': 'linea-mainnet',
    'gnosis': 'gnosis-mainnet',
    'scroll': 'scroll-mainnet',
    'sonic': 'sonic-mainnet',
    'ink': 'ink-mainnet',
    'plasma': 'plasma-mainnet',
}


def load_alchemy_keys():
    """Load all Alchemy API keys from environment."""
    keys = []
    for i in range(1, 20):
        key = os.environ.get(f'ALCHEMY_KEY_{i}')
        if key:
            keys.append((i, key))
    return keys


ALCHEMY_KEYS = load_alchemy_keys()
_current_key_index = 0


def get_next_alchemy_key():
    """Get the next Alchemy key in rotation."""
    global _current_key_index
    if not ALCHEMY_KEYS:
        raise ValueError("No Alchemy keys configured")
    key_num, key = ALCHEMY_KEYS[_current_key_index]
    _current_key_index = (_current_key_index + 1) % len(ALCHEMY_KEYS)
    return key_num, key


def create_web3_for_chain(chain: str, key: str) -> Web3:
    """Create a Web3 instance for a specific chain and key."""
    rpc_chain = CHAIN_ALIASES.get(chain, chain)

    if rpc_chain not in ALCHEMY_CHAIN_SLUGS:
        raise ValueError(f"Chain {rpc_chain} not supported by Alchemy")

    slug = ALCHEMY_CHAIN_SLUGS[rpc_chain]
    url = f"https://{slug}.g.alchemy.com/v2/{key}"

    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 30}))

    # Inject POA middleware if needed
    if chain in POA_CHAINS and geth_poa_middleware:
        try:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except Exception:
            pass

    return w3


def get_web3_with_rotation(chain: str):
    """Get a Web3 instance using the next Alchemy key in rotation."""
    key_num, key = get_next_alchemy_key()
    w3 = create_web3_for_chain(chain, key)
    return w3, key_num


def to_dt(ts: int) -> datetime:
    """
    Convert a unix timestamp to an aware UTC datetime.
    Behavior mirrors liquidation utilities.
    """
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)

def block_for_ts_with_retry(chain: str, ts: int, latest_block: int, max_retries: int = 3):
    """
    Binary search for block at timestamp with key rotation and retries.

    Args:
        chain: Chain name
        ts: Target timestamp
        latest_block: Latest block number on chain
        max_retries: Max retries per RPC call

    Returns:
        Block number at or after timestamp

    Raises:
        Exception if all retries fail
    """
    lo, hi = 1, latest_block
    ans = hi

    while lo <= hi:
        mid = (lo + hi) // 2

        # Try to get block with retries and key rotation
        block_ts = None
        last_error = None

        for attempt in range(max_retries):
            try:
                w3, key_num = get_web3_with_rotation(chain)
                block_ts = w3.eth.get_block(mid)["timestamp"]
                break
            except Exception as e:
                last_error = e
                if '429' in str(e) or 'rate' in str(e).lower():
                    time.sleep(0.5 * (attempt + 1))  # Backoff
                continue

        if block_ts is None:
            raise Exception(f"Failed to get block {mid} after {max_retries} retries: {last_error}")

        if block_ts >= ts:
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


def build_cache_for_chain(chain: str, dates: list, output_file: Path, save_interval: int = 10, max_retries: int = 5):
    """
    Build date→block cache for a specific chain with incremental support.

    Args:
        chain: Chain name (e.g., 'ethereum')
        dates: List of date strings (YYYY-MM-DD)
        output_file: Path to save cache JSON
        save_interval: Save cache to disk every N dates (for crash recovery)
        max_retries: Max retries per date before failing

    Returns:
        True if all dates were cached successfully, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Building block cache for {chain}")
    print(f"{'='*60}\n")

    # Check chain is supported
    rpc_chain = CHAIN_ALIASES.get(chain, chain)
    if rpc_chain not in ALCHEMY_CHAIN_SLUGS:
        print(f"❌ Chain {chain} not supported by Alchemy")
        return False

    print(f"[Config] Using {len(ALCHEMY_KEYS)} Alchemy keys with rotation")
    if chain in POA_CHAINS:
        print(f"[POA] Using POA middleware for {chain}")

    # Load existing cache (incremental support)
    cache = load_existing_cache(output_file)
    existing_count = len(cache)
    if existing_count > 0:
        print(f"[Incremental] Loaded {existing_count} existing dates from cache")

    # Filter to only dates we don't have yet
    missing_dates = [d for d in dates if d not in cache]
    if not missing_dates:
        print(f"[Complete] All {len(dates)} dates already cached!")
        return True

    print(f"[Missing] Need to fetch {len(missing_dates)}/{len(dates)} dates\n")

    # Test connection and get latest block
    try:
        w3, key_num = get_web3_with_rotation(chain)
        latest_block = w3.eth.block_number
        print(f"Connected to {chain} (key {key_num}): latest block = {latest_block:,}\n")
    except Exception as e:
        print(f"❌ Failed to connect to {chain}: {e}")
        return False

    fetched_count = 0
    failed_dates = []

    for i, date_str in enumerate(missing_dates, 1):
        success = False
        last_error = None

        # Retry loop for this date
        for attempt in range(max_retries):
            try:
                # Get UTC window for this NY date
                ts_start_utc, ts_end_utc = ny_date_to_utc_window(date_str)

                # Find block at end of day (snapshot time) with key rotation
                block_num = block_for_ts_with_retry(chain, ts_end_utc, latest_block, max_retries=3)

                # Safety: subtract 1 to ensure block is from target day
                block_num = max(1, block_num - 1)

                # Get block timestamp for verification with retry
                block_ts = None
                for verify_attempt in range(3):
                    try:
                        w3, _ = get_web3_with_rotation(chain)
                        block = w3.eth.get_block(block_num)
                        block_ts = block['timestamp']
                        break
                    except Exception as e:
                        if verify_attempt == 2:
                            raise e
                        time.sleep(0.3 * (verify_attempt + 1))

                cache[date_str] = {
                    'block': block_num,
                    'timestamp': block_ts,
                    'ts_start_utc': ts_start_utc,
                    'ts_end_utc': ts_end_utc,
                }

                fetched_count += 1
                print(f"[{i}/{len(missing_dates)}] {date_str} → block {block_num:,} (ts={block_ts})")
                success = True
                break

            except Exception as e:
                last_error = e
                if '429' in str(e) or 'rate' in str(e).lower():
                    wait_time = 1.0 * (attempt + 1)
                    print(f"  [Retry {attempt+1}/{max_retries}] Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  [Retry {attempt+1}/{max_retries}] Error: {str(e)[:60]}")
                    time.sleep(0.5)

        if not success:
            failed_dates.append(date_str)
            print(f"❌ [{i}/{len(missing_dates)}] FAILED {date_str} after {max_retries} retries: {last_error}")

        # Periodic save for crash recovery
        if fetched_count > 0 and fetched_count % save_interval == 0:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(cache, f, indent=2)
            print(f"    [Checkpoint] Saved {len(cache)} dates to cache")

    # Final save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cache, f, indent=2)

    # Report results
    print(f"\n{'='*60}")
    if failed_dates:
        print(f"❌ INCOMPLETE: {len(failed_dates)} dates failed")
        print(f"   Failed dates: {', '.join(failed_dates[:10])}{'...' if len(failed_dates) > 10 else ''}")
        print(f"   Saved cache to {output_file}")
        print(f"   Total cached: {len(cache)}/{len(dates)} dates")
        print(f"   This run: +{fetched_count} fetched, {len(failed_dates)} failed")
        return False
    else:
        print(f"✅ SUCCESS: All {len(missing_dates)} dates fetched")
        print(f"   Saved cache to {output_file}")
        print(f"   Total cached: {len(cache)}/{len(dates)} dates")
        return True


def main():
    parser = argparse.ArgumentParser(description='Build date→block cache')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--chain', '--chains', nargs='+', dest='chains',
                       default=['ethereum', 'arbitrum', 'base', 'optimism'],
                       help='Chains to build cache for')
    parser.add_argument('--output-dir', default='data/cache',
                       help='Output directory for cache files')
    parser.add_argument('--max-retries', type=int, default=5,
                       help='Max retries per date (default: 5)')

    args = parser.parse_args()

    # Generate date list
    dates = list(iterate_dates(args.start_date, args.end_date))

    print(f"\n{'='*60}")
    print(f"Block Cache Builder")
    print(f"{'='*60}")
    print(f"Date range: {args.start_date} → {args.end_date}")
    print(f"Total dates: {len(dates)}")
    print(f"Chains: {', '.join(args.chains)}")
    print(f"Alchemy keys: {len(ALCHEMY_KEYS)}")
    print(f"Max retries per date: {args.max_retries}")
    print(f"{'='*60}\n")

    output_dir = Path(args.output_dir)

    # Build cache for each chain, track failures
    results = {}
    for chain in args.chains:
        output_file = output_dir / f"{chain}_blocks_{args.start_date}_{args.end_date}.json"
        success = build_cache_for_chain(chain, dates, output_file, max_retries=args.max_retries)
        results[chain] = success

    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")

    success_count = sum(1 for v in results.values() if v)
    fail_count = len(results) - success_count

    for chain, success in results.items():
        status = "✅ Complete" if success else "❌ INCOMPLETE"
        print(f"  {chain}: {status}")

    print(f"\n  Total: {success_count}/{len(results)} chains complete")

    if fail_count > 0:
        print(f"\n❌ {fail_count} chain(s) have incomplete caches!")
        print("   Re-run the script to retry failed dates.")
        sys.exit(1)
    else:
        print(f"\n✅ All chains complete!")
        sys.exit(0)


if __name__ == '__main__':
    main()
