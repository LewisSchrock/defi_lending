#!/usr/bin/env python3
"""
Convert enriched JSONL files to parquet format for gold pipeline.

Reads: data/silver/liquidations/{chain}/events_enriched.jsonl
Writes: data/silver/liquidations/{chain}/liquidations.parquet

Usage:
    python scripts/convert_enriched_to_parquet.py --chain ethereum
    python scripts/convert_enriched_to_parquet.py --chain all
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from glob import glob

import pandas as pd

SILVER_DIR = Path("data/silver/liquidations")
CACHE_DIR = Path("data/cache")


def load_block_ranges(chain: str) -> list:
    """Load block ranges for date lookup from cache files.

    Returns a list of (start_block, end_block, date, timestamp) tuples.
    """
    # Map chain names to cache file prefixes
    chain_prefix_map = {
        "ethereum": "ethereum",
        "arbitrum": "arbitrum",
        "optimism": "optimism",
        "polygon": "polygon",
        "avalanche": "avalanche",
        "bsc": "binance",
        "base": "base",
        "linea": "linea",
        "scroll": "scroll",
        "gnosis": ["gnosis", "xdai"],
        "ink": "ink",
    }

    prefixes = chain_prefix_map.get(chain, [chain])
    if isinstance(prefixes, str):
        prefixes = [prefixes]

    # Collect all date -> block info
    date_blocks = {}
    for prefix in prefixes:
        cache_files = glob(str(CACHE_DIR / f"{prefix}_blocks_*.json"))
        for cache_file in cache_files:
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                    for date_str, block_info in data.items():
                        if isinstance(block_info, dict):
                            block = block_info.get("block")
                            ts = block_info.get("timestamp")
                            if block:
                                date_blocks[date_str] = {"block": int(block), "timestamp": ts}
            except Exception:
                pass

    if not date_blocks:
        return []

    # Sort by date and create block ranges
    sorted_dates = sorted(date_blocks.keys())
    block_ranges = []
    for i, date in enumerate(sorted_dates):
        info = date_blocks[date]
        start_block = info["block"]
        # End block is the start of next day (exclusive)
        if i + 1 < len(sorted_dates):
            end_block = date_blocks[sorted_dates[i + 1]]["block"]
        else:
            end_block = float("inf")
        block_ranges.append((start_block, end_block, date, info["timestamp"]))

    return block_ranges


def find_date_for_block(block_num, block_ranges: list):
    """Find date for a block number using the block ranges."""
    if not block_ranges or pd.isna(block_num):
        return None

    block_num = int(block_num)

    # Binary search for efficiency
    left, right = 0, len(block_ranges) - 1
    while left <= right:
        mid = (left + right) // 2
        start, end, date, ts = block_ranges[mid]
        if start <= block_num < end:
            return date
        elif block_num < start:
            right = mid - 1
        else:
            left = mid + 1

    # Not found in exact range - return closest
    if block_num < block_ranges[0][0]:
        return block_ranges[0][2]
    return block_ranges[-1][2]


def convert_chain(chain: str) -> dict:
    """Convert enriched JSONL to parquet for a single chain."""
    input_file = SILVER_DIR / chain / "events_enriched.jsonl"
    output_file = SILVER_DIR / chain / "liquidations.parquet"

    if not input_file.exists():
        return {"chain": chain, "status": "error", "error": "input not found"}

    print(f"\nProcessing {chain}...")

    # Load block ranges for date lookup
    block_ranges = load_block_ranges(chain)
    print(f"  Block ranges: {len(block_ranges):,} dates")

    # Load JSONL
    events = []
    with open(input_file) as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    print(f"  Loaded {len(events):,} events")

    if not events:
        return {"chain": chain, "status": "error", "error": "no events"}

    # Convert to DataFrame
    df = pd.DataFrame(events)

    # Rename columns to match expected schema
    column_map = {
        "collateral_value_usd": "collateral_usd",
        "debt_value_usd": "debt_usd",
    }
    df = df.rename(columns=column_map)

    # Add missing columns
    if "chain" not in df.columns:
        df["chain"] = chain

    # Derive date from block number using block ranges
    if "block_number" in df.columns:
        # Initialize date column if missing
        if "date" not in df.columns:
            df["date"] = None

        # Fill missing dates from timestamp columns first
        missing_date_mask = df["date"].isna()
        if missing_date_mask.any():
            if "block_timestamp" in df.columns:
                ts_mask = missing_date_mask & df["block_timestamp"].notna()
                if ts_mask.any():
                    df.loc[ts_mask, "date"] = pd.to_datetime(df.loc[ts_mask, "block_timestamp"], unit="s").dt.strftime("%Y-%m-%d")

            if "timestamp" in df.columns:
                missing_date_mask = df["date"].isna()
                ts_mask = missing_date_mask & df["timestamp"].notna()
                if ts_mask.any():
                    df.loc[ts_mask, "date"] = pd.to_datetime(df.loc[ts_mask, "timestamp"], unit="s").dt.strftime("%Y-%m-%d")

        # Fill remaining missing dates from block ranges
        missing_date_mask = df["date"].isna()
        if missing_date_mask.any() and block_ranges:
            df.loc[missing_date_mask, "date"] = df.loc[missing_date_mask, "block_number"].apply(
                lambda b: find_date_for_block(b, block_ranges)
            )

        # Handle block_timestamp
        if "block_timestamp" not in df.columns:
            if "timestamp" in df.columns:
                df["block_timestamp"] = df["timestamp"]
            else:
                df["block_timestamp"] = None

    # Fallback for missing columns
    if "date" not in df.columns:
        df["date"] = None
    if "block_timestamp" not in df.columns:
        df["block_timestamp"] = None

    # Select and order columns
    columns = [
        "tx_hash", "log_index", "block_number", "block_timestamp", "date",
        "chain", "protocol", "csu", "borrower", "liquidator",
        "collateral_asset", "collateral_symbol", "collateral_decimals",
        "collateral_amount", "collateral_usd",
        "debt_asset", "debt_symbol", "debt_decimals",
        "debt_amount", "debt_usd"
    ]

    # Only keep columns that exist
    existing_cols = [c for c in columns if c in df.columns]
    df = df[existing_cols]

    # Save to parquet
    df.to_parquet(output_file, index=False)

    # Stats
    n_priced = df["collateral_usd"].notna().sum()
    pct_priced = 100 * n_priced / len(df) if len(df) > 0 else 0
    total_usd = df["collateral_usd"].sum()

    print(f"  Saved {len(df):,} events to parquet")
    print(f"  Priced: {n_priced:,} ({pct_priced:.1f}%)")
    print(f"  Total collateral USD: ${total_usd:,.0f}")

    return {
        "chain": chain,
        "status": "success",
        "events": len(df),
        "priced": n_priced,
        "total_usd": total_usd
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chain", required=True, help="Chain to convert or 'all'")
    args = parser.parse_args()

    print("=" * 60)
    print("Converting Enriched JSONL to Parquet")
    print("=" * 60)

    if args.chain == "all":
        chains = [d.name for d in SILVER_DIR.iterdir()
                  if d.is_dir() and (d / "events_enriched.jsonl").exists()]
    else:
        chains = [args.chain]

    print(f"Chains: {', '.join(chains)}")

    results = []
    for chain in chains:
        result = convert_chain(chain)
        results.append(result)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_events = 0
    total_priced = 0
    total_usd = 0

    for r in results:
        if r["status"] == "success":
            total_events += r["events"]
            total_priced += r["priced"]
            total_usd += r["total_usd"]
            print(f"  {r['chain']}: {r['events']:,} events, ${r['total_usd']:,.0f}")
        else:
            print(f"  {r['chain']}: ERROR - {r.get('error')}")

    print()
    print(f"Total: {total_events:,} events, {total_priced:,} priced, ${total_usd:,.0f}")


if __name__ == "__main__":
    main()
