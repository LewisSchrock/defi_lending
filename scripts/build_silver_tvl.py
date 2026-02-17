#!/usr/bin/env python3
"""
Build Silver Layer TVL Data

Transforms bronze TVL data into aggregated silver layer:
- Converts raw token amounts to USD values
- Aggregates by CSU and date
- Calculates supply, borrow, and net TVL

Output Structure:
    data/silver/tvl/
    ├── daily_tvl.parquet       # Daily TVL per CSU
    └── market_breakdown.parquet # Per-market breakdown

Schema (daily_tvl):
    - date: str (YYYY-MM-DD)
    - csu: str
    - chain: str
    - protocol: str
    - version: str
    - total_supply_usd: float
    - total_borrow_usd: float
    - net_tvl_usd: float  (supply - borrow)
    - num_markets: int
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.rpc_pool_v2 import get_web3
from adapters.prices.price_service import (
    get_token_price,
    get_cached_price,
    preload_prices_for_date,
    save_all as save_price_cache,
    get_cache_stats,
    clear_not_found,
    get_not_found_tokens
)

# Paths
BRONZE_DIR = Path('data/bronze/tvl')
SILVER_DIR = Path('data/silver/tvl')


def get_token_symbol_from_market(market: Dict, chain: str = 'ethereum') -> Optional[str]:
    """Extract token symbol from market data (handles different adapter formats)."""
    # Try different field names used by various adapters
    symbol = (
        market.get('underlying_symbol') or
        market.get('token_symbol') or
        market.get('symbol') or
        market.get('asset_symbol')
    )
    # Handle native tokens — map to the correct native token per chain
    if symbol == 'NATIVE':
        return CHAIN_NATIVE_TOKENS.get(chain, 'ETH')
    return symbol


# Map chain names to their native token symbols for correct pricing
CHAIN_NATIVE_TOKENS = {
    'ethereum': 'ETH',
    'arbitrum': 'ETH',
    'optimism': 'ETH',
    'base': 'ETH',
    'linea': 'ETH',
    'scroll': 'ETH',
    'plasma': 'ETH',
    'binance': 'BNB',
    'avalanche': 'AVAX',
    'polygon': 'MATIC',
    'xdai': 'xDAI',
    'gnosis': 'xDAI',
    'cronos': 'CRO',
    'flare': 'FLR',
    'meter': 'MTR',
    'ink': 'ETH',
    'sonic': 'S',
    'core': 'CORE',
}


def get_token_decimals_from_market(market: Dict) -> int:
    """Extract token decimals from market data."""
    return (
        market.get('underlying_decimals') or
        market.get('token_decimals') or
        market.get('decimals') or
        18
    )


def get_supply_raw(market: Dict) -> int:
    """Extract raw supply amount from market data."""
    # Different adapters use different field names
    # Aave: supplied_raw
    # Compound V3: supplied_raw
    # Compound V2/Benqi: tvl_underlying_raw or (get_cash_raw + total_borrows_raw)
    # Fluid: total_supply_raw, total_assets_raw

    # Check for Aave/Compound V3 format first
    if 'supplied_raw' in market:
        return market['supplied_raw']

    # Check for Benqi/Compound V2 format (TVL = cash + borrows)
    if 'tvl_underlying_raw' in market:
        return market['tvl_underlying_raw']
    if 'get_cash_raw' in market:
        cash = market.get('get_cash_raw') or 0
        borrows = market.get('total_borrows_raw') or 0
        return cash + borrows

    # Fluid format
    if 'total_assets_raw' in market:
        return market['total_assets_raw']

    # Generic fallbacks
    return (
        market.get('total_supply_raw') or
        market.get('supply_raw') or
        market.get('totalSupply') or
        market.get('supply') or
        0
    )


def get_borrow_raw(market: Dict) -> int:
    """Extract raw borrow amount from market data."""
    # Aave: variable_debt_raw + stable_debt_raw
    # Compound V3: borrowed_raw
    # Compound V2/Benqi: total_borrows_raw
    # Fluid: total_borrow_raw

    # Aave format
    variable_debt = market.get('variable_debt_raw') or 0
    stable_debt = market.get('stable_debt_raw') or 0
    if variable_debt or stable_debt:
        return variable_debt + stable_debt

    # Compound V3 format
    if 'borrowed_raw' in market:
        return market['borrowed_raw']

    # Benqi/Compound V2 format
    if 'total_borrows_raw' in market:
        return market['total_borrows_raw']

    # Fluid format
    if 'total_borrow_raw' in market:
        return market['total_borrow_raw']

    # Generic fallbacks
    return (
        market.get('borrow_raw') or
        market.get('totalBorrow') or
        market.get('borrows') or
        0
    )


def process_bronze_file(
    bronze_file: Path,
    web3,
    chain: str = None,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Process a single bronze file into silver format.

    Returns aggregated TVL data or None if failed.

    Note: The `chain` parameter is now auto-detected from the bronze data
    so that Chainlink lookups and native token mapping use the correct chain.
    """
    try:
        with open(bronze_file) as f:
            bronze_data = json.load(f)
    except Exception as e:
        if verbose:
            print(f"  Error reading {bronze_file}: {e}")
        return None

    csu = bronze_data.get('csu')
    date_str = bronze_data.get('date')
    markets = bronze_data.get('data', [])

    # FIX: Use the chain from the bronze data itself instead of hardcoding 'ethereum'
    # This ensures Chainlink lookups and native token mapping are chain-correct
    actual_chain = bronze_data.get('chain', chain or 'ethereum')

    if not markets:
        return None

    # Aggregate across markets
    total_supply_usd = 0.0
    total_borrow_usd = 0.0
    market_count = 0
    missing_prices = []

    for market in markets:
        symbol = get_token_symbol_from_market(market, chain=actual_chain)
        if not symbol:
            continue

        decimals = get_token_decimals_from_market(market)
        supply_raw = get_supply_raw(market)
        borrow_raw = get_borrow_raw(market)

        # Get price (try cache first, then fetch)
        price = get_cached_price(symbol, date_str)
        if price is None:
            price = get_token_price(symbol, date_str, web3, chain=actual_chain)

        if price is None:
            missing_prices.append(symbol)
            continue

        # Convert to USD
        supply_usd = (supply_raw / 10**decimals) * price
        borrow_usd = (borrow_raw / 10**decimals) * price

        total_supply_usd += supply_usd
        total_borrow_usd += borrow_usd
        market_count += 1

    if verbose and missing_prices:
        print(f"  {csu}/{date_str}: Missing prices for {missing_prices}")

    return {
        'date': date_str,
        'csu': csu,
        'chain': actual_chain,
        'protocol': bronze_data.get('protocol'),
        'version': bronze_data.get('version'),
        'total_supply_usd': total_supply_usd,
        'total_borrow_usd': total_borrow_usd,
        'net_tvl_usd': total_supply_usd - total_borrow_usd,
        'num_markets': market_count,
        'block': bronze_data.get('block'),
    }


