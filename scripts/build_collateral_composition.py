#!/usr/bin/env python3
"""
Build Collateral Composition Data

Extracts daily collateral composition (% breakdown by token) from bronze TVL data.
Creates one file per CSU with daily collateral weights.

This is used to construct collateral baskets for volatility analysis:
"Do liquidations drive collateral asset volatility?"

Output schema per CSU:
- date: Date
- symbol: Token symbol
- supplied_amount: Human-readable token amount supplied
- supplied_usd: USD value of supplied amount
- pct_of_total: Percentage of total collateral (0-100)

Usage:
    python scripts/build_collateral_composition.py --chain ethereum
    python scripts/build_collateral_composition.py --csu aave_v3_ethereum
    python scripts/build_collateral_composition.py --chain ethereum --fetch-prices
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
from typing import Dict, List, Optional

import pandas as pd

# Chainlink price adapter
try:
    from adapters.prices.chainlink import get_token_price_chainlink, get_stablecoins
    from config.rpc_pool import get_web3
    HAS_CHAINLINK = True
except ImportError:
    HAS_CHAINLINK = False
    def get_stablecoins():
        return ['USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'GHO', 'sUSD', 'PYUSD', 'USDS', 'crvUSD']

BRONZE_TVL_DIR = Path('data/bronze/tvl')
OUTPUT_DIR = Path('data/gold/collateral_composition')
REFERENCE_DIR = Path('data/reference')

# CSUs in our gold liquidation panel
ETHEREUM_CSUS = [
    'aave_v3_ethereum',
    'compound_v3_eth_usdc',
    'compound_v3_eth_usdt',
    'compound_v3_eth_usds',
    'compound_v3_eth_weth',
    'sparklend_ethereum',
]


def load_price_cache(chain: str) -> Dict[str, float]:
    """Load existing price cache from silver pipeline."""
    cache_file = REFERENCE_DIR / f"price_cache_{chain}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return {}


def save_price_cache(chain: str, cache: Dict[str, float]):
    """Save price cache."""
    cache_file = REFERENCE_DIR / f"price_cache_{chain}.json"
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)


def get_price_from_cache(symbol: str, date: str, price_cache: Dict[str, float]) -> Optional[float]:
    """Get price from cache only."""
    if not symbol or symbol == 'UNKNOWN':
        return None

    cache_key = f"{date}_{symbol}"

    if cache_key in price_cache:
        return price_cache[cache_key]

    # Check stablecoins
    stablecoins = get_stablecoins()
    if symbol in stablecoins or symbol.upper() in stablecoins:
        return 1.0

    return None


def fetch_price_chainlink(w3, symbol: str, date: str, block: int, price_cache: Dict[str, float]) -> Optional[float]:
    """Fetch price from Chainlink and cache it."""
    if not symbol or symbol == 'UNKNOWN' or not HAS_CHAINLINK:
        return None

    cache_key = f"{date}_{symbol}"

    if cache_key in price_cache:
        return price_cache[cache_key]

    # Check stablecoins
    stablecoins = get_stablecoins()
    if symbol in stablecoins or symbol.upper() in stablecoins:
        price_cache[cache_key] = 1.0
        return 1.0

    # Fetch from Chainlink
    price = get_token_price_chainlink(w3, symbol, chain='ethereum', block=block)
    if price is not None:
        price_cache[cache_key] = price

    return price


def load_bronze_tvl_for_csu(csu: str) -> List[dict]:
    """Load all bronze TVL snapshots for a CSU."""
    csu_dir = BRONZE_TVL_DIR / csu
    if not csu_dir.exists():
        return []

    snapshots = []
    for json_file in sorted(csu_dir.glob('*.json')):
        try:
            with open(json_file) as f:
                data = json.load(f)
                snapshots.append(data)
        except:
            continue

    return snapshots


def process_csu_composition(csu: str, price_cache: Dict[str, float], w3=None, fetch_missing: bool = False) -> pd.DataFrame:
    """Process collateral composition for a single CSU."""
    snapshots = load_bronze_tvl_for_csu(csu)

    if not snapshots:
        print(f"  No bronze TVL data found for {csu}")
        return pd.DataFrame()

    print(f"  Processing {len(snapshots)} snapshots...", flush=True)

    rows = []
    missing_prices = set()

    for i, snapshot in enumerate(snapshots):
        date = snapshot.get('date')
        block = snapshot.get('block')
        markets = snapshot.get('data', [])

        if not date or not markets:
            continue

        # Calculate USD values for each market
        market_values = []

        for market in markets:
            symbol = market.get('symbol', 'UNKNOWN')
            decimals = market.get('decimals', 18)
            supplied_raw = market.get('supplied_raw', 0)

            if supplied_raw == 0:
                continue

            # Convert to human-readable amount
            supplied_amount = supplied_raw / (10 ** decimals)

            # Get USD price (cache first, then Chainlink if requested)
            price = get_price_from_cache(symbol, date, price_cache)

            if price is None and fetch_missing and w3:
                price = fetch_price_chainlink(w3, symbol, date, block, price_cache)

            if price is None:
                missing_prices.add(symbol)

            supplied_usd = supplied_amount * price if price else None

            market_values.append({
                'date': date,
                'symbol': symbol,
                'underlying': market.get('underlying'),
                'supplied_amount': supplied_amount,
                'supplied_usd': supplied_usd,
            })

        # Calculate percentages based on USD values
        total_usd = sum(m['supplied_usd'] for m in market_values if m['supplied_usd'])

        for m in market_values:
            if m['supplied_usd'] and total_usd > 0:
                m['pct_of_total'] = (m['supplied_usd'] / total_usd) * 100
            else:
                m['pct_of_total'] = None

            rows.append(m)

        # Progress
        if (i + 1) % 100 == 0:
            print(f"    {i + 1}/{len(snapshots)} snapshots processed", flush=True)

    if missing_prices:
        print(f"  Missing prices for: {', '.join(sorted(missing_prices)[:10])}{'...' if len(missing_prices) > 10 else ''}")

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description='Build collateral composition data')
    parser.add_argument('--chain', default='ethereum', help='Chain to process')
    parser.add_argument('--csu', help='Specific CSU to process')
    parser.add_argument('--fetch-prices', action='store_true', help='Fetch missing prices from Chainlink')

    args = parser.parse_args()
    chain = args.chain

    print("=" * 70)
    print("Building Collateral Composition Data")
    print("=" * 70)

    # Determine CSUs to process
    if args.csu:
        csus = [args.csu]
    elif chain == 'ethereum':
        csus = ETHEREUM_CSUS
    else:
        print(f"Error: Please specify --csu or use --chain ethereum")
        return

    print(f"\nCSUs to process: {len(csus)}")
    for csu in csus:
        print(f"  - {csu}")

    # Load price cache
    price_cache = load_price_cache(chain)
    print(f"\nLoaded {len(price_cache)} cached prices")

    # Get web3 if fetching prices
    w3 = None
    if args.fetch_prices and HAS_CHAINLINK:
        try:
            w3 = get_web3(chain)
            print(f"Connected to {chain} for price lookups")
        except Exception as e:
            print(f"Warning: Could not connect to {chain}: {e}")

    # Process each CSU
    output_dir = OUTPUT_DIR / chain
    output_dir.mkdir(parents=True, exist_ok=True)

    for csu in csus:
        print(f"\n{csu}:")
        df = process_csu_composition(csu, price_cache, w3, fetch_missing=args.fetch_prices)

        if df.empty:
            print(f"  Skipped (no data)")
            continue

        # Add CSU column
        df['csu'] = csu

        # Reorder columns
        cols = ['date', 'csu', 'symbol', 'underlying', 'supplied_amount', 'supplied_usd', 'pct_of_total']
        df = df[[c for c in cols if c in df.columns]]

        # Save
        csu_file = output_dir / f"{csu}.parquet"
        df.to_parquet(csu_file, index=False)

        # Stats
        n_dates = df['date'].nunique()
        n_tokens = df['symbol'].nunique()
        usd_coverage = df['supplied_usd'].notna().mean() * 100
        print(f"  Saved: {len(df)} rows, {n_dates} dates, {n_tokens} tokens, {usd_coverage:.1f}% USD coverage")

    # Save updated price cache
    if args.fetch_prices:
        save_price_cache(chain, price_cache)
        print(f"\nSaved {len(price_cache)} prices to cache")

    # Create summary file
    print("\n" + "=" * 70)
    print("Creating combined summary...")

    all_data = []
    for csu in csus:
        csu_file = output_dir / f"{csu}.parquet"
        if csu_file.exists():
            all_data.append(pd.read_parquet(csu_file))

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined_file = output_dir / "all_csus_composition.parquet"
        combined.to_parquet(combined_file, index=False)
        print(f"Combined file: {combined_file}")
        print(f"Total rows: {len(combined):,}")

    print("\nCollateral composition complete!")


if __name__ == '__main__':
    main()
