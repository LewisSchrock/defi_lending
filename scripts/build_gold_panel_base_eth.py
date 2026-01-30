#!/usr/bin/env python3
"""
Build Gold Panel — Base + Ethereum Chains

Creates a balanced daily panel merging:
  1. Liquidations (from silver layer)
  2. Utilization (from silver TVL)
  3. Collateral volatility (from vol_util_panel)

Restricted to dates with Base liquidation data (2024-01-02 to 2025-01-25).

Output: data/gold/panel_base_eth/gold_panel_base_eth.parquet (and .xlsx)

Usage:
    python scripts/build_gold_panel_base_eth.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pandas as pd
import numpy as np
from collections import Counter

# === Paths ===
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
BRONZE_LIQ = DATA / "bronze" / "liquidations"
BRONZE_TVL = DATA / "bronze" / "tvl"
SILVER_LIQ = DATA / "silver" / "liquidations"
SILVER_TVL = DATA / "silver" / "tvl" / "daily_tvl.csv"
PRICE_CACHE_DIR = DATA / "reference"
OUTPUT_DIR = DATA / "gold" / "panel_base_eth"

# Stablecoins (assume $1.00)
STABLECOINS = {
    'USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'sUSD', 'USDbC', 'USDBC',
    'USDC.e', 'DAI.e', 'GHO', 'MAI', 'sDAI', 'USDS', 'USD0',
    'crvUSD', 'PYUSD', 'GUSD', 'TUSD', 'BUSD', 'USDP', 'FDUSD',
    'WXDAI', 'SUSD', 'MUSD',
}

SKIP_TOKENS = {'UNKNOWN', 'PT-', 'deUSD', 'sdeUSD', 'eUSDe', 'wUSDM', 'sFRAX', 'sUSDS'}

NATIVE_TOKEN = {
    'ethereum': 'ETH', 'arbitrum': 'ETH', 'optimism': 'ETH',
    'base': 'ETH', 'linea': 'ETH', 'scroll': 'ETH',
    'xdai': 'WXDAI', 'polygon': 'MATIC', 'avalanche': 'AVAX',
    'binance': 'BNB', 'meter': 'MTR',
}

# === CSU Configuration ===
# Exclude CSUs with near-zero utilization or too-short series
EXCLUDE_CSUS = {
    'gearbox_ethereum',         # util ≈ 0
    'fluid_lending_ethereum',   # util ≈ 0
    'compound_v3_base_usdbc',   # util ≈ 0
    'compound_v3_ethereum',     # only 1 day of TVL
}

# All Base + Ethereum CSUs (after exclusions)
BASE_CSUS = [
    'aave_v3_base',
    'compound_v3_base_aero',
    'compound_v3_base_usdc',
    'compound_v3_base_weth',
    'moonwell_lending_base',
]

ETH_CSUS = [
    'aave_v3_ethereum',
    'compound_v3_eth_usdc',
    'compound_v3_eth_usds',
    'compound_v3_eth_usdt',
    'compound_v3_eth_weth',
    'compound_v3_eth_wsteth',
    'sparklend_ethereum',
]

ALL_CSUS = BASE_CSUS + ETH_CSUS


# === Price Loading ===

def load_all_prices() -> dict:
    """Load all available price caches."""
    cache = {}
    # Reference price caches (per-chain)
    for f in PRICE_CACHE_DIR.glob("price_cache_*.json"):
        with open(f) as fh:
            cache.update(json.load(fh))
    # Daily prices cache (from DefiLlama)
    daily = DATA / "cache" / "prices" / "daily_prices.json"
    if daily.exists():
        with open(daily) as fh:
            cache.update(json.load(fh))
    return cache


# === Step 1: Build Liquidation Panel ===

def load_silver_liquidations(chain: str) -> pd.DataFrame:
    """Load silver liquidations for a chain."""
    path = SILVER_LIQ / chain / "liquidations.parquet"
    if not path.exists():
        print(f"  WARNING: No silver liquidations for {chain}")
        return pd.DataFrame()
    df = pd.read_parquet(path)
    df['date'] = df['date'].astype(str)
    df = df[df['date'] != 'None']
    df = df.dropna(subset=['date'])
    return df


def enrich_usd_values(df: pd.DataFrame, price_cache: dict) -> pd.DataFrame:
    """Fill missing collateral_usd and debt_usd using price cache."""
    df = df.copy()
    filled_coll = 0
    filled_debt = 0

    for idx in df.index:
        date = df.at[idx, 'date']

        # Collateral USD
        if pd.isna(df.at[idx, 'collateral_usd']) or df.at[idx, 'collateral_usd'] == 0:
            sym = df.at[idx, 'collateral_symbol']
            amt = df.at[idx, 'collateral_amount']
            if pd.notna(sym) and pd.notna(amt) and amt > 0:
                price = price_cache.get(f"{date}_{sym}")
                if price:
                    df.at[idx, 'collateral_usd'] = amt * price
                    filled_coll += 1

        # Debt USD
        if pd.isna(df.at[idx, 'debt_usd']) or df.at[idx, 'debt_usd'] == 0:
            sym = df.at[idx, 'debt_symbol']
            amt = df.at[idx, 'debt_amount']
            if pd.notna(sym) and pd.notna(amt) and amt > 0:
                price = price_cache.get(f"{date}_{sym}")
                if price:
                    df.at[idx, 'debt_usd'] = amt * price
                    filled_debt += 1

    print(f"    Enriched: {filled_coll} collateral, {filled_debt} debt USD values")
    return df


def aggregate_daily_liquidations(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate silver events to daily CSU-level totals."""
    if df.empty:
        return pd.DataFrame(columns=['date', 'csu', 'n_liquidations',
                                      'total_collateral_usd', 'total_debt_usd',
                                      'n_unique_borrowers', 'n_unique_liquidators'])

    agg = df.groupby(['date', 'csu']).agg(
        n_liquidations=('tx_hash', 'count'),
        total_collateral_usd=('collateral_usd', 'sum'),
        total_debt_usd=('debt_usd', 'sum'),
        n_unique_borrowers=('borrower', 'nunique'),
        n_unique_liquidators=('liquidator', 'nunique'),
    ).reset_index()

    return agg


