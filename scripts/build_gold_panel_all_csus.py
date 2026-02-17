#!/usr/bin/env python3
"""
Build Complete Gold Panel — All CSUs

Merges liquidation and TVL data for all 27 CSUs with complete data:
  1. Liquidations (from gold/liquidations/all_chains)
  2. TVL data (from silver/tvl)
  3. Volatility calculations (collateral basket returns)

Output: data/gold/panel_all_csus/gold_panel_all_csus.parquet

Usage:
    python scripts/build_gold_panel_all_csus.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pandas as pd
import numpy as np
from datetime import datetime

# === Paths ===
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
SILVER_TVL = DATA / "silver" / "tvl" / "daily_tvl.csv"
VOL_UTIL_PANEL = DATA / "analysis" / "vol_util_panel.parquet"
GOLD_LIQ = DATA / "gold" / "liquidations" / "all_chains" / "daily_panel.parquet"
PRICE_CACHE_DIR = DATA / "reference"
OUTPUT_DIR = DATA / "gold" / "panel_all_csus"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CSU name mappings — now empty because bronze parser (resolve_csu) already
# produces names that match the vol_util convention. If any mismatch appears,
# add entries here as {source_name: canonical_name}.
CSU_NAME_MAP = {}

# Exclude test/aggregate CSUs from TVL
TVL_EXCLUDE = {
    'compound_v3_ethereum',     # Aggregate, not a real market
    'fluid_lending_ethereum',   # Different protocol, not in liquidations
    'fluid_lending_arbitrum',
    'sumermoney_meter',
}

# Stablecoins (assume $1.00 if price unavailable)
STABLECOINS = {
    'USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'sUSD', 'USDbC', 'USDBC',
    'USDC.e', 'USDT.e', 'DAI.e', 'GHO', 'MAI', 'sDAI', 'USDS', 'USD0',
    'crvUSD', 'PYUSD', 'GUSD', 'TUSD', 'BUSD', 'USDP', 'FDUSD',
    'WXDAI', 'SUSD', 'MUSD', 'USDC.E',
}


def load_price_cache() -> dict:
    """Load all available price caches."""
    cache = {}

    # Reference price caches (per-chain)
    for f in PRICE_CACHE_DIR.glob("price_cache_*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
                cache.update(data)
                print(f"  Loaded {len(data):,} prices from {f.name}")
        except Exception as e:
            print(f"  Warning: Could not load {f.name}: {e}")

    # Daily prices cache (from DefiLlama)
    daily = DATA / "cache" / "prices" / "daily_prices.json"
    if daily.exists():
        try:
            with open(daily) as fh:
                data = json.load(fh)
                cache.update(data)
                print(f"  Loaded {len(data):,} prices from daily_prices.json")
        except Exception as e:
            print(f"  Warning: Could not load daily_prices.json: {e}")

    print(f"  Total price cache entries: {len(cache):,}")
    return cache


def load_liquidations() -> pd.DataFrame:
    """Load gold liquidation panel."""
    print("\n1. Loading liquidation data...")
    df = pd.read_parquet(GOLD_LIQ)

    # Ensure date is string format YYYY-MM-DD
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    print(f"  Loaded {len(df):,} liquidation observations")
    print(f"  CSUs: {df['csu'].nunique()}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

    return df


def load_vol_util() -> pd.DataFrame:
    """Load volatility + utilization panel."""
    print("\n2. Loading vol_util panel (volatility + utilization)...")
    df = pd.read_parquet(VOL_UTIL_PANEL)

    # Normalize CSU names to match liquidation data
    df['csu'] = df['csu'].replace(CSU_NAME_MAP)

    # Ensure date is string format YYYY-MM-DD
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    print(f"  Loaded {len(df):,} observations")
    print(f"  CSUs: {df['csu'].nunique()}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

    return df


def load_tvl() -> pd.DataFrame:
    """Load TVL data for supply/borrow amounts."""
    print("\n3. Loading TVL data (supply/borrow amounts)...")
    df = pd.read_csv(SILVER_TVL)

    # Normalize CSU names
    df['csu'] = df['csu'].replace(CSU_NAME_MAP)

    # Exclude test/aggregate CSUs
    df = df[~df['csu'].isin(TVL_EXCLUDE)].copy()

    # Ensure date is string format YYYY-MM-DD
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    # Select relevant columns
    tvl = df[['date', 'csu', 'total_supply_usd', 'total_borrow_usd']].copy()

    print(f"  Loaded {len(tvl):,} TVL observations")
    print(f"  CSUs: {tvl['csu'].nunique()}")

    return tvl


def merge_all_data(liq: pd.DataFrame, vol_util: pd.DataFrame, tvl: pd.DataFrame) -> pd.DataFrame:
    """Merge liquidation, vol_util, and TVL data."""
    print("\n4. Merging liquidation + vol_util + TVL data...")

    # Find CSUs with all three datasets
    liq_csus = set(liq['csu'].unique())
    vol_csus = set(vol_util['csu'].unique())
    tvl_csus = set(tvl['csu'].unique())

    # CSUs with liquidation + volatility (minimum requirement)
    common_csus = liq_csus & vol_csus

    print(f"  CSUs with liquidation + volatility: {len(common_csus)}")
    print(f"  CSUs also with TVL: {len(common_csus & tvl_csus)}")

    # Merge liquidation + vol_util first
    merged = pd.merge(
        liq[liq['csu'].isin(common_csus)],
        vol_util[vol_util['csu'].isin(common_csus)],
        on=['date', 'csu'],
        how='outer',
        suffixes=('', '_vol')
    )

    # Add TVL data (supply/borrow amounts)
    merged = pd.merge(
        merged,
        tvl[tvl['csu'].isin(common_csus)],
        on=['date', 'csu'],
        how='left'
    )

    # Fill missing liquidation counts with 0
    for col in ['n_liquidations', 'total_collateral_usd', 'total_debt_usd',
                'n_unique_borrowers', 'n_unique_liquidators', 'n_priced']:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    # Create has_liquidation flag
    merged['has_liquidation'] = (merged['n_liquidations'] > 0).astype(int)

    # Create log transformations
    merged['log_collateral_usd'] = np.log1p(merged['total_collateral_usd'])
    merged['log_debt_usd'] = np.log1p(merged['total_debt_usd'])
    merged['log_n_liquidations'] = np.log1p(merged['n_liquidations'])

    print(f"  Merged panel: {len(merged):,} observations")
    print(f"  CSUs: {merged['csu'].nunique()}")
    print(f"  Date range: {merged['date'].min()} to {merged['date'].max()}")

    # Show CSUs included
    print(f"\n  CSUs in merged panel:")
    for i, csu in enumerate(sorted(merged['csu'].unique()), 1):
        chain = merged[merged['csu'] == csu]['chain'].iloc[0] if 'chain' in merged.columns else '?'
        print(f"    {i:2}. {csu:<40} ({chain})")

    return merged




def create_balanced_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Create balanced panel with all CSU x date combinations."""
    print("\n5. Creating balanced panel...")

    # Get full date range
    min_date = df['date'].min()
    max_date = df['date'].max()

    # Create all combinations
    csus = df['csu'].unique()
    dates = pd.date_range(start=min_date, end=max_date, freq='D')
    dates_str = [d.strftime('%Y-%m-%d') for d in dates]

    # Create full index
    index_df = pd.DataFrame([
        {'date': date, 'csu': csu}
        for csu in csus
        for date in dates_str
    ])

    # Merge with data
    balanced = pd.merge(index_df, df, on=['date', 'csu'], how='left')

    # Fill missing values
    fill_cols = ['n_liquidations', 'total_collateral_usd', 'total_debt_usd',
                 'n_unique_borrowers', 'n_unique_liquidators', 'n_priced',
                 'has_liquidation', 'log_collateral_usd', 'log_debt_usd',
                 'log_n_liquidations', 'basket_return', 'volatility']

    for col in fill_cols:
        if col in balanced.columns:
            balanced[col] = balanced[col].fillna(0)

    # Forward fill utilization and TVL
    balanced = balanced.sort_values(['csu', 'date'])
    for col in ['utilization', 'total_supply_usd', 'total_borrow_usd']:
        if col in balanced.columns:
            balanced[col] = balanced.groupby('csu')[col].ffill()

    print(f"  Balanced panel: {len(balanced):,} observations")
    print(f"  = {len(csus)} CSUs × {len(dates_str)} dates")

    return balanced


