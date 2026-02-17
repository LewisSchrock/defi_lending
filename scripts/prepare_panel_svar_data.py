#!/usr/bin/env python3
"""
Prepare Data for Pedroni Panel SVAR

Constructs panel data with economically meaningful variables:
1. Leverage (Utilization Ratio) = Borrowed / Supplied
2. Liquidation = log(1 + total_collateral_usd) - log-transformed USD value of collateral seized per day
3. Volatility = Collateral-weighted rolling std dev of basket returns

Utilization and volatility are sourced from the vol_util_panel (computed
from bronze TVL data in build_volatility_panel.py). Liquidation comes from
the gold liquidation panel. CSU names are normalized across data sources.

See data/analysis/README.md for economic definitions.

Output: Excel + Parquet files ready for Panel SVAR analysis

Usage:
    python scripts/prepare_panel_svar_data.py
    python scripts/prepare_panel_svar_data.py --start-date 2024-07-01
    python scripts/prepare_panel_svar_data.py --min-coverage 0.70
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import pandas as pd
import numpy as np


# === CSU Name Normalization ===
# Maps non-canonical names to canonical names.
# Convention: {protocol}_{chain}_{version}_{market}
#   - Use actual protocol names for forks (benqi, venus, sonne, mendi)
#   - Use RPC chain names (binance not bsc, gnosis not xdai)

CSU_ALIASES = {
    # Liquidation panel uses these → canonical
    'aave_v3_bsc': 'aave_v3_binance',
    'compound_v2_avalanche': 'benqi_lending_avalanche',
    'compound_v2_bsc': 'venus_core_pool_binance',
    'compound_v2_optimism': 'sonne_lending_optimism',
    'compound_v2_linea': 'mendi_lending_linea',
    'compound_v2_polygon': 'keom_lending_polygon',
    'aave_v3_ink': 'tydro_ink',
    # Vol/util panel uses this → canonical
    'aave_v3_xdai': 'aave_v3_gnosis',
}


def normalize_csu(name: str) -> str:
    """Map a CSU name to its canonical form."""
    return CSU_ALIASES.get(name, name)


# === Data Loading ===

def load_liquidation_panel() -> pd.DataFrame:
    """Load gold liquidation panel with normalized CSU names."""
    path = Path('data/gold/liquidations/all_chains/daily_panel.parquet')
    df = pd.read_parquet(path)
    df['csu'] = df['csu'].map(normalize_csu)
    return df


def load_vol_util_panel() -> pd.DataFrame:
    """Load utilization + volatility panel (from build_volatility_panel.py)."""
    path = Path('data/analysis/vol_util_panel.parquet')
    df = pd.read_parquet(path)
    df['csu'] = df['csu'].map(normalize_csu)
    return df


# === Main Pipeline ===

def prepare_panel_data(start_date: str = '2024-07-01',
                       min_coverage: float = 0.70) -> pd.DataFrame:
    """
    Prepare balanced panel with:
    - liquidation: log(1 + total_collateral_usd)
    - utilization: Leverage proxy (borrowed/supplied) from bronze TVL
    - volatility: Rolling std of collateral basket returns from bronze TVL
    """
    print("Loading data...")
    liq_df = load_liquidation_panel()
    vu_df = load_vol_util_panel()

    liq_csus = set(liq_df['csu'].unique())
    vu_csus = set(vu_df['csu'].unique())
    matched_csus = sorted(liq_csus & vu_csus)

    print(f"  Liquidation panel: {len(liq_csus)} CSUs, {len(liq_df):,} rows")
    print(f"  Vol/util panel:    {len(vu_csus)} CSUs, {len(vu_df):,} rows")
    print(f"  Matched CSUs:      {len(matched_csus)}")

    unmatched_liq = sorted(liq_csus - vu_csus)
    if unmatched_liq:
        print(f"  No vol/util data:  {unmatched_liq}")

    # Build panel: start with liquidation data for matched CSUs
    panel = liq_df[liq_df['csu'].isin(matched_csus)][
        ['date', 'csu', 'n_liquidations', 'total_collateral_usd', 'total_debt_usd']
    ].copy()

    # Log-transformed liquidation variable
    panel['liquidation'] = np.log1p(panel['total_collateral_usd'])

    # Merge utilization + volatility from vol_util panel
    panel = panel.merge(
        vu_df[['date', 'csu', 'utilization', 'volatility', 'basket_return']],
        on=['date', 'csu'],
        how='left'
    )

    # Apply T-trimming
    if start_date:
        before = len(panel)
        panel = panel[panel['date'] >= start_date].copy()
        print(f"\n  T-trimming: start={start_date}, dropped {before - len(panel):,} rows")

    panel = panel.sort_values(['csu', 'date']).reset_index(drop=True)

    # Filter CSUs by coverage
    print(f"\nFiltering CSUs (min coverage={min_coverage:.0%} for all 3 vars)...")
    qualified = []
    for csu in sorted(panel['csu'].unique()):
        cd = panel[panel['csu'] == csu]
        liq_pct = cd['liquidation'].notna().mean()
        util_pct = cd['utilization'].notna().mean()
        vol_pct = cd['volatility'].notna().mean()
        all3_pct = ((cd['liquidation'].notna()) &
                    (cd['utilization'].notna()) &
                    (cd['volatility'].notna())).mean()

        if all3_pct >= min_coverage:
            qualified.append(csu)
            print(f"  QUALIFIED {csu}: all3={all3_pct:.0%} "
                  f"(liq={liq_pct:.0%}, util={util_pct:.0%}, vol={vol_pct:.0%})")
        else:
            print(f"  DROPPED   {csu}: all3={all3_pct:.0%} "
                  f"(liq={liq_pct:.0%}, util={util_pct:.0%}, vol={vol_pct:.0%})")

    qualified_panel = panel[panel['csu'].isin(qualified)].copy()

    return panel, qualified_panel


def main():
    parser = argparse.ArgumentParser(description='Prepare Panel SVAR data')
    parser.add_argument('--start-date', type=str, default='2024-07-01',
                        help='Start date for T-trimming (default: 2024-07-01)')
    parser.add_argument('--min-coverage', type=float, default=0.70,
                        help='Min coverage for all 3 vars to qualify (default: 0.70)')
    args = parser.parse_args()

    print("=" * 70)
    print("Preparing Panel SVAR Data")
    print("=" * 70)

    panel, qualified = prepare_panel_data(
        start_date=args.start_date,
        min_coverage=args.min_coverage,
    )

    # Summary
    print("\n" + "=" * 70)
    print("Full Panel Summary")
    print("=" * 70)
    print(f"  Members (N): {panel['csu'].nunique()}")
    print(f"  Time periods (T): {panel['date'].nunique()}")
    print(f"  Total observations: {len(panel):,}")
    print(f"  Date range: {panel['date'].min()} to {panel['date'].max()}")

    print(f"\n  Variable coverage (full panel):")
    for col in ['liquidation', 'utilization', 'volatility']:
        coverage = panel[col].notna().mean() * 100
        mean_val = panel[col].mean()
        print(f"    {col}: {coverage:.1f}% coverage, mean={mean_val:.4f}")

    print("\n" + "=" * 70)
    print("Qualified Panel Summary")
    print("=" * 70)
    print(f"  Members (N): {qualified['csu'].nunique()}")
    print(f"  Time periods (T): {qualified['date'].nunique()}")
    print(f"  Total observations: {len(qualified):,}")
    if not qualified.empty:
        print(f"  Date range: {qualified['date'].min()} to {qualified['date'].max()}")

    print(f"\n  Variable coverage (qualified):")
    for col in ['liquidation', 'utilization', 'volatility']:
        coverage = qualified[col].notna().mean() * 100
        mean_val = qualified[col].mean()
        print(f"    {col}: {coverage:.1f}% coverage, mean={mean_val:.4f}")

    print(f"\n  By CSU:")
    for csu in sorted(qualified['csu'].unique()):
        cd = qualified[qualified['csu'] == csu]
        liq_days = (cd['total_collateral_usd'] > 0).sum()
        util_mean = cd['utilization'].mean()
        vol_mean = cd['volatility'].mean()
        print(f"    {csu}: T={len(cd)}, "
              f"liq_events={liq_days}, "
              f"util={util_mean:.3f}, "
              f"vol={vol_mean:.4f}")

    # Save
    output_dir = Path('data/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full panel
    panel.to_parquet(output_dir / 'panel_svar_data.parquet', index=False)
    panel.to_excel(output_dir / 'panel_svar_data.xlsx', sheet_name='panel_data', index=False)
    print(f"\nSaved full panel: {output_dir / 'panel_svar_data.parquet'}")

    # Qualified panel
    qualified.to_parquet(output_dir / 'panel_svar_data_qualified.parquet', index=False)
    qualified.to_excel(output_dir / 'panel_svar_data_qualified.xlsx',
                       sheet_name='panel_data', index=False)
    print(f"Saved qualified panel: {output_dir / 'panel_svar_data_qualified.parquet'}")

    # Config
    print("\n" + "=" * 70)
    print("Panel SVAR Configuration (for main.py)")
    print("=" * 70)
    print(f"""
excel_path = "panel_svar_data_qualified.xlsx"
excel_sheet_name = "panel_data"
td_col = ["date"]
member_col = "csu"

variables = {{
    'liquidation': [0],
    'utilization': [0],
    'volatility': [0],
}}

variable_order = ['liquidation', 'utilization', 'volatility']
""")


if __name__ == '__main__':
    main()
