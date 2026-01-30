#!/usr/bin/env python3
"""
Prepare Data for Pedroni Panel SVAR

Constructs panel data with economically meaningful variables:
1. Leverage (Utilization Ratio) = Borrowed / Supplied
2. Liquidation = USD value of collateral seized per day
3. Volatility = Collateral-weighted rolling std dev of basket returns

See data/analysis/README.md for economic definitions.

Output: Excel file ready for Panel SVAR analysis

Usage:
    python scripts/prepare_panel_svar_data.py
    python scripts/prepare_panel_svar_data.py --window 7  # 7-day rolling volatility
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import pandas as pd
import numpy as np
from typing import Dict


# === Data Loading ===

def load_liquidation_panel() -> pd.DataFrame:
    """Load gold liquidation panel."""
    path = Path('data/gold/liquidations/ethereum/daily_panel.parquet')
    return pd.read_parquet(path)


def load_tvl_data() -> pd.DataFrame:
    """Load silver TVL data for utilization calculation."""
    path = Path('data/silver/tvl/daily_tvl.csv')
    return pd.read_csv(path)


def load_collateral_composition() -> pd.DataFrame:
    """Load collateral composition data."""
    path = Path('data/gold/collateral_composition/ethereum/all_csus_composition.parquet')
    return pd.read_parquet(path)


def load_price_cache() -> Dict[str, float]:
    """Load historical price cache."""
    path = Path('data/reference/price_cache_ethereum.json')
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


# === Utilization (Leverage) ===

def calculate_utilization(tvl_df: pd.DataFrame, csus: list) -> pd.DataFrame:
    """
    Calculate utilization ratio = borrowed / supplied for each CSU-date.
    """
    # Filter to relevant CSUs
    tvl = tvl_df[tvl_df['csu'].isin(csus)].copy()

    # Calculate utilization
    tvl['utilization'] = tvl['total_borrow_usd'] / tvl['total_supply_usd']

    # Handle edge cases
    tvl['utilization'] = tvl['utilization'].replace([np.inf, -np.inf], np.nan)
    tvl['utilization'] = tvl['utilization'].clip(0, 1)  # Bound to [0, 1]

    return tvl[['date', 'csu', 'utilization', 'total_supply_usd', 'total_borrow_usd']]


# === Volatility (Collateral-Weighted) ===

def calculate_basket_returns(comp_df: pd.DataFrame, price_cache: Dict[str, float]) -> pd.DataFrame:
    """
    Calculate daily collateral basket returns for each CSU.

    R_t = Σ w_{i,t-1} × r_{i,t}

    where r_{i,t} = log(p_{i,t}) - log(p_{i,t-1})
    """
    results = []

    for csu in comp_df['csu'].unique():
        csu_data = comp_df[comp_df['csu'] == csu].copy()
        dates = sorted(csu_data['date'].unique())

        for i, date in enumerate(dates):
            if i == 0:
                continue  # Need previous day for returns

            prev_date = dates[i - 1]

            # Get weights from previous day (w_{i,t-1})
            prev_comp = csu_data[csu_data['date'] == prev_date]
            if prev_comp.empty:
                continue

            # Calculate weighted return
            basket_return = 0.0
            total_weight = 0.0

            for _, row in prev_comp.iterrows():
                symbol = row['symbol']
                weight = row.get('pct_of_total')

                if pd.isna(weight) or weight <= 0:
                    continue

                weight = weight / 100.0  # Convert to decimal

                # Get prices
                price_today_key = f"{date}_{symbol}"
                price_prev_key = f"{prev_date}_{symbol}"

                price_today = price_cache.get(price_today_key)
                price_prev = price_cache.get(price_prev_key)

                if price_today and price_prev and price_today > 0 and price_prev > 0:
                    # Log return
                    log_return = np.log(price_today) - np.log(price_prev)
                    basket_return += weight * log_return
                    total_weight += weight

            # Only record if we have sufficient coverage
            if total_weight > 0.5:  # At least 50% of basket has price data
                results.append({
                    'date': date,
                    'csu': csu,
                    'basket_return': basket_return,
                    'weight_coverage': total_weight,
                })

    return pd.DataFrame(results)


def calculate_rolling_volatility(basket_df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    Calculate rolling standard deviation of basket returns.

    σ_{j,t} = rolling_std(R_t, window=H)
    """
    results = []

    for csu in basket_df['csu'].unique():
        csu_data = basket_df[basket_df['csu'] == csu].sort_values('date').copy()

        if len(csu_data) < window:
            continue

        # Rolling volatility
        csu_data['volatility'] = csu_data['basket_return'].rolling(
            window=window, min_periods=window // 2
        ).std()

        results.append(csu_data[['date', 'csu', 'basket_return', 'volatility']])

    if not results:
        return pd.DataFrame(columns=['date', 'csu', 'basket_return', 'volatility'])

    return pd.concat(results, ignore_index=True)


# === Main Pipeline ===