def build_liquidation_panel(date_range: list, csus: list,
                            base_silver: pd.DataFrame, eth_silver: pd.DataFrame) -> pd.DataFrame:
    """Build balanced daily liquidation panel."""
    # Aggregate both chains
    base_daily = aggregate_daily_liquidations(base_silver)
    eth_daily = aggregate_daily_liquidations(eth_silver)
    daily = pd.concat([base_daily, eth_daily], ignore_index=True)

    # Create balanced panel skeleton
    full_idx = pd.MultiIndex.from_product([date_range, csus], names=['date', 'csu'])
    panel = pd.DataFrame(index=full_idx).reset_index()

    # Merge
    panel = panel.merge(daily, on=['date', 'csu'], how='left')

    # Fill zeros for days without liquidations
    fill_cols = ['n_liquidations', 'total_collateral_usd', 'total_debt_usd',
                 'n_unique_borrowers', 'n_unique_liquidators']
    for col in fill_cols:
        panel[col] = panel[col].fillna(0)

    int_cols = ['n_liquidations', 'n_unique_borrowers', 'n_unique_liquidators']
    for col in int_cols:
        panel[col] = panel[col].astype(int)

    # Derived features
    panel['has_liquidation'] = (panel['n_liquidations'] > 0).astype(int)
    panel['log_collateral_usd'] = np.log1p(panel['total_collateral_usd'])
    panel['log_debt_usd'] = np.log1p(panel['total_debt_usd'])
    panel['log_n_liquidations'] = np.log1p(panel['n_liquidations'])

    return panel.sort_values(['date', 'csu']).reset_index(drop=True)


# === Step 2: Add Utilization ===