def collect_all_tokens(csu_dirs: List[Path], sample_size: int = 5) -> set:
    """Collect all unique token symbols from bronze data."""
    tokens = set()

    for csu_dir in csu_dirs:
        files = list(csu_dir.glob('*.json'))[:sample_size]
        for f in files:
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    for market in data.get('data', []):
                        symbol = get_token_symbol_from_market(market)
                        if symbol:
                            tokens.add(symbol)
            except:
                pass

    return tokens


def load_existing_silver() -> Dict[str, Dict]:
    """Load existing silver data indexed by (csu, date) for incremental updates."""
    existing = {}
    silver_json = SILVER_DIR / 'daily_tvl.json'

    if silver_json.exists():
        try:
            with open(silver_json) as f:
                records = json.load(f)
                for r in records:
                    key = (r.get('csu'), r.get('date'))
                    existing[key] = r
        except Exception:
            pass

    return existing


def main():
    parser = argparse.ArgumentParser(description='Build Silver Layer TVL Data')
    parser.add_argument('--csu', help='Process only this CSU')
    parser.add_argument('--date', help='Process only this date (YYYY-MM-DD)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    parser.add_argument('--force', action='store_true', help='Reprocess all files (ignore existing silver)')
    parser.add_argument('--clear-not-found', action='store_true',
                        help='Clear not-found cache before running (retry failed lookups)')
    parser.add_argument('--show-not-found', action='store_true',
                        help='Show tokens in not-found cache and exit')
    args = parser.parse_args()

    print("=" * 60)
    print("Building Silver Layer TVL Data")
    print("=" * 60)

    # Handle --show-not-found
    if args.show_not_found:
        not_found = get_not_found_tokens()
        print(f"\nTokens in not-found cache ({sum(not_found.values())} total entries):")
        for token, count in sorted(not_found.items(), key=lambda x: -x[1]):
            print(f"  {token}: {count} dates")
        return

    # Handle --clear-not-found
    if args.clear_not_found:
        print("\n[Pre-run] Clearing not-found cache...")
        cleared = clear_not_found()
        print(f"  Cleared {cleared} entries (will retry all failed lookups)")

    # Stage 1: Connect to RPC
    print("\n[Stage 1/5] Connecting to Ethereum RPC...")
    web3 = get_web3('ethereum')
    print(f"  Connected to Ethereum RPC (block {web3.eth.block_number:,})")

    # Stage 2: Find bronze files
    print("\n[Stage 2/5] Finding bronze data files...")
    csu_dirs = list(BRONZE_DIR.iterdir()) if BRONZE_DIR.exists() else []
    csu_dirs = [d for d in csu_dirs if d.is_dir()]

    if args.csu:
        csu_dirs = [d for d in csu_dirs if d.name == args.csu]

    if not csu_dirs:
        print("  No bronze data found!")
        return

    total_files = sum(len(list(d.glob('*.json'))) for d in csu_dirs)
    print(f"  Found {len(csu_dirs)} CSUs with {total_files} total files")

    # Stage 3: Collect tokens
    print("\n[Stage 3/5] Collecting unique tokens from bronze data...")
    all_tokens = collect_all_tokens(csu_dirs, sample_size=10)
    print(f"  Found {len(all_tokens)} unique tokens")
    if args.verbose:
        print(f"  Tokens: {sorted(all_tokens)}")

    # Stage 4: Check price cache status
    print("\n[Stage 4/5] Checking price cache...")
    cache_stats = get_cache_stats()
    print(f"  Cached prices: {cache_stats['total_prices']} entries")
    print(f"  Unique tokens: {cache_stats['unique_tokens']}")
    print(f"  Dates covered: {cache_stats['total_dates']}")
    print(f"  Not-found entries: {cache_stats['not_found_entries']}")

    # Stage 5: Process bronze files (incremental)
    print("\n[Stage 5/5] Processing bronze files to silver...")

    # Load existing silver data for incremental updates
    if args.force:
        existing_silver = {}
        print("  --force: Reprocessing all files")
    else:
        existing_silver = load_existing_silver()
        print(f"  Existing silver records: {len(existing_silver)}")

    silver_data = list(existing_silver.values())  # Start with existing data
    processed = 0
    skipped = 0
    errors = 0

    for csu_idx, csu_dir in enumerate(sorted(csu_dirs), 1):
        csu_name = csu_dir.name
        bronze_files = sorted(csu_dir.glob('*.json'))

        if args.date:
            bronze_files = [f for f in bronze_files if f.stem == args.date]

        # Filter out files we already have in silver (unless --force)
        # FIX: Initialize skipped_count before the conditional to avoid NameError
        skipped_count = 0
        if not args.force:
            new_files = []
            for f in bronze_files:
                date_str = f.stem  # filename is YYYY-MM-DD.json
                key = (csu_name, date_str)
                if key not in existing_silver:
                    new_files.append(f)
            skipped_count = len(bronze_files) - len(new_files)
            skipped += skipped_count
            bronze_files = new_files

        if not bronze_files:
            print(f"\n  [{csu_idx}/{len(csu_dirs)}] {csu_name}: 0 new files ({skipped_count} already in silver)")
            continue

        print(f"\n  [{csu_idx}/{len(csu_dirs)}] {csu_name}: {len(bronze_files)} new files")

        for file_idx, bronze_file in enumerate(bronze_files, 1):
            if args.dry_run:
                print(f"    Would process: {bronze_file.name}")
                continue

            result = process_bronze_file(
                bronze_file,
                web3,
                chain=None,  # FIX: auto-detect from bronze data (was hardcoded 'ethereum')
                verbose=args.verbose
            )

            if result:
                silver_data.append(result)
                processed += 1
            else:
                errors += 1

            # Progress update every 50 files or at end
            if file_idx % 50 == 0 or file_idx == len(bronze_files):
                print(f"    Processed {file_idx}/{len(bronze_files)} files "
                      f"(total: {processed} ok, {errors} err)")

        # Checkpoint save after each CSU (crash recovery)
        if not args.dry_run and processed > 0:
            save_price_cache()
            print(f"    [Checkpoint] Price cache saved")

    if args.dry_run:
        print(f"\nDry run complete. Would process {total_files} files.")
        return

    # Save price cache
    print("\n[Saving] Price cache...")
    save_price_cache()
    final_stats = get_cache_stats()
    print(f"  Price cache saved: {final_stats['total_prices']} entries")

    # Save silver data
    print("\n[Saving] Silver layer data...")
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    if silver_data:
        # Save as JSON (simple format)
        output_file = SILVER_DIR / 'daily_tvl.json'
        with open(output_file, 'w') as f:
            json.dump(silver_data, f, indent=2)
        print(f"  JSON: {output_file} ({len(silver_data)} records)")

        # Also save as CSV for easy viewing
        csv_file = SILVER_DIR / 'daily_tvl.csv'
        with open(csv_file, 'w') as f:
            if silver_data:
                headers = list(silver_data[0].keys())
                f.write(','.join(headers) + '\n')
                for row in silver_data:
                    values = [str(row.get(h, '')) for h in headers]
                    f.write(','.join(values) + '\n')
        print(f"  CSV:  {csv_file}")

    # === Data Validation ===
    print("\n[Validation] Running sanity checks on silver data...")
    warnings = []
    if silver_data:
        for r in silver_data:
            csu, date = r.get('csu'), r.get('date')
            supply = r.get('total_supply_usd', 0)
            borrow = r.get('total_borrow_usd', 0)
            net = r.get('net_tvl_usd', 0)

            # Check for negative values (should never happen)
            if supply < 0:
                warnings.append(f"  WARN: {csu}/{date}: negative supply ${supply:,.0f}")
            if borrow < 0:
                warnings.append(f"  WARN: {csu}/{date}: negative borrow ${borrow:,.0f}")

            # Check utilization > 100% (borrow > supply, possible but unusual)
            if supply > 0 and borrow > supply:
                util = borrow / supply
                if util > 1.5:  # Flag extreme cases only
                    warnings.append(f"  WARN: {csu}/{date}: utilization {util:.1%} (borrow > supply)")

            # Check for suspiciously large TVL (> $100B for a single CSU-day)
            if supply > 100e9:
                warnings.append(f"  WARN: {csu}/{date}: supply ${supply/1e9:,.1f}B seems too large")

            # Check for zero markets with nonzero TVL (data consistency)
            if r.get('num_markets', 0) == 0 and supply > 0:
                warnings.append(f"  WARN: {csu}/{date}: 0 markets but supply=${supply:,.0f}")

            # Check net_tvl_usd consistency
            expected_net = supply - borrow
            if abs(net - expected_net) > 1.0:  # Allow $1 floating-point tolerance
                warnings.append(f"  WARN: {csu}/{date}: net_tvl mismatch (got {net:,.0f}, expected {expected_net:,.0f})")

    if warnings:
        print(f"  Found {len(warnings)} warnings:")
        for w in warnings[:20]:  # Show first 20
            print(w)
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more warnings")
    else:
        print("  All checks passed ✓")

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Bronze files processed: {processed}")
    print(f"  Bronze files skipped (already in silver): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Silver records total: {len(silver_data)}")
    print(f"  Price cache entries: {final_stats['total_prices']}")
    print(f"  Validation warnings: {len(warnings)}")

    if silver_data:
        # Quick stats
        total_supply = sum(r['total_supply_usd'] for r in silver_data)
        total_borrow = sum(r['total_borrow_usd'] for r in silver_data)
        print(f"\n  Total Supply (all CSUs, all dates): ${total_supply/1e9:,.2f}B")
        print(f"  Total Borrow (all CSUs, all dates): ${total_borrow/1e9:,.2f}B")


if __name__ == '__main__':
    main()
