#!/usr/bin/env python3
"""
Build Utilization + Volatility Panel for ALL CSUs with bronze TVL data.

Pipeline:
1. Scan all bronze TVL to find unique tokens per CSU
2. Batch-fetch missing prices from DefiLlama
3. Compute collateral composition (weights) from bronze TVL + prices
4. Compute basket returns and rolling volatility
5. Merge with utilization from silver TVL
6. Output balanced panel for Panel VAR

Usage:
    python3 scripts/build_volatility_panel.py
    python3 scripts/build_volatility_panel.py --window 14
    python3 scripts/build_volatility_panel.py --skip-fetch  # skip price fetching
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import time
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime

from adapters.prices.defillama import (
    get_defillama_id, batch_get_historical_prices, STABLECOINS as DL_STABLECOINS
)

BRONZE_TVL_DIR = Path('data/bronze/tvl')
PRICE_CACHE_DIR = Path('data/reference')
OUTPUT_DIR = Path('data/analysis')

# Stablecoins we assume = $1.00
STABLECOINS = {
    'USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'GHO', 'sUSD', 'PYUSD', 'USDS',
    'crvUSD', 'USDbC', 'USDBC', 'USDC.e', 'DAI.e', 'GUSD', 'TUSD', 'BUSD',
    'USDP', 'FDUSD', 'USD0', 'AUSD', 'RLUSD', 'USDG', 'mUSD', 'syrupUSDT',
    'WXDAI', 'SUSD', 'MUSD',
}

# Skip tokens we can't price (PT tokens, UNKNOWN, etc.)
SKIP_TOKENS = {'UNKNOWN', 'PT-', 'deUSD', 'sdeUSD', 'eUSDe', 'wUSDM', 'sFRAX', 'sUSDS'}

# Native token mapping per chain
NATIVE_TOKEN = {
    'ethereum': 'ETH',
    'arbitrum': 'ETH',
    'optimism': 'ETH',
    'base': 'ETH',
    'linea': 'ETH',
    'scroll': 'ETH',
    'xdai': 'WXDAI',
    'polygon': 'MATIC',
    'avalanche': 'AVAX',
    'binance': 'BNB',
    'meter': 'MTR',
    'ink': 'ETH',
    'flare': 'FLR',
    'cronos': 'CRO',
}


def _get_symbol(market: dict, chain: str = '') -> str:
    """Extract underlying token symbol from any bronze TVL schema."""
    sym = (
        market.get('underlying_symbol') or
        market.get('token_symbol') or
        market.get('symbol') or
        market.get('asset_symbol') or
        market.get('loan_symbol') or        # Morpho Blue
        'UNKNOWN'
    )
    if sym == 'NATIVE':
        return NATIVE_TOKEN.get(chain, 'ETH')
    # Strip bridge suffixes like ".eth", ".bsc" (Meter/Sumer uses these)
    if '.' in sym and sym.rsplit('.', 1)[-1] in ('eth', 'bsc', 'matic'):
        sym = sym.rsplit('.', 1)[0]
    return sym


def _get_decimals(market: dict) -> int:
    """Extract token decimals from any bronze TVL schema."""
    return (
        market.get('underlying_decimals') or
        market.get('token_decimals') or
        market.get('decimals') or
        market.get('loan_decimals') or        # Morpho Blue
        18
    )


def _get_supply_raw(market: dict) -> int:
    """Extract raw supply amount from any bronze TVL schema."""
    # Aave / Compound V3
    if 'supplied_raw' in market:
        return market['supplied_raw']
    # Compound V2 / Benqi / Moonwell / Venus / Sumermoney
    if 'tvl_underlying_raw' in market:
        return market['tvl_underlying_raw']
    if 'get_cash_raw' in market:
        cash = market.get('get_cash_raw') or 0
        borrows = market.get('total_borrows_raw') or 0
        return cash + borrows
    # Fluid / Gearbox
    if 'total_assets_raw' in market:
        return market['total_assets_raw']
    # Morpho Blue
    if 'total_supply_assets_raw' in market:
        return market['total_supply_assets_raw']
    return market.get('total_supply_raw') or 0


def _get_borrow_raw(market: dict) -> int:
    """Extract raw borrow amount from any bronze TVL schema."""
    # Aave: variable_debt_raw + stable_debt_raw
    variable_debt = market.get('variable_debt_raw') or 0
    stable_debt = market.get('stable_debt_raw') or 0
    if variable_debt or stable_debt:
        return variable_debt + stable_debt
    # Compound V3
    if 'borrowed_raw' in market:
        return market['borrowed_raw']
    # Compound V2 / Benqi / Venus / Sonne / Mendi / Moonwell
    if 'total_borrows_raw' in market:
        return market['total_borrows_raw']
    # Fluid / Gearbox
    if 'total_borrow_raw' in market:
        return market['total_borrow_raw']
    # Morpho Blue
    return market.get('total_borrow_assets_raw') or 0


def load_price_cache() -> dict:
    """Load unified price cache (symbol-keyed)."""
    cache = {}
    for f in PRICE_CACHE_DIR.glob('price_cache_*.json'):
        with open(f) as fh:
            cache.update(json.load(fh))
    # Also load the daily cache
    daily = Path('data/cache/prices/daily_prices.json')
    if daily.exists():
        with open(daily) as fh:
            cache.update(json.load(fh))
    return cache


def load_oracle_price_cache() -> dict:
    """Load protocol oracle price cache (address-keyed: chain:addr:date)."""
    path = Path('data/cache/prices/protocol_oracle_prices.json')
    if path.exists():
        with open(path) as fh:
            return json.load(fh)
    return {}


CHAIN_ALIASES = {'xdai': 'gnosis', 'bsc': 'binance'}


def _normalize_chain(chain: str) -> str:
    """Normalize chain names (xdai->gnosis, bsc->binance)."""
    return CHAIN_ALIASES.get(chain.lower(), chain.lower())


def _get_chain_from_csu(csu: str) -> str:
    """Parse chain from CSU name."""
    for chain in ['ethereum', 'arbitrum', 'optimism', 'polygon', 'avalanche',
                  'binance', 'gnosis', 'linea', 'scroll', 'ink', 'base',
                  'sonic', 'celo', 'fantom', 'zksync', 'meter', 'blast']:
        if chain in csu.lower():
            return chain
    aliases = {'eth': 'ethereum', 'arb': 'arbitrum', 'op': 'optimism',
               'bsc': 'binance', 'xdai': 'gnosis'}
    for part in csu.lower().split('_'):
        if part in aliases:
            return aliases[part]
    return 'unknown'


def save_price_cache(cache: dict):
    """Save to a unified price cache file."""
    out = PRICE_CACHE_DIR / 'price_cache_all.json'
    PRICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(out, 'w') as f:
        json.dump(cache, f)
    print(f"  Saved {len(cache):,} prices to {out}")


def scan_all_bronze_tvl():
    """Scan all bronze TVL data to find (date, token) pairs needed."""
    print("Scanning bronze TVL data...")
    csu_dirs = sorted(BRONZE_TVL_DIR.iterdir())

    # Collect: {csu: [{date, markets: [{symbol, decimals, supplied_raw, ...}]}]}
    all_snapshots = {}
    all_date_tokens = set()  # (date, symbol) pairs needing prices

    for csu_dir in csu_dirs:
        if not csu_dir.is_dir():
            continue
        csu = csu_dir.name
        json_files = sorted(csu_dir.glob('*.json'))
        if not json_files:
            continue

        snapshots = []
        for jf in json_files:
            try:
                with open(jf) as f:
                    data = json.load(f)
                date = data.get('date')
                chain = data.get('chain', '')
                markets = data.get('data', [])
                if not date or not markets:
                    continue
                snapshots.append(data)
                for m in markets:
                    sym = _get_symbol(m, chain)
                    if sym.upper() in STABLECOINS or sym in STABLECOINS:
                        continue
                    if any(sym.startswith(skip) for skip in SKIP_TOKENS) or sym in SKIP_TOKENS:
                        continue
                    if _get_supply_raw(m) > 0:
                        all_date_tokens.add((date, sym))
            except:
                continue

        all_snapshots[csu] = snapshots
        print(f"  {csu}: {len(snapshots)} snapshots")

    print(f"  Total CSUs: {len(all_snapshots)}")
    print(f"  Total (date, token) pairs needing prices: {len(all_date_tokens):,}")
    return all_snapshots, all_date_tokens


def fetch_missing_prices(date_tokens: set, cache: dict) -> dict:
    """Batch-fetch missing prices from DefiLlama."""
    # Find what's missing
    missing = []
    for date, sym in date_tokens:
        cache_key = f"{date}_{sym}"
        if cache_key not in cache:
            missing.append((date, sym))

    if not missing:
        print("  No missing prices!")
        return cache

    # Group by date for efficient batch fetching
    by_date = defaultdict(set)
    for date, sym in missing:
        dl_id = get_defillama_id(sym)
        if dl_id:
            by_date[date].add((sym, dl_id))

    unique_tokens = set(sym for _, sym in missing)
    print(f"  Missing: {len(missing):,} (date,token) pairs for {len(unique_tokens)} unique tokens across {len(by_date)} dates")

    # Batch fetch by date
    fetched = 0
    failed_tokens = set()
    dates_sorted = sorted(by_date.keys())

    for i, date in enumerate(dates_sorted):
        tokens = list(by_date[date])
        # Batch in groups of 30
        for batch_start in range(0, len(tokens), 30):
            batch = tokens[batch_start:batch_start + 30]
            dl_ids = [dl_id for _, dl_id in batch]
            sym_map = {dl_id: sym for sym, dl_id in batch}

            try:
                prices = batch_get_historical_prices(dl_ids, date)
                for dl_id, price in prices.items():
                    sym = sym_map.get(dl_id)
                    if sym and price is not None:
                        cache[f"{date}_{sym}"] = price
                        fetched += 1
                    elif sym:
                        failed_tokens.add(sym)
            except Exception as e:
                print(f"    Error on {date}: {e}")

        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{len(dates_sorted)} dates processed, {fetched:,} prices fetched...")

    print(f"  Fetched {fetched:,} new prices")
    if failed_tokens:
        print(f"  Could not price: {sorted(failed_tokens)[:15]}{'...' if len(failed_tokens) > 15 else ''}")

    return cache


def _lookup_price_bvp(chain: str, token_addr: str, sym: str, date: str,
                      cache: dict, oracle_cache: dict) -> float:
    """Look up price: oracle cache (address-keyed) first, then symbol cache."""
    # 1. Protocol oracle cache (by address)
    if token_addr and oracle_cache:
        oracle_key = f"{chain}:{token_addr.lower()}:{date}"
        price = oracle_cache.get(oracle_key)
        if price is not None and price > 0:
            return price

    # 2. Symbol-based cache
    price = cache.get(f"{date}_{sym}")
    if price is not None and price > 0:
        return price

    # 3. Try uppercase symbol
    price = cache.get(f"{date}_{sym.upper()}")
    if price is not None and price > 0:
        return price

    # 4. Stablecoin assumption
    if sym.upper() in STABLECOINS or sym in STABLECOINS:
        return 1.0

    return None


def build_composition_and_volatility(all_snapshots: dict, cache: dict,
                                      window: int = 14,
                                      oracle_cache: dict = None) -> pd.DataFrame:
    """
    From bronze TVL + prices, compute:
    - collateral weights per CSU per date
    - basket returns
    - rolling volatility
    - utilization (borrowed / supplied) directly from bronze data

    Uses protocol oracle prices (by token address) as primary price source,
    with the symbol-based cache as fallback.
    """
    if oracle_cache is None:
        oracle_cache = {}

    print(f"\nBuilding collateral composition and {window}-day volatility...")
    if oracle_cache:
        print(f"  Using {len(oracle_cache):,} protocol oracle prices (address-keyed)")

    all_results = []

    for csu, snapshots in sorted(all_snapshots.items()):
        if not snapshots:
            continue

        chain = _get_chain_from_csu(csu)

        # Step 1: Compute daily basket returns and utilization
        # Need: weights from t-1, returns from t
        # Store token addresses alongside symbols for oracle lookups
        daily_data = {}  # date -> {symbol: weight}
        daily_addrs = {}  # date -> {symbol: token_address}
        daily_util = {}   # date -> utilization ratio

        for snap in snapshots:
            date = snap['date']
            snap_chain = _normalize_chain(snap.get('chain', chain))
            markets = snap.get('data', [])

            token_usd = {}
            token_addrs = {}
            total_supply_usd = 0.0
            total_borrow_usd = 0.0

            for m in markets:
                sym = _get_symbol(m, snap_chain)
                dec = _get_decimals(m)
                supply_raw = _get_supply_raw(m)
                borrow_raw = _get_borrow_raw(m)

                if supply_raw == 0 and borrow_raw == 0:
                    continue

                # Get token address for oracle lookup
                addr = (m.get('underlying') or
                        m.get('underlying_address') or
                        m.get('token_address') or
                        m.get('loan_token') or
                        m.get('collateral_token') or
                        m.get('address') or '')

                # Get price using oracle cache first, then symbol cache
                price = _lookup_price_bvp(
                    snap_chain, addr, sym, date, cache, oracle_cache)

                if price is None:
                    continue

                human_supply = supply_raw / (10 ** dec)
                human_borrow = borrow_raw / (10 ** dec)

                supply_usd = human_supply * price
                borrow_usd = human_borrow * price

                total_supply_usd += supply_usd
                total_borrow_usd += borrow_usd

                if supply_usd > 0:
                    token_usd[sym] = supply_usd
                    if addr:
                        token_addrs[sym] = addr

            total_usd = sum(token_usd.values())
            if total_usd > 0:
                weights = {sym: val / total_usd for sym, val in token_usd.items()}
                daily_data[date] = weights
                daily_addrs[date] = token_addrs

            # Compute utilization for this date
            if total_supply_usd > 0:
                util = total_borrow_usd / total_supply_usd
                daily_util[date] = min(max(util, 0.0), 1.0)  # Clip to [0, 1]

        dates = sorted(daily_data.keys())
        if len(dates) < window + 1:
            continue

        # Step 2: Compute basket returns
        basket_returns = []
        for i in range(1, len(dates)):
            date = dates[i]
            prev_date = dates[i - 1]

            prev_weights = daily_data.get(prev_date, {})
            if not prev_weights:
                continue

            basket_ret = 0.0
            total_w = 0.0

            for sym, w in prev_weights.items():
                # Get token address for oracle lookup
                addr = daily_addrs.get(prev_date, {}).get(sym, '')

                p_today = _lookup_price_bvp(
                    chain, addr, sym, date, cache, oracle_cache)
                p_prev = _lookup_price_bvp(
                    chain, addr, sym, prev_date, cache, oracle_cache)

                if p_today and p_prev and p_today > 0 and p_prev > 0:
                    log_ret = np.log(p_today) - np.log(p_prev)
                    # Skip token if return implies bad oracle price
                    # (|log_ret| > 2.0 ≈ >7x move, catches exchange-rate oracle errors)
                    if abs(log_ret) > 2.0:
                        continue
                    basket_ret += w * log_ret
                    total_w += w

            if total_w > 0.3:  # At least 30% weight coverage
                basket_returns.append({'date': date, 'basket_return': basket_ret})

        if len(basket_returns) < window:
            continue

        # Step 3: Rolling volatility
        br_df = pd.DataFrame(basket_returns)
        br_df = br_df.sort_values('date')
        br_df['volatility'] = br_df['basket_return'].rolling(
            window=window, min_periods=window // 2
        ).std()
        br_df['csu'] = csu

        # Step 4: Merge utilization onto volatility dates
        br_df['utilization'] = br_df['date'].map(daily_util)

        all_results.append(br_df[['date', 'csu', 'basket_return', 'volatility', 'utilization']])

        vol_coverage = br_df['volatility'].notna().mean() * 100
        util_coverage = br_df['utilization'].notna().mean() * 100
        print(f"  {csu}: {len(br_df)} days, {vol_coverage:.0f}% volatility coverage, {util_coverage:.0f}% utilization coverage")

    if not all_results:
        return pd.DataFrame()

    return pd.concat(all_results, ignore_index=True)


def build_panel(vol_df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Build final panel from volatility + utilization (both from bronze data)."""
    print("\nBuilding final panel...")

    # Utilization is already computed alongside volatility from bronze data
    panel = vol_df[['date', 'csu', 'basket_return', 'volatility', 'utilization']].copy()
    panel = panel.sort_values(['csu', 'date']).reset_index(drop=True)

    # Drop CSUs with poor coverage
    good_csus = []
    for csu in sorted(panel['csu'].unique()):
        cd = panel[panel['csu'] == csu]
        vol_pct = cd['volatility'].notna().mean()
        util_pct = cd['utilization'].notna().mean()
        n_obs = len(cd)
        if vol_pct >= 0.5 and util_pct >= 0.5 and n_obs >= 50:
            good_csus.append(csu)
            print(f"  KEEP {csu}: {n_obs} obs, util={util_pct:.0%}, vol={vol_pct:.0%}")
        else:
            print(f"  DROP {csu}: {n_obs} obs, util={util_pct:.0%}, vol={vol_pct:.0%}")

    panel = panel[panel['csu'].isin(good_csus)].copy()

    # For balanced panel: find common date range
    date_counts = panel.groupby('date')['csu'].nunique()
    max_csus = date_counts.max()
    # Keep dates where at least 80% of CSUs have data
    good_dates = date_counts[date_counts >= max_csus * 0.8].index
    panel = panel[panel['date'].isin(good_dates)]

    return panel


