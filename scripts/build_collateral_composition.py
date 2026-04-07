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
    python scripts/build_collateral_composition.py --all
    python scripts/build_collateral_composition.py --chain ethereum
    python scripts/build_collateral_composition.py --csu aave_v3_ethereum
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
from typing import Dict, List, Optional

import pandas as pd

BRONZE_TVL_DIR = Path('data/bronze/tvl')
OUTPUT_DIR = Path('data/gold/collateral_composition')
REFERENCE_DIR = Path('data/reference')
CACHE_DIR = Path('data/cache/prices')

STABLECOINS = {
    'USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'GHO', 'sUSD', 'PYUSD', 'USDS',
    'crvUSD', 'USDbC', 'USDBC', 'USDC.e', 'DAI.e', 'GUSD', 'TUSD', 'BUSD',
    'USDP', 'FDUSD', 'USD0', 'AUSD', 'RLUSD', 'USDG', 'mUSD', 'syrupUSDT',
    'WXDAI', 'SUSD', 'MUSD', 'USDe', 'sUSDe',
}

# Chain detection from CSU name
CHAIN_KEYWORDS = [
    'ethereum', 'arbitrum', 'optimism', 'polygon', 'avalanche',
    'base', 'binance', 'gnosis', 'linea', 'scroll', 'ink',
    'sonic', 'celo', 'fantom', 'blast', 'zksync', 'meter',
]
CHAIN_ALIASES = {
    'eth': 'ethereum', 'arb': 'arbitrum', 'op': 'optimism',
    'bsc': 'binance', 'xdai': 'gnosis', 'poly': 'polygon',
}


def detect_chain(csu: str) -> str:
    """Detect chain from CSU name."""
    lower = csu.lower()
    for chain in CHAIN_KEYWORDS:
        if chain in lower:
            return chain
    for alias, chain in CHAIN_ALIASES.items():
        if f'_{alias}_' in f'_{lower}_':
            return chain
    return 'unknown'


def load_all_price_caches() -> Dict[str, float]:
    """Load all available price caches (reference + oracle + daily)."""
    cache = {}
    # Reference price caches
    for f in REFERENCE_DIR.glob('price_cache_*.json'):
        try:
            with open(f) as fh:
                cache.update(json.load(fh))
        except Exception:
            continue
    # Daily prices
    daily = CACHE_DIR / 'daily_prices.json'
    if daily.exists():
        try:
            with open(daily) as fh:
                cache.update(json.load(fh))
        except Exception:
            pass
    return cache


def load_oracle_price_cache() -> Dict[str, float]:
    """Load protocol oracle price cache (chain:addr:date -> price)."""
    path = CACHE_DIR / 'protocol_oracle_prices.json'
    if path.exists():
        try:
            with open(path) as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}


def get_price(symbol: str, date: str, token_addr: str, chain: str,
              price_cache: Dict[str, float], oracle_cache: Dict[str, float]) -> Optional[float]:
    """Get price from any available source."""
    if not symbol or symbol == 'UNKNOWN':
        return None

    # Stablecoins
    if symbol in STABLECOINS or symbol.upper() in STABLECOINS:
        return 1.0

    # Oracle cache (address-based, most reliable)
    if token_addr and oracle_cache:
        oracle_key = f"{chain}:{token_addr.lower()}:{date}"
        price = oracle_cache.get(oracle_key)
        if price is not None and price > 0:
            return price

    # Symbol-based cache
    cache_key = f"{date}_{symbol}"
    if cache_key in price_cache:
        return price_cache[cache_key]

    # Try uppercase
    cache_key_upper = f"{date}_{symbol.upper()}"
    if cache_key_upper in price_cache:
        return price_cache[cache_key_upper]

    return None


def _get_symbol(market: dict, chain: str = '') -> str:
    """Extract underlying token symbol from any bronze TVL schema."""
    sym = (
        market.get('underlying_symbol') or
        market.get('token_symbol') or
        market.get('symbol') or
        market.get('asset_symbol') or
        'UNKNOWN'
    )
    native_map = {
        'ethereum': 'ETH', 'arbitrum': 'ETH', 'optimism': 'ETH',
        'base': 'ETH', 'linea': 'ETH', 'scroll': 'ETH', 'ink': 'ETH',
        'gnosis': 'WXDAI', 'polygon': 'MATIC', 'avalanche': 'AVAX',
        'binance': 'BNB', 'meter': 'MTR', 'sonic': 'S', 'fantom': 'FTM',
    }
    if sym == 'NATIVE':
        return native_map.get(chain, 'ETH')
    return sym


def _get_supply_raw(market: dict) -> int:
    """Extract raw supply amount from any bronze TVL schema."""
    if 'supplied_raw' in market:
        return market['supplied_raw']
    if 'tvl_underlying_raw' in market:
        return market['tvl_underlying_raw']
    if 'get_cash_raw' in market:
        cash = market.get('get_cash_raw') or 0
        borrows = market.get('total_borrows_raw') or 0
        return cash + borrows
    if 'total_assets_raw' in market:
        return market['total_assets_raw']
    return market.get('total_supply_raw') or 0


def _get_decimals(market: dict) -> int:
    """Extract token decimals from any bronze TVL schema."""
    return (
        market.get('underlying_decimals') or
        market.get('token_decimals') or
        market.get('decimals') or
        18
    )


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


