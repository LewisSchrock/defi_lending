#!/usr/bin/env python3
"""
Liquidation Event Collector using dRPC

Optimized for high-throughput collection using dRPC paid endpoints.
Uses 50,000 block chunks based on validation tests.

Usage:
    python scripts/collect_liquidations_drpc.py --chain ethereum
    python scripts/collect_liquidations_drpc.py --chain ethereum --start-date 2025-01-01
    python scripts/collect_liquidations_drpc.py --chain all  # All configured chains

    # Run with a specific API key by number (for parallel collection in separate terminals):
    python scripts/collect_liquidations_drpc.py --chain linea --key 2 --start-date 2024-01-01
    python scripts/collect_liquidations_drpc.py --chain scroll --key 3 --start-date 2024-01-01
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# dRPC endpoints per chain (from .env)
# Primary key (DRPC_KEY_<CHAIN>) used by default
# Additional keys (DRPC_KEY_2, DRPC_KEY_3) for parallel collection
DRPC_KEYS = {
    "ethereum": os.environ.get("DRPC_KEY_ETHEREUM", ""),
    "arbitrum": os.environ.get("DRPC_KEY_ARBITRUM", ""),
    "optimism": os.environ.get("DRPC_KEY_OPTIMISM", ""),
    "polygon": os.environ.get("DRPC_KEY_POLYGON", ""),
    "avalanche": os.environ.get("DRPC_KEY_AVALANCHE", ""),
    "bsc": os.environ.get("DRPC_KEY_BSC", ""),
    "base": os.environ.get("DRPC_KEY_BASE", ""),
    "linea": os.environ.get("DRPC_KEY_LINEA", ""),
    "scroll": os.environ.get("DRPC_KEY_SCROLL", ""),
    "gnosis": os.environ.get("DRPC_KEY_GNOSIS", ""),
    "plasma": os.environ.get("DRPC_KEY_PLASMA", ""),
    "ink": os.environ.get("DRPC_KEY_INK", ""),
    "flare": os.environ.get("DRPC_KEY_FLARE", ""),
    "meter": os.environ.get("DRPC_KEY_METER", ""),
}

# Additional API keys for parallel collection (chain-agnostic)
DRPC_EXTRA_KEYS = [
    os.environ.get("DRPC_KEY_2", ""),
    os.environ.get("DRPC_KEY_3", ""),
]

# Collection settings - chunk sizes per chain (dense chains need smaller chunks)
CHUNK_SIZES = {
    "ethereum": 50000,   # 12s blocks, sparse
    "arbitrum": 50000,   # 0.25s blocks but sparse liquidations
    "optimism": 50000,   # 2s blocks, sparse
    "polygon": 1000,     # 2s blocks, VERY dense - dRPC 10s timeout limit
    "avalanche": 5000,   # 2s blocks
    "bsc": 3000,         # 3s blocks, dense
    "base": 10000,       # 2s blocks
    "linea": 10000,      # 2s blocks
    "scroll": 10000,     # 3s blocks
    "gnosis": 10000,     # 5s blocks
    "plasma": 10000,     # 2s blocks, new chain
    "ink": 10000,        # 1s blocks, new chain
    "flare": 10000,      # 1s blocks
    "meter": 10000,      # 2s blocks
}
DEFAULT_CHUNK_SIZE = 10000

RETRY_MAX = 3
RETRY_BACKOFF = [1, 3, 10]  # seconds

# Liquidation event signatures
LIQUIDATION_TOPICS = [
    # Aave V3 / SparkLend / Tydro: LiquidationCall(address,address,address,uint256,uint256,address,bool)
    "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286",
    # Compound V3: AbsorbCollateral(address,address,address,uint256,uint256)
    "0x9850ab1af75177e4a7e9870da8a34d4979b71cc4cd596df22ba4fb8b571430b9",
    # Compound V3: AbsorbDebt(address,address,uint256,uint256) — FIX: was missing entirely
    "0x1547a878dc89ad3c367b6338b4be6a65a5dd74fb77ae044da1e8747ef1f4f62f",
    # Compound V2 / Venus / Benqi / Moonwell / Kinetic / Sumer: LiquidateBorrow(address,address,uint256,address,uint256)
    "0x298637f684da70674f26509b10f07ec2fbc77a335ab1e7d6215a4b2484d8bb52",
    # Fluid: Liquidation(address,address,address,address,uint256,uint256)
    # FIX: was wrong topic0 from 'Liquidate(address,uint256,uint256,address,uint256,bool)'
    "0x64f7c2c46814e079964a1934953e50adc025dc52cdbeb7d8e478e9fb9bfd2c2d",
    # Gearbox: LiquidateCreditAccount(address,address,address,uint256)
    "0x7dfecd8419723a9d3954585a30c2a270165d70aafa146c11c1e1b88ae1439064",
    # Cap: Liquidate(address,address,uint256,uint256)
    "0xf3fa0eaee8f258c23b013654df25d1527f98a5c7ccd5e951dd77caca400ef972",
    # Lista (Morpho-style): Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)
    "0xa4946ede45d0c6f06a0f5ce92c9ad3b4751452d2fe0e25010783bcab57a67e41",
]

# Approximate block times (seconds per block) for date estimation
BLOCK_TIMES = {
    "ethereum": 12,
    "arbitrum": 0.25,
    "optimism": 2,
    "polygon": 2,
    "avalanche": 2,
    "bsc": 3,
    "base": 2,
    "linea": 2,
    "scroll": 3,
    "gnosis": 5,
    "plasma": 2,
    "ink": 1,
    "flare": 1,
    "meter": 2,
}

# Approximate genesis/start blocks for each chain
CHAIN_START_BLOCKS = {
    "ethereum": 15537393,   # Merge block (Sep 2022)
    "arbitrum": 1,
    "optimism": 1,
    "polygon": 1,
    "avalanche": 1,
    "bsc": 1,
    "base": 1,
    "linea": 1,
    "scroll": 1,
    "gnosis": 1,
    "plasma": 1,
    "ink": 1,
    "flare": 1,
    "meter": 1,
}

# Output directory
OUTPUT_DIR = Path("data/bronze/liquidations")


# ==============================================================================
# UTILITIES
# ==============================================================================

def get_drpc_url(chain: str) -> str:
    """Get dRPC endpoint URL for a chain."""
    value = DRPC_KEYS.get(chain, "")
    if not value:
        raise ValueError(f"DRPC_KEY_{chain.upper()} not configured")
    if value.startswith("http"):
        return value
    return f"https://lb.drpc.org/ogrpc?network={chain}&dkey={value}"


async def eth_block_number(session: aiohttp.ClientSession, url: str) -> int:
    """Get current block number."""
    payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
    async with session.post(url, json=payload) as resp:
        result = await resp.json()
    if "error" in result:
        raise Exception(f"RPC error: {result['error']}")
    return int(result["result"], 16)


async def eth_get_logs(
    session: aiohttp.ClientSession,
    url: str,
    from_block: int,
    to_block: int,
    topics: List[str],
) -> List[Dict]:
    """Call eth_getLogs with retry logic."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",
        "params": [{
            "fromBlock": hex(from_block),
            "toBlock": hex(to_block),
            "topics": [topics],  # OR of all topics
        }],
        "id": 1,
    }

    for attempt in range(RETRY_MAX):
        try:
            async with session.post(url, json=payload) as resp:
                result = await resp.json()

            if "error" in result:
                error_msg = str(result["error"])
                # Check for response too large error
                if "too large" in error_msg.lower() or "limit" in error_msg.lower():
                    raise Exception(f"Response too large for {to_block - from_block} blocks")
                raise Exception(f"RPC error: {error_msg}")

            return result.get("result", [])

        except Exception as e:
            if attempt < RETRY_MAX - 1:
                wait = RETRY_BACKOFF[attempt]
                print(f"    Retry {attempt + 1}/{RETRY_MAX} after {wait}s: {str(e)[:50]}")
                await asyncio.sleep(wait)
            else:
                raise