def load_utilization(csus: list) -> pd.DataFrame:
    """Load utilization from silver TVL."""
    tvl = pd.read_csv(SILVER_TVL)
    tvl = tvl[tvl['csu'].isin(csus)].copy()
    tvl['utilization'] = tvl['total_borrow_usd'] / tvl['total_supply_usd']
    tvl['utilization'] = tvl['utilization'].replace([np.inf, -np.inf], np.nan).clip(0, 1)
    return tvl[['date', 'csu', 'utilization', 'total_supply_usd', 'total_borrow_usd']]


# === Step 3: Compute Volatility from Bronze TVL ===

def _get_symbol(market: dict, chain: str = '') -> str:
    sym = (market.get('underlying_symbol') or market.get('token_symbol') or
           market.get('symbol') or market.get('asset_symbol') or 'UNKNOWN')
    if sym == 'NATIVE':
        return NATIVE_TOKEN.get(chain, 'ETH')
    if '.' in sym and sym.rsplit('.', 1)[-1] in ('eth', 'bsc', 'matic'):
        sym = sym.rsplit('.', 1)[0]
    return sym


def _get_decimals(market: dict) -> int:
    return (market.get('underlying_decimals') or market.get('token_decimals') or
            market.get('decimals') or 18)


def _get_supply_raw(market: dict) -> int:
    if 'supplied_raw' in market:
        return market['supplied_raw']
    if 'tvl_underlying_raw' in market:
        return market['tvl_underlying_raw']
    if 'get_cash_raw' in market:
        return (market.get('get_cash_raw') or 0) + (market.get('total_borrows_raw') or 0)
    if 'total_assets_raw' in market:
        return market['total_assets_raw']
    return market.get('total_supply_raw') or 0


def compute_volatility_from_bronze(csus: list, price_cache: dict, window: int = 14) -> pd.DataFrame:
    """
    Compute collateral basket volatility directly from bronze TVL data.
    This avoids the 80% CSU date filter in build_volatility_panel.py,
    giving us full coverage back to Jan 2024.
    """
    print(f"  Computing {window}-day rolling volatility from bronze TVL...")
    all_results = []

    for csu in csus:
        csu_dir = BRONZE_TVL / csu
        if not csu_dir.exists():
            print(f"    {csu}: no bronze TVL directory")
            continue

        json_files = sorted(csu_dir.glob('*.json'))
        if not json_files:
            continue

        # Load all snapshots
        daily_data = {}  # date -> {symbol: weight}
        for jf in json_files:
            try:
                with open(jf) as f:
                    data = json.load(f)
                date = data.get('date')
                chain = data.get('chain', '')
                markets = data.get('data', [])
                if not date or not markets:
                    continue

                token_usd = {}
                for m in markets:
                    sym = _get_symbol(m, chain)
                    dec = _get_decimals(m)
                    raw = _get_supply_raw(m)
                    if raw == 0:
                        continue

                    human_amount = raw / (10 ** dec)

                    # Get price
                    price = price_cache.get(f"{date}_{sym}")
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
                    daily_data[date] = {sym: val / total_usd for sym, val in token_usd.items()}
            except:
                continue

        dates = sorted(daily_data.keys())
        if len(dates) < window + 1:
            print(f"    {csu}: only {len(dates)} dates, need {window+1}")
            continue

        # Compute basket returns
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
                p_today = price_cache.get(f"{date}_{sym}")
                p_prev = price_cache.get(f"{prev_date}_{sym}")
                if p_today is None and (sym.upper() in STABLECOINS or sym in STABLECOINS):
                    p_today = 1.0
                if p_prev is None and (sym.upper() in STABLECOINS or sym in STABLECOINS):
                    p_prev = 1.0
                if p_today and p_prev and p_today > 0 and p_prev > 0:
                    log_ret = np.log(p_today) - np.log(p_prev)
                    basket_ret += w * log_ret
                    total_w += w

            if total_w > 0.3:
                basket_returns.append({'date': date, 'basket_return': basket_ret})

        if len(basket_returns) < window:
            print(f"    {csu}: only {len(basket_returns)} basket returns, need {window}")
            continue

        br_df = pd.DataFrame(basket_returns).sort_values('date')
        br_df['volatility'] = br_df['basket_return'].rolling(
            window=window, min_periods=2
        ).std()
        br_df['csu'] = csu

        all_results.append(br_df[['date', 'csu', 'basket_return', 'volatility']])
        vol_pct = br_df['volatility'].notna().mean() * 100
        print(f"    {csu}: {len(br_df)} days, vol coverage={vol_pct:.0f}%, range={dates[0]} to {dates[-1]}")

    if not all_results:
        return pd.DataFrame(columns=['date', 'csu', 'basket_return', 'volatility'])

    return pd.concat(all_results, ignore_index=True)