def main():
    parser = argparse.ArgumentParser(description='Build volatility panel for all CSUs')
    parser.add_argument('--window', type=int, default=14, help='Rolling volatility window (default: 14)')
    parser.add_argument('--skip-fetch', action='store_true', help='Skip DefiLlama price fetching')
    args = parser.parse_args()

    print("=" * 70)
    print("Building Utilization + Volatility Panel (All CSUs)")
    print("=" * 70)

    # Step 1: Scan bronze TVL
    all_snapshots, date_tokens = scan_all_bronze_tvl()

    # Step 2: Load and update price caches
    print("\nLoading price caches...")
    cache = load_price_cache()
    print(f"  Symbol-based prices: {len(cache):,}")
    oracle_cache = load_oracle_price_cache()
    print(f"  Protocol oracle prices: {len(oracle_cache):,}")

    if not args.skip_fetch:
        print("\nFetching missing prices from DefiLlama...")
        cache = fetch_missing_prices(date_tokens, cache)
        save_price_cache(cache)

    # Step 3: Build composition + volatility (using both price sources)
    vol_df = build_composition_and_volatility(
        all_snapshots, cache, window=args.window, oracle_cache=oracle_cache)

    if vol_df.empty:
        print("ERROR: No volatility data produced!")
        return

    # Step 4: Build panel
    panel = build_panel(vol_df, args.window)

    # Summary
    print("\n" + "=" * 70)
    print("Panel Summary")
    print("=" * 70)
    print(f"  CSUs (N): {panel['csu'].nunique()}")
    print(f"  Dates (T): {panel['date'].nunique()}")
    print(f"  Total observations: {len(panel):,}")
    print(f"  Date range: {panel['date'].min()} to {panel['date'].max()}")
    print(f"  Utilization coverage: {panel['utilization'].notna().mean():.1%}")
    print(f"  Volatility coverage: {panel['volatility'].notna().mean():.1%}")

    # Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    excel_path = OUTPUT_DIR / 'vol_util_panel.xlsx'
    panel.to_excel(excel_path, sheet_name='panel_data', index=False)
    print(f"\nSaved: {excel_path}")

    parquet_path = OUTPUT_DIR / 'vol_util_panel.parquet'
    panel.to_parquet(parquet_path, index=False)
    print(f"Saved: {parquet_path}")

    # Also save the full price cache back to ethereum reference
    eth_cache_path = PRICE_CACHE_DIR / 'price_cache_ethereum.json'
    with open(eth_cache_path, 'w') as f:
        json.dump(cache, f, indent=2)
    print(f"Updated: {eth_cache_path} ({len(cache):,} prices)")

    # Config for Panel VAR
    print(f"\n" + "=" * 70)
    print("Panel VAR Configuration")
    print("=" * 70)
    print(f"""
excel_path = "vol_util_panel.xlsx"
excel_sheet_name = "panel_data"
td_col = ["date"]
member_col = "csu"

variables = {{
    'utilization': [0],
    'volatility': [0],
}}

variable_order = ['utilization', 'volatility']
""")


if __name__ == '__main__':
    main()