def process_csu_composition(csu: str, chain: str,
                            price_cache: Dict[str, float],
                            oracle_cache: Dict[str, float]) -> pd.DataFrame:
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
        snap_chain = snapshot.get('chain', chain)
        markets = snapshot.get('data', [])

        if not date or not markets:
            continue

        market_values = []

        for market in markets:
            symbol = _get_symbol(market, snap_chain)
            decimals = _get_decimals(market)
            supplied_raw = _get_supply_raw(market)

            if supplied_raw == 0:
                continue

            supplied_amount = supplied_raw / (10 ** decimals)

            # Get token address for oracle lookup
            token_addr = (market.get('underlying_address') or
                         market.get('underlying') or
                         market.get('token_address') or
                         market.get('address') or '')

            price = get_price(symbol, date, token_addr, snap_chain,
                            price_cache, oracle_cache)

            if price is None:
                missing_prices.add(symbol)

            supplied_usd = supplied_amount * price if price else None

            market_values.append({
                'date': date,
                'symbol': symbol,
                'underlying': token_addr,
                'supplied_amount': supplied_amount,
                'supplied_usd': supplied_usd,
            })

        total_usd = sum(m['supplied_usd'] for m in market_values if m['supplied_usd'])

        for m in market_values:
            if m['supplied_usd'] and total_usd > 0:
                m['pct_of_total'] = (m['supplied_usd'] / total_usd) * 100
            else:
                m['pct_of_total'] = None
            rows.append(m)

        if (i + 1) % 200 == 0:
            print(f"    {i + 1}/{len(snapshots)} snapshots processed", flush=True)

    if missing_prices:
        print(f"  Missing prices for: {', '.join(sorted(missing_prices)[:10])}{'...' if len(missing_prices) > 10 else ''}")

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def discover_all_csus() -> List[str]:
    """Discover all CSUs with bronze TVL data."""
    csus = []
    for d in sorted(BRONZE_TVL_DIR.iterdir()):
        if d.is_dir() and list(d.glob('*.json')):
            csus.append(d.name)
    return csus


def main():
    parser = argparse.ArgumentParser(description='Build collateral composition data')
    parser.add_argument('--all', action='store_true', help='Process ALL CSUs from bronze TVL')
    parser.add_argument('--chain', help='Only process CSUs on this chain')
    parser.add_argument('--csu', help='Specific CSU to process')

    args = parser.parse_args()

    print("=" * 70)
    print("Building Collateral Composition Data")
    print("=" * 70)

    # Determine CSUs to process
    if args.csu:
        csus = [args.csu]
    elif args.all:
        csus = discover_all_csus()
    elif args.chain:
        all_csus = discover_all_csus()
        csus = [c for c in all_csus if detect_chain(c) == args.chain]
    else:
        csus = discover_all_csus()

    if not csus:
        print("No CSUs found to process!")
        return

    # Group by chain for display
    chain_groups = {}
    for csu in csus:
        chain = detect_chain(csu)
        chain_groups.setdefault(chain, []).append(csu)

    print(f"\nCSUs to process: {len(csus)} across {len(chain_groups)} chains")
    for chain, chain_csus in sorted(chain_groups.items()):
        print(f"  {chain}: {len(chain_csus)} CSUs")

    # Load all price caches
    print("\nLoading price caches...")
    price_cache = load_all_price_caches()
    print(f"  Symbol-based prices: {len(price_cache):,}")
    oracle_cache = load_oracle_price_cache()
    print(f"  Protocol oracle prices: {len(oracle_cache):,}")

    # Process each CSU
    all_dfs = []
    for csu in csus:
        chain = detect_chain(csu)
        output_dir = OUTPUT_DIR / chain
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{csu} ({chain}):")
        df = process_csu_composition(csu, chain, price_cache, oracle_cache)

        if df.empty:
            print(f"  Skipped (no data)")
            continue

        df['csu'] = csu

        cols = ['date', 'csu', 'symbol', 'underlying', 'supplied_amount', 'supplied_usd', 'pct_of_total']
        df = df[[c for c in cols if c in df.columns]]

        # Save per-CSU
        csu_file = output_dir / f"{csu}.parquet"
        df.to_parquet(csu_file, index=False)

        n_dates = df['date'].nunique()
        n_tokens = df['symbol'].nunique()
        usd_coverage = df['supplied_usd'].notna().mean() * 100
        print(f"  {len(df):,} rows, {n_dates} dates, {n_tokens} tokens, {usd_coverage:.1f}% USD coverage")

        all_dfs.append(df)

    # Create combined file
    print("\n" + "=" * 70)
    print("Creating combined composition file...")

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined_file = OUTPUT_DIR / "all_chains_composition.parquet"
        combined.to_parquet(combined_file, index=False)
        print(f"  Output: {combined_file}")
        print(f"  Total rows: {len(combined):,}")
        print(f"  CSUs: {combined['csu'].nunique()}")
        print(f"  USD coverage: {combined['supplied_usd'].notna().mean()*100:.1f}%")

        # Per-chain summary
        print(f"\n  Per-chain USD coverage:")
        for csu in sorted(combined['csu'].unique()):
            csu_data = combined[combined['csu'] == csu]
            pct = csu_data['supplied_usd'].notna().mean() * 100
            print(f"    {csu:<45} {pct:5.1f}%")

    print("\nCollateral composition complete!")


if __name__ == '__main__':
    main()
