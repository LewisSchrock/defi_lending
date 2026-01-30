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
}


def _get_symbol(market: dict, chain: str = '') -> str:
    """Extract underlying token symbol from any bronze TVL schema."""
    sym = (
        market.get('underlying_symbol') or
        market.get('token_symbol') or
        market.get('symbol') or
        market.get('asset_symbol') or
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
    return market.get('total_supply_raw') or 0


def load_price_cache() -> dict:
    """Load unified price cache."""
    cache = {}
    for f in PRICE_CACHE_DIR.glob('price_cache_*.json'):
        with open(f) as fh:
            cache.update(json.load(fh))
    # Also load the daily cache
    daily = PRICE_CACHE_DIR.parent / 'data' / 'cache' / 'prices' / 'daily_prices.json'
    if daily.exists():
        with open(daily) as fh:
            cache.update(json.load(fh))
    return cache


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


def build_composition_and_volatility(all_snapshots: dict, cache: dict, window: int = 14) -> pd.DataFrame:
    """
    From bronze TVL + prices, compute:
    - collateral weights per CSU per date
    - basket returns
    - rolling volatility
    """
    print(f"\nBuilding collateral composition and {window}-day volatility...")

    all_results = []

    for csu, snapshots in sorted(all_snapshots.items()):
        if not snapshots:
            continue

        # Step 1: Compute daily basket returns
        # Need: weights from t-1, returns from t
        daily_data = {}  # date -> {symbol: (weight, supplied_usd)}

        for snap in snapshots:
            date = snap['date']
            chain = snap.get('chain', '')
            markets = snap.get('data', [])

            token_usd = {}
            for m in markets:
                sym = _get_symbol(m, chain)
                dec = _get_decimals(m)
                raw = _get_supply_raw(m)
                if raw == 0:
                    continue

                human_amount = raw / (10 ** dec)

                # Get price
                cache_key = f"{date}_{sym}"
                price = cache.get(cache_key)
                if price is None:
                    if sym.upper() in STABLECOINS or sym in STABLECOINS:
                        price = 1.0
                    else:
                        continue

                usd_val = human_amount * price
                if usd_val > 0:
                    token_usd[sym] = usd_val

            total_usd = sum(token_usd.values())
            if total_usd > 0:
                weights = {sym: val / total_usd for sym, val in token_usd.items()}
                daily_data[date] = weights

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
                p_today = cache.get(f"{date}_{sym}")
                p_prev = cache.get(f"{prev_date}_{sym}")

                if p_today is None and (sym.upper() in STABLECOINS or sym in STABLECOINS):
                    p_today = 1.0
                if p_prev is None and (sym.upper() in STABLECOINS or sym in STABLECOINS):
                    p_prev = 1.0

                if p_today and p_prev and p_today > 0 and p_prev > 0:
                    log_ret = np.log(p_today) - np.log(p_prev)
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

        all_results.append(br_df[['date', 'csu', 'basket_return', 'volatility']])

        vol_coverage = br_df['volatility'].notna().mean() * 100
        print(f"  {csu}: {len(br_df)} days, {vol_coverage:.0f}% volatility coverage")

    if not all_results:
        return pd.DataFrame()

    return pd.concat(all_results, ignore_index=True)


def build_panel(vol_df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Merge volatility with utilization from silver TVL."""
    print("\nBuilding final panel...")

    # Load utilization from silver TVL
    tvl = pd.read_csv('data/silver/tvl/daily_tvl.csv')
    tvl['date'] = pd.to_datetime(tvl['date']).dt.strftime('%Y-%m-%d')
    tvl['utilization'] = tvl['total_borrow_usd'] / tvl['total_supply_usd']
    tvl['utilization'] = tvl['utilization'].replace([np.inf, -np.inf], np.nan).clip(0, 1)

    # Only keep CSUs that have volatility data
    vol_csus = set(vol_df['csu'].unique())
    util_df = tvl[tvl['csu'].isin(vol_csus)][['date', 'csu', 'utilization']].copy()

    # Merge
    panel = util_df.merge(
        vol_df[['date', 'csu', 'basket_return', 'volatility']],
        on=['date', 'csu'],
        how='inner'
    )

    panel = panel.sort_values(['csu', 'date']).reset_index(drop=True)

    # Drop CSUs with poor coverage
    good_csus = []
    for csu in sorted(panel['csu'].unique()):
        cd = panel[panel['csu'] == csu]
        vol_pct = cd['volatility'].notna().mean()
        util_pct = cd['utilization'].notna().mean()
        n_obs = len(cd)
        if vol_pct >= 0.5 and util_pct >= 0.5 and n_obs >= 100:
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

    # Step 2: Load and update price cache
    print("\nLoading price cache...")
    cache = load_price_cache()
    print(f"  Existing prices: {len(cache):,}")

    if not args.skip_fetch:
        print("\nFetching missing prices from DefiLlama...")
        cache = fetch_missing_prices(date_tokens, cache)
        save_price_cache(cache)

    # Step 3: Build composition + volatility
    vol_df = build_composition_and_volatility(all_snapshots, cache, window=args.window)

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