async def get_block_timestamp(session: aiohttp.ClientSession, url: str, block_num: int) -> int:
    """Get timestamp for a specific block."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(block_num), False],
        "id": 1,
    }
    async with session.post(url, json=payload) as resp:
        result = await resp.json()
    if "error" in result or not result.get("result"):
        return 0
    return int(result["result"]["timestamp"], 16)


def estimate_block_for_date(chain: str, target_date: datetime, current_block: int, current_time: datetime) -> int:
    """Estimate block number for a target date."""
    seconds_diff = (current_time - target_date).total_seconds()
    block_time = BLOCK_TIMES.get(chain, 2)
    blocks_diff = int(seconds_diff / block_time)
    estimated = current_block - blocks_diff
    return max(estimated, CHAIN_START_BLOCKS.get(chain, 1))


def load_checkpoint(chain: str) -> Dict:
    """Load checkpoint for a chain."""
    checkpoint_file = OUTPUT_DIR / chain / "checkpoint.json"
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            data = json.load(f)
        # Normalize: other collectors use 'total_events' instead of 'events_count'
        if "events_count" not in data:
            data["events_count"] = data.get("total_events", 0)
        return data
    return {"last_block": 0, "events_count": 0}


def save_checkpoint(chain: str, last_block: int, events_count: int):
    """Save checkpoint for a chain."""
    checkpoint_file = OUTPUT_DIR / chain / "checkpoint.json"
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checkpoint_file, "w") as f:
        json.dump({
            "last_block": last_block,
            "events_count": events_count,
            "updated": datetime.now().isoformat(),
        }, f, indent=2)


def append_events(chain: str, events: List[Dict]):
    """Append events to JSONL file."""
    events_file = OUTPUT_DIR / chain / "events.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with open(events_file, "a") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")


# ==============================================================================
# MAIN COLLECTION
# ==============================================================================

async def collect_chain(chain: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
    """Collect liquidation events for a single chain."""
    print(f"\n{'=' * 60}")
    print(f"COLLECTING: {chain.upper()}")
    print(f"{'=' * 60}")

    url = get_drpc_url(chain)
    timeout = aiohttp.ClientTimeout(total=120, connect=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Get current block
        current_block = await eth_block_number(session, url)
        current_time = datetime.now()
        print(f"  Current block: {current_block:,}")

        # Determine block range
        checkpoint = load_checkpoint(chain)

        # Calculate the start block from date (if provided)
        if start_date:
            date_block = estimate_block_for_date(chain, start_date, current_block, current_time)
            print(f"  Start date: {start_date.date()} → estimated block {date_block:,}")
        else:
            # Default: start from 2024-01-01
            default_start = datetime(2024, 1, 1)
            date_block = estimate_block_for_date(chain, default_start, current_block, current_time)
            print(f"  Default start (2024-01-01): estimated block {date_block:,}")

        # Use checkpoint if it's ahead of the date-based start
        if checkpoint["last_block"] > 0 and checkpoint["last_block"] >= date_block:
            from_block = checkpoint["last_block"] + 1
            print(f"  Resuming from checkpoint: block {from_block:,} ({checkpoint['events_count']:,} events already collected)")
        else:
            from_block = date_block

        if end_date:
            to_block = estimate_block_for_date(chain, end_date, current_block, current_time)
            print(f"  End date: {end_date.date()} → estimated block {to_block:,}")
        else:
            to_block = current_block

        total_blocks = to_block - from_block
        if total_blocks <= 0:
            print(f"  No new blocks to process")
            return

        # Get chain-specific chunk size
        chunk_size = CHUNK_SIZES.get(chain, DEFAULT_CHUNK_SIZE)

        print(f"  Block range: {from_block:,} → {to_block:,} ({total_blocks:,} blocks)")
        print(f"  Chunk size: {chunk_size:,} blocks")
        print(f"  Estimated chunks: {(total_blocks // chunk_size) + 1}")
        print()

        # Collection loop
        total_events = checkpoint.get("events_count", 0)
        chunks_processed = 0
        start_time = time.time()

        block = from_block
        while block <= to_block:
            chunk_end = min(block + chunk_size - 1, to_block)

            try:
                events = await eth_get_logs(session, url, block, chunk_end, LIQUIDATION_TOPICS)

                if events:
                    # Add block timestamps (batch the first and last for efficiency)
                    for event in events:
                        event["_chain"] = chain
                        event["_collected"] = datetime.now().isoformat()

                    append_events(chain, events)
                    total_events += len(events)

                chunks_processed += 1
                progress = (block - from_block) / total_blocks * 100
                elapsed = time.time() - start_time
                blocks_per_sec = (block - from_block) / elapsed if elapsed > 0 else 0
                eta_sec = (to_block - block) / blocks_per_sec if blocks_per_sec > 0 else 0

                print(f"  [{progress:5.1f}%] Block {block:,}-{chunk_end:,} | "
                      f"{len(events)} events | Total: {total_events:,} | "
                      f"{blocks_per_sec:,.0f} blk/s | ETA: {eta_sec/60:.1f}m")

                # Save checkpoint periodically
                if chunks_processed % 10 == 0:
                    save_checkpoint(chain, chunk_end, total_events)

                block = chunk_end + 1

            except Exception as e:
                print(f"  ERROR at block {block}: {e}")
                # Save checkpoint and continue
                save_checkpoint(chain, block - 1, total_events)
                # Try smaller chunk on error (timeout or too large)
                error_str = str(e).lower()
                if "too large" in error_str or "timeout" in error_str or "-32002" in error_str:
                    print(f"  Reducing chunk size and retrying...")
                    smaller_end = min(block + chunk_size // 2 - 1, to_block)
                    try:
                        events = await eth_get_logs(session, url, block, smaller_end, LIQUIDATION_TOPICS)
                        if events:
                            for event in events:
                                event["_chain"] = chain
                            append_events(chain, events)
                            total_events += len(events)
                        block = smaller_end + 1
                        continue
                    except:
                        pass
                raise

        # Final checkpoint
        save_checkpoint(chain, to_block, total_events)

        elapsed = time.time() - start_time
        print(f"\n  DONE: {chain}")
        print(f"  Total events: {total_events:,}")
        print(f"  Time: {elapsed/60:.1f} minutes")
        print(f"  Avg speed: {total_blocks/elapsed:,.0f} blocks/sec")


async def collect_chain_with_key(chain: str, key_url: str, start_date: Optional[datetime], end_date: Optional[datetime]):
    """Wrapper to collect a chain using a specific key URL."""
    # Temporarily override the chain's key
    original_key = DRPC_KEYS.get(chain)
    # Extract base URL and replace chain slug
    # Key URL format: https://lb.drpc.live/ethereum/KEY -> https://lb.drpc.live/{chain}/KEY
    if "/ethereum/" in key_url:
        chain_url = key_url.replace("/ethereum/", f"/{chain}/")
    else:
        chain_url = key_url  # Already chain-specific
    DRPC_KEYS[chain] = chain_url
    try:
        await collect_chain(chain, start_date, end_date)
    finally:
        DRPC_KEYS[chain] = original_key


async def main():
    parser = argparse.ArgumentParser(description="Collect liquidation events via dRPC")
    parser.add_argument("--chain", required=True, help="Chain to collect (or 'all' or comma-separated list)")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--key", type=int, help="Use DRPC_KEY_N from .env (e.g., --key 2 uses DRPC_KEY_2)")
    parser.add_argument("--parallel", action="store_true", help="Run chains in parallel using multiple keys")
    args = parser.parse_args()

    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else None
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None

    # If --key N provided, use DRPC_KEY_N from .env for all chains
    selected_key = None
    if args.key:
        key_name = f"DRPC_KEY_{args.key}"
        selected_key = os.environ.get(key_name, "")
        if not selected_key:
            print(f"ERROR: {key_name} not found in .env")
            sys.exit(1)
        # Override all chain keys with this key
        for chain_name in DRPC_KEYS.keys():
            DRPC_KEYS[chain_name] = f"https://lb.drpc.org/ogrpc?network={chain_name}&dkey={selected_key}"
        print(f"Using {key_name}: {selected_key[:8]}...{selected_key[-4:]}")

    # Get chains to process
    configured = [c for c, k in DRPC_KEYS.items() if k]

    # All known chains
    all_known_chains = list(DRPC_KEYS.keys())

    if args.chain == "all":
        chains = configured
    elif "," in args.chain:
        # Comma-separated list of chains
        chains = [c.strip() for c in args.chain.split(",")]
        for c in chains:
            if c not in all_known_chains:
                print(f"ERROR: Unknown chain '{c}'")
                print(f"Known chains: {', '.join(all_known_chains)}")
                sys.exit(1)
            if c not in configured and not args.key:
                print(f"ERROR: Chain '{c}' not configured (no key in .env)")
                print(f"Use --key N to use DRPC_KEY_N, or add DRPC_KEY_{c.upper()} to .env")
                sys.exit(1)
    elif args.chain in all_known_chains:
        if args.chain not in configured and not args.key:
            print(f"ERROR: Chain '{args.chain}' not configured (no key in .env)")
            print(f"Use --key N to use DRPC_KEY_N, or add DRPC_KEY_{args.chain.upper()} to .env")
            sys.exit(1)
        chains = [args.chain]
    else:
        print(f"ERROR: Unknown chain '{args.chain}'")
        print(f"Known chains: {', '.join(all_known_chains)}")
        sys.exit(1)

    print("=" * 60)
    print("dRPC LIQUIDATION COLLECTOR")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    print(f"Chains: {', '.join(chains)}")
    print(f"Mode: {'PARALLEL' if args.parallel else 'SEQUENTIAL'}")
    if start_date:
        print(f"Start date: {start_date.date()}")
    if end_date:
        print(f"End date: {end_date.date()}")

    if args.parallel and len(chains) > 1:
        # Collect available keys (primary + extras)
        available_keys = []
        # Add primary keys that have URLs
        for chain, key in DRPC_KEYS.items():
            if key and key not in available_keys:
                available_keys.append(key)
                break  # Just need one primary
        # Add extra keys
        for key in DRPC_EXTRA_KEYS:
            if key and key not in available_keys:
                available_keys.append(key)

        print(f"Available keys for parallel: {len(available_keys)}")

        if len(available_keys) < len(chains):
            print(f"WARNING: Only {len(available_keys)} keys for {len(chains)} chains")
            print(f"         Some chains will run sequentially")

        # Create tasks for parallel execution
        tasks = []
        for i, chain in enumerate(chains):
            key_idx = i % len(available_keys)
            key_url = available_keys[key_idx]
            print(f"  {chain} → key #{key_idx + 1}")
            tasks.append(collect_chain_with_key(chain, key_url, start_date, end_date))

        # Run all chains in parallel
        print("\nStarting parallel collection...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Report results
        for chain, result in zip(chains, results):
            if isinstance(result, Exception):
                print(f"\nERROR on {chain}: {result}")
    else:
        # Sequential collection
        for chain in chains:
            try:
                await collect_chain(chain, start_date, end_date)
            except Exception as e:
                print(f"\nERROR on {chain}: {e}")
                continue

    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
