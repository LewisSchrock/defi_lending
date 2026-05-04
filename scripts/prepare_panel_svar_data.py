#!/usr/bin/env python3
"""
Prepare Data for Pedroni Panel SVAR

Constructs panel data with economically meaningful variables:
1. Leverage (Utilization Ratio) = Borrowed / Supplied
2. Liquidation = log(1 + total_collateral_usd) - log-transformed USD value of collateral seized per day
3. Volatility = Collateral-weighted rolling std dev of basket returns

Utilization and volatility are sourced from the collateral_basket panel (computed
from bronze TVL data in build_volatility_panel.py). Liquidation comes from
the gold liquidation panel. CSU names are normalized across data sources.

The panel is UNBALANCED: each CSU is trimmed to its own effective date range
(first to last date with vol/util data). The Pedroni (2013) framework estimates
separate VARs per CSU, so different members can have different T.

See data/analysis/README.md for economic definitions.

Output: Excel + Parquet files ready for Panel SVAR analysis

Usage:
    python scripts/prepare_panel_svar_data.py
    python scripts/prepare_panel_svar_data.py --min-obs 200
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
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

# === CSU Exclusions ===
# CSUs excluded from the qualified SVAR panel due to degenerate variable behavior.
# These units produce constant or near-constant series that prevent SVAR estimation.
CSU_EXCLUSIONS = {
    'sonne_lending_optimism',   # Post-exploit: utilization=1.0, liquidation=0 throughout
    'gearbox_ethereum',         # Credit Account architecture: utilization=0, liquidation=0 throughout
    'compound_v3_base_weth',    # Zero liquidation events across entire sample (degenerate)
    'ironbank_ethereum',        # Zero liquidation events across entire sample (degenerate)
    'ironbank_fantom',          # Zero liquidation events across entire sample (degenerate)
}


def normalize_csu(name: str) -> str:
    """Map a CSU name to its canonical form."""
    return CSU_ALIASES.get(name, name)


# === Data Loading ===

GOLD_LIQUIDATION_PANEL = Path('data/gold/liquidations/all_chains/daily_panel.parquet')


def load_liquidation_panel() -> pd.DataFrame:
    """Load the canonical gold liquidation panel with normalized CSU names."""
    df = pd.read_parquet(GOLD_LIQUIDATION_PANEL)
    df['csu'] = df['csu'].map(normalize_csu)

    # Deduplicate within panel (name normalization can merge CSUs)
    df = df.groupby(['date', 'csu'], as_index=False).agg({
        col: 'sum' for col in ['n_liquidations', 'total_collateral_usd', 'total_debt_usd']
        if col in df.columns
    })

    # Supplement with bronze CV3 data for CSUs not already in gold
    bronze_supplement = _load_bronze_cv3_supplement(existing_csus=set(df['csu'].unique()))
    if not bronze_supplement.empty:
        df = pd.concat([df, bronze_supplement], ignore_index=True)
        print(f"  After bronze supplement: {df['csu'].nunique()} CSUs")

    return df


def _load_bronze_cv3_supplement(existing_csus: set) -> pd.DataFrame:
    """Load Compound V3 events from bronze _cv3 directories not in gold.

    Converts usd_value_raw / 1e8 to USD for AbsorbCollateral and AbsorbDebt
    events, then aggregates to daily panels matching gold schema.
    """
    bronze_root = Path('data/bronze/liquidations')
    cv3_dirs = sorted(bronze_root.glob('*_cv3'))

    if not cv3_dirs:
        return pd.DataFrame()

    all_events = []
    for cv3_dir in cv3_dirs:
        events_file = cv3_dir / 'events.jsonl'
        if not events_file.exists():
            continue
        with open(events_file) as f:
            for line in f:
                try:
                    all_events.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

    if not all_events:
        return pd.DataFrame()

    df = pd.DataFrame(all_events)
    df['csu'] = df['csu'].map(normalize_csu)

    # Only keep CSUs not already in gold
    new_csus = set(df['csu'].unique()) - existing_csus
    if not new_csus:
        return pd.DataFrame()

    df = df[df['csu'].isin(new_csus)].copy()

    # Convert usd_value_raw to USD (Compound V3 uses 1e8 scaling)
    df['usd_value'] = pd.to_numeric(df.get('usd_value_raw', 0), errors='coerce').fillna(0) / 1e8

    # Separate collateral and debt events
    coll = df[df['event_name'] == 'AbsorbCollateral'].copy()
    debt = df[df['event_name'] == 'AbsorbDebt'].copy()

    # Aggregate collateral USD by (date, csu)
    coll_daily = coll.groupby(['date', 'csu']).agg(
        total_collateral_usd=('usd_value', 'sum'),
    ).reset_index() if not coll.empty else pd.DataFrame(columns=['date', 'csu', 'total_collateral_usd'])

    # Aggregate debt USD by (date, csu)
    debt_daily = debt.groupby(['date', 'csu']).agg(
        total_debt_usd=('usd_value', 'sum'),
    ).reset_index() if not debt.empty else pd.DataFrame(columns=['date', 'csu', 'total_debt_usd'])

    # Count unique liquidations by (tx_hash, borrower) pairs per (date, csu)
    liq_counts = df.drop_duplicates(subset=['tx_hash', 'borrower', 'date', 'csu']).groupby(
        ['date', 'csu']
    ).size().reset_index(name='n_liquidations')

    # Merge all aggregates
    daily = liq_counts.merge(coll_daily, on=['date', 'csu'], how='left')
    daily = daily.merge(debt_daily, on=['date', 'csu'], how='left')
    daily['total_collateral_usd'] = daily['total_collateral_usd'].fillna(0)
    daily['total_debt_usd'] = daily['total_debt_usd'].fillna(0)

    # Create balanced panel with continuous date range (fill missing dates with 0)
    min_date = df['date'].min()
    max_date = df['date'].max()
    all_dates = [d.strftime('%Y-%m-%d') for d in pd.date_range(min_date, max_date, freq='D')]
    all_new_csus = sorted(new_csus)
    full_idx = pd.MultiIndex.from_product([all_dates, all_new_csus], names=['date', 'csu'])
    balanced = pd.DataFrame(index=full_idx).reset_index()
    balanced = balanced.merge(daily, on=['date', 'csu'], how='left')
    balanced['n_liquidations'] = balanced['n_liquidations'].fillna(0).astype(int)
    balanced['total_collateral_usd'] = balanced['total_collateral_usd'].fillna(0)
    balanced['total_debt_usd'] = balanced['total_debt_usd'].fillna(0)

    print(f"  Bronze CV3 supplement: {len(new_csus)} new CSUs "
          f"({', '.join(all_new_csus)}), "
          f"{int(daily['n_liquidations'].sum()):,} total events")

    return balanced


def load_vol_util_panel() -> pd.DataFrame:
    """Load collateral-basket panel (basket return, volatility, utilization, TVL)
    produced by build_volatility_panel.py."""
    path = Path('data/analysis/collateral_basket.parquet')
    df = pd.read_parquet(path)
    df['csu'] = df['csu'].map(normalize_csu)
    return df


# === Main Pipeline ===

def prepare_panel_data(min_obs: int = 200) -> pd.DataFrame:
    """
    Prepare unbalanced panel with:
    - liquidation: log(1 + total_collateral_usd)
    - utilization: Leverage proxy (borrowed/supplied) from bronze TVL
    - volatility: Rolling std of collateral basket returns from bronze TVL

    Each CSU is trimmed to its own effective date range (first to last date
    with vol/util data). The Pedroni framework estimates separate VARs per
    member, so different CSUs can have different T.

    CSUs are qualified based on minimum complete observations (all 3 vars
    non-null), not coverage percentage of a fixed window.
    """
    print("Loading data...")
    liq_df = load_liquidation_panel()
    vu_df = load_vol_util_panel()

    liq_csus = set(liq_df['csu'].unique())
    vu_csus = set(vu_df['csu'].unique())
    matched_csus = sorted((liq_csus & vu_csus) - CSU_EXCLUSIONS)

    excluded_present = sorted((liq_csus | vu_csus) & CSU_EXCLUSIONS)
    if excluded_present:
        print(f"  Excluded CSUs:     {excluded_present}")

    print(f"  Liquidation panel: {len(liq_csus)} CSUs, {len(liq_df):,} rows")
    print(f"  Vol/util panel:    {len(vu_csus)} CSUs, {len(vu_df):,} rows")
    print(f"  Matched CSUs:      {len(matched_csus)}")

    unmatched_liq = sorted(liq_csus - vu_csus - CSU_EXCLUSIONS)
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
        vu_df[['date', 'csu', 'utilization', 'volatility', 'basket_return', 'log_price']],
        on=['date', 'csu'],
        how='left'
    )

    panel = panel.sort_values(['csu', 'date']).reset_index(drop=True)

    # Per-CSU trimming: trim each CSU to its effective date range
    # (first to last date where vol/util data exists)
    print("\nPer-CSU effective range trimming...")
    trimmed_parts = []
    before_total = len(panel)
    for csu in sorted(panel['csu'].unique()):
        cd = panel[panel['csu'] == csu]
        has_vu = cd['utilization'].notna() | cd['volatility'].notna()
        if not has_vu.any():
            continue
        first_vu = cd.loc[has_vu, 'date'].min()
        last_vu = cd.loc[has_vu, 'date'].max()
        trimmed = cd[(cd['date'] >= first_vu) & (cd['date'] <= last_vu)]
        trimmed_parts.append(trimmed)

    panel = pd.concat(trimmed_parts, ignore_index=True)
    dropped = before_total - len(panel)
    if dropped > 0:
        print(f"  Dropped {dropped:,} rows outside per-CSU effective ranges")

    # Filter CSUs by minimum complete observations
    print(f"\nFiltering CSUs (min {min_obs} complete observations)...")
    qualified = []
    for csu in sorted(panel['csu'].unique()):
        cd = panel[panel['csu'] == csu]
        complete = ((cd['liquidation'].notna()) &
                    (cd['utilization'].notna()) &
                    (cd['volatility'].notna())).sum()
        total = len(cd)
        date_range = f"{cd['date'].min()} to {cd['date'].max()}"

        if complete >= min_obs:
            qualified.append(csu)
            print(f"  QUALIFIED {csu}: T={total}, complete={complete}, "
                  f"range={date_range}")
        else:
            print(f"  DROPPED   {csu}: T={total}, complete={complete}, "
                  f"range={date_range}")

    qualified_panel = panel[panel['csu'].isin(qualified)].copy()

    return panel, qualified_panel


def main():
    parser = argparse.ArgumentParser(description='Prepare Panel SVAR data')
    parser.add_argument('--min-obs', type=int, default=200,
                        help='Min complete observations (all 3 vars) to qualify (default: 200)')
    args = parser.parse_args()

    print("=" * 70)
    print("Preparing Panel SVAR Data (unbalanced panel)")
    print("=" * 70)

    panel, qualified = prepare_panel_data(min_obs=args.min_obs)

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
        complete = ((cd['liquidation'].notna()) &
                    (cd['utilization'].notna()) &
                    (cd['volatility'].notna())).sum()
        liq_days = (cd['total_collateral_usd'] > 0).sum()
        util_mean = cd['utilization'].mean()
        vol_mean = cd['volatility'].mean()
        print(f"    {csu}: T={len(cd)}, complete={complete}, "
              f"range={cd['date'].min()} to {cd['date'].max()}, "
              f"liq_events={liq_days}, "
              f"util={util_mean:.3f}, vol={vol_mean:.4f}")

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
