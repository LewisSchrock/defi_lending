#!/usr/bin/env python3
"""
Build Gold Layer - Daily Liquidation Panels

Aggregates silver liquidation data into daily panels by CSU for econometric analysis.
Creates a balanced panel with zeros for days without liquidations.

Output schema:
- date: Date (index)
- csu: CSU identifier (index)
- n_liquidations: Count of liquidation events
- total_collateral_usd: Sum of collateral seized in USD
- total_debt_usd: Sum of debt repaid in USD
- n_unique_borrowers: Count of unique borrowers liquidated
- n_unique_liquidators: Count of unique liquidators
- avg_collateral_usd: Average collateral per liquidation
- avg_debt_usd: Average debt per liquidation

Usage:
    python3 scripts/build_gold_liquidations.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def load_silver_data(chain: str = 'ethereum') -> pd.DataFrame:
    """Load silver liquidation data."""
    silver_path = Path(f'data/silver/liquidations/{chain}/liquidations.parquet')
    if not silver_path.exists():
        raise FileNotFoundError(f"Silver data not found: {silver_path}")
    return pd.read_parquet(silver_path)


def aggregate_daily_by_csu(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate liquidations to daily totals by CSU."""

    agg = df.groupby(['date', 'csu']).agg(
        n_liquidations=('tx_hash', 'count'),
        total_collateral_usd=('collateral_usd', 'sum'),
        total_debt_usd=('debt_usd', 'sum'),
        n_unique_borrowers=('borrower', 'nunique'),
        n_unique_liquidators=('liquidator', 'nunique'),
    ).reset_index()

    # Calculate averages (handle division by zero)
    agg['avg_collateral_usd'] = agg['total_collateral_usd'] / agg['n_liquidations']
    agg['avg_debt_usd'] = agg['total_debt_usd'] / agg['n_liquidations']

    return agg