def prepare_panel_data(volatility_window: int = 14) -> pd.DataFrame:
    """
    Prepare balanced panel with:
    - utilization: Leverage proxy (borrowed/supplied)
    - liquidation: Collateral seized USD
    - volatility: Rolling std of collateral basket returns
    """
    print("Loading data...")
    liq_df = load_liquidation_panel()
    tvl_df = load_tvl_data()
    comp_df = load_collateral_composition()
    price_cache = load_price_cache()

    csus = liq_df['csu'].unique().tolist()
    print(f"  CSUs: {csus}")
    print(f"  Liquidations: {len(liq_df):,} rows")
    print(f"  TVL: {len(tvl_df):,} rows")
    print(f"  Composition: {len(comp_df):,} rows")
    print(f"  Prices: {len(price_cache):,} cached")

    # 1. Utilization (Leverage)
    print("\n[1/3] Calculating utilization (leverage)...")
    util_df = calculate_utilization(tvl_df, csus)
    print(f"  Generated {len(util_df):,} utilization observations")

    # 2. Basket returns
    print("\n[2/3] Calculating collateral basket returns...")
    basket_df = calculate_basket_returns(comp_df, price_cache)
    print(f"  Generated {len(basket_df):,} basket return observations")

    # 3. Rolling volatility
    print(f"\n[3/3] Calculating {volatility_window}-day rolling volatility...")
    vol_df = calculate_rolling_volatility(basket_df, window=volatility_window)
    print(f"  Generated {vol_df['volatility'].notna().sum():,} volatility observations")

    # Merge everything
    print("\nMerging datasets...")

    # Start with liquidation panel (balanced)
    panel = liq_df[['date', 'csu', 'n_liquidations', 'total_collateral_usd', 'total_debt_usd']].copy()

    # Rename liquidation column
    panel = panel.rename(columns={'total_collateral_usd': 'liquidation'})

    # Merge utilization
    panel = panel.merge(
        util_df[['date', 'csu', 'utilization']],
        on=['date', 'csu'],
        how='left'
    )

    # Merge volatility
    panel = panel.merge(
        vol_df[['date', 'csu', 'basket_return', 'volatility']],
        on=['date', 'csu'],
        how='left'
    )

    # Sort
    panel = panel.sort_values(['csu', 'date']).reset_index(drop=True)

    return panel


def main():
    parser = argparse.ArgumentParser(description='Prepare Panel SVAR data')
    parser.add_argument('--window', type=int, default=14,
                       help='Rolling window for volatility calculation (default: 14 days)')
    args = parser.parse_args()

    print("=" * 70)
    print("Preparing Panel SVAR Data")
    print("=" * 70)

    panel = prepare_panel_data(volatility_window=args.window)

    # Summary
    print("\n" + "=" * 70)
    print("Panel Summary")
    print("=" * 70)

    print(f"\nDimensions:")
    print(f"  Members (N): {panel['csu'].nunique()}")
    print(f"  Time periods (T): {panel['date'].nunique()}")
    print(f"  Total observations: {len(panel):,}")

    print(f"\nDate range: {panel['date'].min()} to {panel['date'].max()}")

    print(f"\nVariable coverage:")
    for col in ['liquidation', 'utilization', 'volatility']:
        coverage = panel[col].notna().mean() * 100
        mean_val = panel[col].mean()
        print(f"  {col}: {coverage:.1f}% coverage, mean={mean_val:.4f}")

    print(f"\nBy CSU:")
    for csu in sorted(panel['csu'].unique()):
        csu_data = panel[panel['csu'] == csu]
        liq_sum = csu_data['liquidation'].sum()
        util_mean = csu_data['utilization'].mean()
        vol_mean = csu_data['volatility'].mean()
        print(f"  {csu}:")
        print(f"    Liquidation: ${liq_sum:,.0f}")
        print(f"    Avg utilization: {util_mean:.3f}" if pd.notna(util_mean) else "    Avg utilization: N/A")
        print(f"    Avg volatility: {vol_mean:.4f}" if pd.notna(vol_mean) else "    Avg volatility: N/A")

    # Save
    output_dir = Path('data/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Excel for Panel SVAR
    excel_path = output_dir / 'panel_svar_data.xlsx'
    panel.to_excel(excel_path, sheet_name='panel_data', index=False)
    print(f"\nSaved: {excel_path}")

    # Parquet for Python
    parquet_path = output_dir / 'panel_svar_data.parquet'
    panel.to_parquet(parquet_path, index=False)
    print(f"Saved: {parquet_path}")

    # Sample
    print("\n" + "=" * 70)
    print("Sample Data (days with liquidations)")
    print("=" * 70)
    sample = panel[panel['liquidation'] > 0].head(5)
    sample_display = sample[['date', 'csu', 'liquidation', 'utilization', 'volatility']].copy()
    sample_display['liquidation'] = sample_display['liquidation'].apply(lambda x: f"${x:,.0f}")
    print(sample_display.to_string(index=False))

    # Config for Panel SVAR
    print("\n" + "=" * 70)
    print("Panel SVAR Configuration (for main.py)")
    print("=" * 70)
    print(f"""
# Add to main.py:

excel_path = "panel_svar_data.xlsx"
excel_sheet_name = "panel_data"
td_col = ["date"]
member_col = "csu"

# Variables: {{name: [unit_root_indicator, ...]}}
# 1 = has unit root (will be differenced), 0 = stationary
variables = {{
    'liquidation': [0],  # Collateral seized USD (may need log transform)
    'utilization': [0],  # Leverage ratio (bounded 0-1, stationary)
    'volatility': [0],   # Collateral basket volatility (stationary)
}}

variable_order = ['liquidation', 'utilization', 'volatility']
""")


if __name__ == '__main__':
    main()
