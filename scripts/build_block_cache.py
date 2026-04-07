#!/usr/bin/env python3
"""
Block Cache Builder (Optimized for dRPC paid plan)

Pre-computes date→block mappings for a date range.
Uses persistent connections and block time estimation for speed.

Usage:
    python scripts/build_block_cache.py --start-date 2024-01-01 --end-date 2026-02-23 --chain celo blast zksync fantom
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add parent to path BEFORE importing project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        geth_poa_middleware = None

from config.rpc_pool_v2 import get_web3_with_info, PUBLIC_RPCS

NY_TZ = pytz.timezone("America/New_York")

# Chains that use POA (Proof of Authority) or have non-standard extraData
POA_CHAINS = {'binance', 'polygon', 'gnosis', 'avalanche', 'optimism', 'linea',
              'scroll', 'xdai', 'cronos', 'meter', 'flare', 'sonic', 'plasma',
              'celo', 'blast', 'manta', 'fantom'}

CHAIN_ALIASES = {'xdai': 'gnosis'}

# Average block times (seconds) for initial estimation — refined at runtime
AVG_BLOCK_TIMES = {
    'ethereum': 12, 'arbitrum': 0.25, 'base': 2, 'optimism': 2,
    'polygon': 2, 'avalanche': 2, 'binance': 3, 'linea': 3,
    'gnosis': 5, 'scroll': 3, 'sonic': 1, 'ink': 2, 'plasma': 2,
    'cronos': 6, 'meter': 2, 'flare': 2, 'celo': 5, 'blast': 2,
    'zksync': 1, 'manta': 2, 'fantom': 1,
}


class ChainConnection:
    """Persistent Web3 connection with automatic reconnect."""

    def __init__(self, chain: str):
        self.chain = chain
        self.rpc_chain = CHAIN_ALIASES.get(chain, chain)
        self.w3 = None
        self._connect()

    def _connect(self):
        """Establish connection via rpc_pool_v2."""
        for attempt in range(5):
            try:
                self.w3, _, _ = get_web3_with_info(self.rpc_chain)
                if self.chain in POA_CHAINS and geth_poa_middleware:
                    try:
                        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    except Exception:
                        pass
                self.w3.eth.block_number  # Test
                return
            except Exception:
                time.sleep(0.3 * (attempt + 1))

        # Fallback to public RPCs
        for url in PUBLIC_RPCS.get(self.rpc_chain, []):
            try:
                self.w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 30}))
                if self.chain in POA_CHAINS and geth_poa_middleware:
                    try:
                        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    except Exception:
                        pass
                self.w3.eth.block_number  # Test
                return
            except Exception:
                continue
        raise ConnectionError(f"Could not connect to any RPC for {self.chain}")

    def get_block(self, block_num: int, max_retries: int = 3) -> dict:
        """Get a block with auto-reconnect on failure."""
        for attempt in range(max_retries):
            try:
                return self.w3.eth.get_block(block_num)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                err = str(e).lower()
                if '429' in err or 'rate' in err:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    self._connect()

    def get_block_ts(self, block_num: int) -> int:
        """Get just the timestamp for a block."""
        return self.get_block(block_num)['timestamp']

    @property
    def latest_block(self) -> int:
        for attempt in range(3):
            try:
                return self.w3.eth.block_number
            except Exception:
                self._connect()
        raise ConnectionError(f"Cannot get latest block for {self.chain}")


def block_for_ts(conn: ChainConnection, ts: int, latest_block: int,
                 hint_block: int = None, avg_block_time: float = None) -> int:
    """
    Find block at timestamp using estimation + narrowed binary search.
    Much faster than pure binary search — typically 3-5 RPC calls instead of 25+.
    """
    # Phase 1: Estimate starting block using block time
    if hint_block and avg_block_time and avg_block_time > 0:
        hint_ts = conn.get_block_ts(hint_block)
        estimated_block = hint_block + int((ts - hint_ts) / avg_block_time)
        estimated_block = max(1, min(estimated_block, latest_block))
    else:
        # No hint — estimate from genesis
        latest_ts = conn.get_block_ts(latest_block)
        if latest_ts > ts:
            ratio = (ts - conn.get_block_ts(1)) / (latest_ts - conn.get_block_ts(1))
            estimated_block = max(1, int(latest_block * ratio))
        else:
            estimated_block = latest_block

    # Phase 2: Check estimate and determine search direction
    est_ts = conn.get_block_ts(estimated_block)

    # Phase 3: Narrow down with exponential probing
    if est_ts >= ts:
        # Block is at or after target — search backwards
        hi = estimated_block
        step = max(1, int(86400 / (avg_block_time or 12)))  # ~1 day of blocks
        lo = max(1, estimated_block - step)
        while conn.get_block_ts(lo) >= ts and lo > 1:
            hi = lo
            step *= 2
            lo = max(1, lo - step)
    else:
        # Block is before target — search forwards
        lo = estimated_block
        step = max(1, int(86400 / (avg_block_time or 12)))
        hi = min(latest_block, estimated_block + step)
        while conn.get_block_ts(hi) < ts and hi < latest_block:
            lo = hi
            step *= 2
            hi = min(latest_block, hi + step)

    # Phase 4: Tight binary search in narrow range
    ans = hi
    while lo <= hi:
        mid = (lo + hi) // 2
        mid_ts = conn.get_block_ts(mid)
        if mid_ts >= ts:
            ans = mid
            hi = mid - 1
        else:
            lo = mid + 1

    return ans


def ny_date_to_utc_window(date_str: str) -> tuple[int, int]:
    d = datetime.fromisoformat(date_str).date()
    start_ny = NY_TZ.localize(datetime(d.year, d.month, d.day, 0, 0, 0))
    end_ny = start_ny + timedelta(days=1)
    return int(start_ny.astimezone(timezone.utc).timestamp()), int(end_ny.astimezone(timezone.utc).timestamp())


def iterate_dates(start_str: str, end_str: str):
    d0 = date.fromisoformat(start_str)
    d1 = date.fromisoformat(end_str)
    d = d0
    while d <= d1:
        yield d.isoformat()
        d += timedelta(days=1)


def load_existing_cache(output_file: Path) -> dict:
    if output_file.exists():
        try:
            with open(output_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def build_cache_for_chain(chain: str, dates: list, output_file: Path,
                          save_interval: int = 25, max_retries: int = 5):
    print(f"\n{'='*60}")
    print(f"Building block cache for {chain}")
    print(f"{'='*60}\n")

    print(f"[Config] Using rpc_pool_v2 (dRPC paid plan, no rate limit)")
    if chain in POA_CHAINS:
        print(f"[POA] Using POA middleware for {chain}")

    # Load existing cache (incremental)
    cache = load_existing_cache(output_file)
    if cache:
        print(f"[Incremental] Loaded {len(cache)} existing dates")

    missing_dates = [d for d in dates if d not in cache]
    if not missing_dates:
        print(f"[Complete] All {len(dates)} dates already cached!")
        return True

    print(f"[Missing] Need {len(missing_dates)}/{len(dates)} dates\n")

    # Connect
    try:
        conn = ChainConnection(chain)
        latest_block = conn.latest_block
        print(f"Connected to {chain}: latest block = {latest_block:,}")
    except Exception as e:
        print(f"Failed to connect to {chain}: {e}")
        return False

    # Estimate avg block time from a recent sample
    avg_bt = AVG_BLOCK_TIMES.get(CHAIN_ALIASES.get(chain, chain), 2.0)
    try:
        sample_block = max(1, latest_block - 1000)
        sample_ts = conn.get_block_ts(sample_block)
        latest_ts = conn.get_block_ts(latest_block)
        if latest_ts > sample_ts:
            avg_bt = (latest_ts - sample_ts) / (latest_block - sample_block)
            print(f"[Block time] {avg_bt:.3f}s/block (measured)")
    except Exception:
        print(f"[Block time] {avg_bt:.1f}s/block (default estimate)")

    print(f"[Speed] Using estimation + narrow binary search (~5 RPC calls/date)\n")

    fetched = 0
    failed = []
    last_block = None  # Use as hint for next date
    start_time = time.time()

    for i, date_str in enumerate(missing_dates, 1):
        for attempt in range(max_retries):
            try:
                ts_start, ts_end = ny_date_to_utc_window(date_str)
                block_num = block_for_ts(conn, ts_end, latest_block,
                                        hint_block=last_block, avg_block_time=avg_bt)
                block_num = max(1, block_num - 1)
                block_ts = conn.get_block_ts(block_num)

                cache[date_str] = {
                    'block': block_num,
                    'timestamp': block_ts,
                    'ts_start_utc': ts_start,
                    'ts_end_utc': ts_end,
                }
                last_block = block_num
                fetched += 1

                # Progress report
                elapsed = time.time() - start_time
                rate = fetched / elapsed if elapsed > 0 else 0
                eta = (len(missing_dates) - i) / rate if rate > 0 else 0
                if i <= 5 or i % 50 == 0 or i == len(missing_dates):
                    print(f"[{i}/{len(missing_dates)}] {date_str} → block {block_num:,} "
                          f"({rate:.1f} dates/s, ETA {eta/60:.1f}min)")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    failed.append(date_str)
                    print(f"[{i}] FAILED {date_str}: {str(e)[:60]}")
                else:
                    time.sleep(0.5)
                    try:
                        conn._connect()
                    except Exception:
                        pass

        # Periodic save
        if fetched > 0 and fetched % save_interval == 0:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(cache, f, indent=2)

    # Final save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cache, f, indent=2)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    if failed:
        print(f"INCOMPLETE: {len(failed)} dates failed ({elapsed:.0f}s)")
        print(f"   Cached: {len(cache)}/{len(dates)} | This run: +{fetched}")
        return False
    else:
        print(f"SUCCESS: {fetched} dates in {elapsed:.0f}s ({fetched/elapsed:.1f}/s)")
        print(f"   Cached: {len(cache)}/{len(dates)} total")
        return True


def main():
    parser = argparse.ArgumentParser(description='Build date→block cache')
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    parser.add_argument('--chain', '--chains', nargs='+', dest='chains',
                       default=['ethereum', 'arbitrum', 'base', 'optimism'])
    parser.add_argument('--output-dir', default='data/cache')
    parser.add_argument('--max-retries', type=int, default=5)

    args = parser.parse_args()
    dates = list(iterate_dates(args.start_date, args.end_date))

    print(f"\n{'='*60}")
    print(f"Block Cache Builder (dRPC optimized)")
    print(f"{'='*60}")
    print(f"Date range: {args.start_date} → {args.end_date} ({len(dates)} dates)")
    print(f"Chains: {', '.join(args.chains)}")
    print(f"{'='*60}\n")

    output_dir = Path(args.output_dir)
    results = {}
    for chain in args.chains:
        output_file = output_dir / f"{chain}_blocks_{args.start_date}_{args.end_date}.json"
        results[chain] = build_cache_for_chain(chain, dates, output_file, max_retries=args.max_retries)

    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    for chain, ok in results.items():
        print(f"  {chain}: {'Complete' if ok else 'INCOMPLETE'}")
    ok_count = sum(1 for v in results.values() if v)
    print(f"\n  {ok_count}/{len(results)} chains complete")
    sys.exit(0 if ok_count == len(results) else 1)


if __name__ == '__main__':
    main()