def create_balanced_panel(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Create balanced panel with all CSU × date combinations.

    Days without liquidations get zeros.
    """
    # Get date range
    if start_date is None:
        start_date = df['date'].min()
    if end_date is None:
        end_date = df['date'].max()

    # Create all dates
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    dates = [d.strftime('%Y-%m-%d') for d in dates]

    # Get all CSUs
    csus = df['csu'].unique().tolist()

    # Create full panel index
    full_index = pd.MultiIndex.from_product([dates, csus], names=['date', 'csu'])
    full_panel = pd.DataFrame(index=full_index).reset_index()

    # Merge with actual data
    panel = full_panel.merge(df, on=['date', 'csu'], how='left')

    # Fill missing values with zeros
    fill_cols = ['n_liquidations', 'total_collateral_usd', 'total_debt_usd',
                 'n_unique_borrowers', 'n_unique_liquidators',
                 'avg_collateral_usd', 'avg_debt_usd']

    for col in fill_cols:
        panel[col] = panel[col].fillna(0)

    # Convert counts to int
    int_cols = ['n_liquidations', 'n_unique_borrowers', 'n_unique_liquidators']
    for col in int_cols:
        panel[col] = panel[col].astype(int)

    return panel.sort_values(['date', 'csu']).reset_index(drop=True)


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features useful for econometric analysis."""

    df = df.copy()

    # Binary indicator: any liquidation that day
    df['has_liquidation'] = (df['n_liquidations'] > 0).astype(int)

    # Log transforms (add 1 to handle zeros)
    df['log_collateral_usd'] = np.log1p(df['total_collateral_usd'])
    df['log_debt_usd'] = np.log1p(df['total_debt_usd'])
    df['log_n_liquidations'] = np.log1p(df['n_liquidations'])

    return df


def main():
    print("=" * 70)
    print("Building Gold Layer - Daily Liquidation Panels")
    print("=" * 70)

    # Load silver data
    print("\nLoading silver data...")
    df = load_silver_data('ethereum')
    print(f"  Loaded {len(df):,} liquidation events")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  CSUs: {df['csu'].nunique()}")

    # Aggregate to daily by CSU
    print("\nAggregating to daily panels...")
    daily = aggregate_daily_by_csu(df)
    print(f"  Created {len(daily):,} CSU-day observations (sparse)")

    # Create balanced panel
    print("\nCreating balanced panel...")
    panel = create_balanced_panel(daily)
    print(f"  Balanced panel: {len(panel):,} observations")
    print(f"  ({panel['date'].nunique()} dates × {panel['csu'].nunique()} CSUs)")

    # Add derived features
    print("\nAdding derived features...")
    panel = add_derived_features(panel)

    # Summary statistics
    print("\n" + "=" * 70)
    print("Panel Summary Statistics")
    print("=" * 70)

    # By CSU
    print("\nBy CSU:")
    print("-" * 70)
    csu_summary = panel.groupby('csu').agg({
        'n_liquidations': 'sum',
        'has_liquidation': 'sum',
        'total_collateral_usd': 'sum',
        'total_debt_usd': 'sum',
    }).round(2)
    csu_summary.columns = ['Total Events', 'Days w/ Liquidations', 'Total Collateral USD', 'Total Debt USD']

    for csu in csu_summary.index:
        row = csu_summary.loc[csu]
        total_days = panel[panel['csu'] == csu]['date'].nunique()
        pct_days = (row['Days w/ Liquidations'] / total_days) * 100
        print(f"  {csu}:")
        print(f"    Events: {int(row['Total Events']):,}")
        print(f"    Days with liquidations: {int(row['Days w/ Liquidations'])} / {total_days} ({pct_days:.1f}%)")
        print(f"    Collateral USD: ${row['Total Collateral USD']:,.0f}")
        print(f"    Debt USD: ${row['Total Debt USD']:,.0f}")
        print()

    # Overall
    print("Overall:")
    print("-" * 70)
    total_events = panel['n_liquidations'].sum()
    days_with_liq = (panel.groupby('date')['n_liquidations'].sum() > 0).sum()
    total_days = panel['date'].nunique()
    print(f"  Total liquidation events: {total_events:,}")
    print(f"  Days with any liquidation: {days_with_liq} / {total_days} ({100*days_with_liq/total_days:.1f}%)")
    print(f"  Total collateral seized: ${panel['total_collateral_usd'].sum():,.0f}")
    print(f"  Total debt repaid: ${panel['total_debt_usd'].sum():,.0f}")

    # Save
    output_dir = Path('data/gold/liquidations/ethereum')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / 'daily_panel.parquet'
    panel.to_parquet(output_path, index=False)
    print(f"\nSaved to: {output_path}")

    # Also save as CSV for easy inspection
    csv_path = output_dir / 'daily_panel.csv'
    panel.to_csv(csv_path, index=False)
    print(f"Also saved CSV: {csv_path}")

    # Panel structure verification
    print("\n" + "=" * 70)
    print("Panel VAR Readiness Check")
    print("=" * 70)

    n_csus = panel['csu'].nunique()
    n_dates = panel['date'].nunique()
    expected_obs = n_csus * n_dates
    actual_obs = len(panel)

    print(f"\n  Cross-sectional units (N): {n_csus}")
    print(f"  Time periods (T): {n_dates}")
    print(f"  Expected observations (N×T): {expected_obs:,}")
    print(f"  Actual observations: {actual_obs:,}")
    print(f"  Panel balanced: {'Yes' if expected_obs == actual_obs else 'No'}")

    # Check for sufficient variation
    print("\n  Variation check:")
    for csu in panel['csu'].unique():
        csu_data = panel[panel['csu'] == csu]
        var_events = csu_data['n_liquidations'].var()
        var_usd = csu_data['total_debt_usd'].var()
        print(f"    {csu}: var(events)={var_events:.2f}, var(debt_usd)={var_usd:.2e}")

    print("\n✓ Gold layer complete - panel ready for econometric analysis")


if __name__ == '__main__':
    main()