def save_panel(df: pd.DataFrame):
    """Save the gold panel."""
    print("\n6. Saving gold panel...")

    # Sort by CSU and date
    df = df.sort_values(['csu', 'date'])

    # Save as parquet
    output_parquet = OUTPUT_DIR / "gold_panel_all_csus.parquet"
    df.to_parquet(output_parquet, index=False)
    print(f"  Saved: {output_parquet}")

    # Save as CSV for inspection
    output_csv = OUTPUT_DIR / "gold_panel_all_csus.csv"
    df.to_csv(output_csv, index=False)
    print(f"  Saved: {output_csv}")

    # Summary stats
    summary = df.groupby('csu').agg({
        'n_liquidations': 'sum',
        'total_collateral_usd': 'sum',
        'utilization': 'mean',
        'total_supply_usd': 'mean',
    }).round(2)

    summary_path = OUTPUT_DIR / "panel_summary.csv"
    summary.to_csv(summary_path)
    print(f"  Saved: {summary_path}")

    # Print summary
    print(f"\n{'='*80}")
    print("GOLD PANEL SUMMARY")
    print(f"{'='*80}")
    print(f"Total observations: {len(df):,}")
    print(f"CSUs: {df['csu'].nunique()}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total collateral: ${df['total_collateral_usd'].sum():,.0f}")
    print(f"Total liquidations: {df['n_liquidations'].sum():,}")
    print(f"\nOutput: {output_parquet}")


def main():
    """Build complete gold panel."""
    print("="*80)
    print("BUILD GOLD PANEL — ALL CSUs")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*80)

    # Load data
    price_cache = load_price_cache()
    liquidations = load_liquidations()
    vol_util = load_vol_util()
    tvl = load_tvl()

    # Merge all three datasets
    panel = merge_all_data(liquidations, vol_util, tvl)

    # Create balanced panel
    panel = create_balanced_panel(panel)

    # Save
    save_panel(panel)

    print(f"\n{'='*80}")
    print(f"✅ COMPLETE")
    print(f"Finished: {datetime.now().isoformat()}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