# === Main ===

def main():
    print("=" * 70)
    print("Building Gold Panel — Base + Ethereum")
    print("=" * 70)

    # Load prices
    print("\n[1/6] Loading price cache...")
    prices = load_all_prices()
    print(f"  {len(prices):,} cached prices")

    # Load silver liquidations
    print("\n[2/6] Loading silver liquidations...")
    base_silver = load_silver_liquidations('base')
    eth_silver = load_silver_liquidations('ethereum')
    print(f"  Base: {len(base_silver):,} events")
    print(f"  Ethereum: {len(eth_silver):,} events")

    # Enrich Base USD values
    print("\n  Enriching Base liquidation USD values...")
    base_before = base_silver['collateral_usd'].notna().sum()
    base_silver = enrich_usd_values(base_silver, prices)
    base_after = base_silver['collateral_usd'].notna().sum()
    print(f"    collateral_usd coverage: {base_before} → {base_after} / {len(base_silver)}")

    # Also enrich Ethereum where missing
    print("  Enriching Ethereum liquidation USD values...")
    eth_silver = enrich_usd_values(eth_silver, prices)

    # Filter to relevant CSUs
    base_silver = base_silver[base_silver['csu'].isin(ALL_CSUS)]
    eth_silver = eth_silver[eth_silver['csu'].isin(ALL_CSUS)]
    print(f"\n  After CSU filter: Base={len(base_silver):,}, Eth={len(eth_silver):,}")

    # Determine date range: dates with Base liquidation data
    print("\n[3/6] Determining date range...")
    base_liq_dates = sorted(base_silver['date'].unique())
    print(f"  Base liquidation dates: {base_liq_dates[0]} to {base_liq_dates[-1]} ({len(base_liq_dates)} days)")

    # Use full calendar range between first and last Base liq date
    all_dates = pd.date_range(start=base_liq_dates[0], end=base_liq_dates[-1], freq='D')
    date_range = [d.strftime('%Y-%m-%d') for d in all_dates]
    print(f"  Full calendar range: {date_range[0]} to {date_range[-1]} ({len(date_range)} days)")

    # Build liquidation panel
    print(f"\n[4/6] Building liquidation panel ({len(ALL_CSUS)} CSUs × {len(date_range)} days)...")
    liq_panel = build_liquidation_panel(date_range, ALL_CSUS, base_silver, eth_silver)
    print(f"  Panel: {len(liq_panel):,} obs")
    print(f"  Days with any liquidation: {liq_panel.groupby('date')['n_liquidations'].sum().gt(0).sum()}")

    # Add utilization
    print("\n[5/6] Adding utilization...")
    util_df = load_utilization(ALL_CSUS)
    liq_panel = liq_panel.merge(
        util_df[['date', 'csu', 'utilization', 'total_supply_usd', 'total_borrow_usd']],
        on=['date', 'csu'], how='left'
    )
    util_coverage = liq_panel['utilization'].notna().mean() * 100
    print(f"  Utilization coverage: {util_coverage:.1f}%")

    # Compute volatility from bronze TVL (full date range)
    print("\n[6/6] Computing volatility from bronze TVL...")
    vol_df = compute_volatility_from_bronze(ALL_CSUS, prices, window=14)
    liq_panel = liq_panel.merge(
        vol_df[['date', 'csu', 'basket_return', 'volatility']],
        on=['date', 'csu'], how='left'
    )
    vol_coverage = liq_panel['volatility'].notna().mean() * 100
    print(f"  Volatility coverage: {vol_coverage:.1f}%")

    # Final panel
    panel = liq_panel.sort_values(['csu', 'date']).reset_index(drop=True)

    # === Summary ===
    print("\n" + "=" * 70)
    print("GOLD PANEL SUMMARY")
    print("=" * 70)
    print(f"\nDimensions:")
    print(f"  CSUs (N):      {panel['csu'].nunique()}")
    print(f"  Dates (T):     {panel['date'].nunique()}")
    print(f"  Observations:  {len(panel):,}")
    print(f"  Date range:    {panel['date'].min()} to {panel['date'].max()}")

    print(f"\nVariable coverage:")
    for col in ['n_liquidations', 'utilization', 'volatility', 'total_collateral_usd']:
        cov = panel[col].notna().mean() * 100
        mn = panel[col].mean()
        print(f"  {col:30s}: {cov:5.1f}% coverage, mean={mn:.4f}")

    print(f"\nBy CSU:")
    for csu in sorted(panel['csu'].unique()):
        sub = panel[panel['csu'] == csu]
        n_liq = sub['n_liquidations'].sum()
        days_liq = sub['has_liquidation'].sum()
        util_m = sub['utilization'].mean()
        vol_m = sub['volatility'].mean()
        chain = 'base' if '_base' in csu or 'moonwell' in csu else 'ethereum'
        print(f"  {csu} ({chain}):")
        print(f"    Liquidations: {n_liq:,} events, {days_liq} days with liq")
        print(f"    Util: {util_m:.3f}" if pd.notna(util_m) else "    Util: N/A", end="")
        print(f"  |  Vol: {vol_m:.4f}" if pd.notna(vol_m) else "  |  Vol: N/A")

    # Liquidation USD coverage check
    liq_events = panel[panel['n_liquidations'] > 0]
    zero_usd = (liq_events['total_collateral_usd'] == 0).sum()
    print(f"\n  Liquidation USD coverage:")
    print(f"    Days with liquidations: {len(liq_events):,}")
    print(f"    Days with $0 collateral USD: {zero_usd} ({100*zero_usd/max(1,len(liq_events)):.1f}%)")

    # === Save ===
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    parquet_path = OUTPUT_DIR / "gold_panel_base_eth.parquet"
    panel.to_parquet(parquet_path, index=False)
    print(f"\nSaved: {parquet_path}")

    xlsx_path = OUTPUT_DIR / "gold_panel_base_eth.xlsx"
    panel.to_excel(xlsx_path, sheet_name='panel_data', index=False)
    print(f"Saved: {xlsx_path}")

    # Also save a summary CSV
    summary_path = OUTPUT_DIR / "panel_summary.csv"
    summary_rows = []
    for csu in sorted(panel['csu'].unique()):
        sub = panel[panel['csu'] == csu]
        chain = 'base' if '_base' in csu or 'moonwell' in csu else 'ethereum'
        summary_rows.append({
            'csu': csu,
            'chain': chain,
            'n_dates': sub['date'].nunique(),
            'total_liquidations': int(sub['n_liquidations'].sum()),
            'days_with_liquidation': int(sub['has_liquidation'].sum()),
            'total_collateral_usd': sub['total_collateral_usd'].sum(),
            'mean_utilization': sub['utilization'].mean(),
            'mean_volatility': sub['volatility'].mean(),
        })
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    print(f"Saved: {summary_path}")

    print(f"\n{'='*70}")
    print("Gold panel complete — ready for 3-variable Panel VAR")
    print(f"  Variables: utilization, volatility, liquidation")
    print(f"  Cholesky ordering: utilization → volatility → liquidation")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
