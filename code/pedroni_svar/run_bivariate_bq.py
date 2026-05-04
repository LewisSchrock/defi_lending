#!/usr/bin/env python3
"""
Bivariate BQ Panel SVAR: Cascade vs Mechanical Liquidations

Variables:
  liquidation (I(0)), log_price (I(1))

Identification: Blanchard-Quah (Long-Run)
  Δz = [Δp, liq], ordering: [log_price, liquidation]
  A(1) lower triangular:
    A(1)[0,1] = 0: shock 2 (mechanical) has NO permanent effect on price level
    Only shock 1 (cascade) permanently moves the price level.
    Signs (normalizations):
      A(1)[0,0] > 0 (positive cascade shock → higher price)
      A(1)[1,1] > 0 (positive mechanical shock → more liquidation)

Based on: Pedroni (2013), Econometrics 1(2), 180-206
"""

import sys
import os
import warnings
import copy
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")
warnings.filterwarnings("ignore", category=FutureWarning)

from SVAR import VAR_input, SVAR, VAR_output
from panelSVAR import panelSVAR, Panel_output
from identification import findM


# === Configuration ===

VARIABLE_ORDER = ['log_price', 'liquidation']
VARIABLES = {
    'log_price':   [1, 1],   # I(1) in, cumulate IRFs to recover level
    'liquidation': [0, 0],   # I(0) in, I(0) out
}
SHOCKS = ['Cascade', 'Mechanical']

# BQ identification: A(1) lower triangular
#   Δz = [Δp, liq], A(1)[0,1] = 0: mechanical has NO permanent effect on price
#   Only cascade shock permanently moves the price level.
#   Signs (normalizations only):
#     A(1)[0,0] > 0: positive cascade shock → higher price
#     A(1)[1,1] > 0: positive mechanical shock → more liquidation
SR_CONSTRAINT = np.array([])
LR_CONSTRAINT = np.array([
    ['.', '0'],
    ['.', '.'],
])
SR_SIGN = np.array([])
LR_SIGN = np.array([
    ['+', '.'],
    ['.', '+'],
])

MAXLAGS = 10
NSTEPS = 12
LAGMETHOD = 'bic'

# === CSU Definitions ===

# ALL_CSUS is loaded dynamically from the qualified panel in load_panel().
# Denomination subsamples (Compound V3 isolated markets with stablecoin base).
STABLECOIN_BASE_CSUS = [
    'compound_v3_arb_usdc', 'compound_v3_arb_usdc_e', 'compound_v3_arb_usdt',
    'compound_v3_base_usdc', 'compound_v3_base_usdbc',
    'compound_v3_eth_usdc', 'compound_v3_eth_usds', 'compound_v3_eth_usdt',
]

VOLATILE_BASE_CSUS = [
    'compound_v3_arb_weth', 'compound_v3_base_aero',
    'compound_v3_eth_weth',
]


def load_panel() -> pd.DataFrame:
    """Load qualified panel data from gold-sourced qualified parquet."""
    path = PROJECT_ROOT / 'data' / 'analysis' / 'panel_svar_data_qualified.parquet'
    df = pd.read_parquet(path)

    print(f"  Source: {path}")
    print(f"  Raw qualified panel: {len(df)} obs, {df['csu'].nunique()} CSUs")

    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])

    # Convert log_price (cumulative log return) to price level
    df['log_price'] = np.exp(df['log_price'])

    # Keep only needed columns
    cols = ['date', 'csu'] + VARIABLE_ORDER
    df = df[cols].copy()
    df = df.dropna(subset=VARIABLE_ORDER)

    # Truncate CSUs with long lead-in periods of zero liquidation activity.
    # Start dates chosen just before first observed liquidation event.
    CSU_START_DATES = {
        'aave_v3_binance':          '2025-08-01',
        'venus_core_pool_binance':  '2025-08-01',
        'benqi_lending_avalanche':  '2025-07-01',
        'compound_v3_eth_usds':     '2024-12-01',
    }
    for csu, start in CSU_START_DATES.items():
        mask = (df['csu'] == csu) & (df['date'] < pd.Timestamp(start))
        n_dropped = mask.sum()
        if n_dropped > 0:
            df = df[~mask]
            print(f"  Truncated {csu}: dropped {n_dropped} obs before {start}")

    # Drop CSUs with degenerate IRFs (explosive price response)
    DROP_CSUS = ['layerbank_lending_scroll', 'benqi_lending_avalanche']
    for csu in DROP_CSUS:
        n = (df['csu'] == csu).sum()
        if n > 0:
            df = df[df['csu'] != csu]
            print(f"  Dropped {csu}: degenerate IRF ({n} obs removed)")

    return df


def make_var_input(df: pd.DataFrame) -> VAR_input:
    """Create a VAR_input object for bivariate system."""
    return VAR_input(
        variables=copy.deepcopy(VARIABLES),
        variable_order=VARIABLE_ORDER,
        shocks=SHOCKS,
        td_col=['date'],
        member_col='csu',
        M=None,
        sr_constraint=SR_CONSTRAINT.copy() if SR_CONSTRAINT.size > 0 else SR_CONSTRAINT,
        lr_constraint=LR_CONSTRAINT.copy(),
        sr_sign=SR_SIGN.copy() if SR_SIGN.size > 0 else SR_SIGN,
        lr_sign=LR_SIGN.copy(),
        maxlags=MAXLAGS,
        nsteps=NSTEPS,
        lagmethod=LAGMETHOD,
        bootstrap=False,
        ndraws=2000,
        signif=0.05,
        df=df,
        plot=False,
        savefig_path='',
    )


def parse_panel_output(panel_out: Panel_output, nsteps: int, size: int):
    """Parse Panel_output into structured IRF arrays per member."""
    results = {}
    for member in panel_out.comp_df.index:
        comp_row = panel_out.comp_df.loc[member]
        comm_row = panel_out.comm_df.loc[member]
        idio_row = panel_out.idio_df.loc[member]
        lam_row = panel_out.lambda_df.loc[member]

        if comp_row.isna().all():
            continue

        comp_ir = np.zeros((nsteps + 1, size, size))
        comm_ir = np.zeros((nsteps + 1, size, size))
        idio_ir = np.zeros((nsteps + 1, size, size))

        idx = 0
        for vr in range(size):
            for sk in range(size):
                for lg in range(nsteps + 1):
                    comp_ir[lg, vr, sk] = float(comp_row.iloc[idx])
                    comm_ir[lg, vr, sk] = float(comm_row.iloc[idx])
                    idio_ir[lg, vr, sk] = float(idio_row.iloc[idx])
                    idx += 1

        lam_mat = np.array(lam_row.values, dtype=float).reshape(size, size)

        results[member] = {
            'composite': comp_ir,
            'common': comm_ir,
            'idiosyncratic': idio_ir,
            'lambda': lam_mat,
        }
    return results


def compute_median_irf(member_irfs: dict, irf_type: str = 'composite'):
    arrays = [v[irf_type] for v in member_irfs.values()]
    if not arrays:
        return None
    return np.median(np.stack(arrays, axis=0), axis=0)


def compute_iqr_irfs(member_irfs: dict, irf_type: str = 'composite'):
    """Compute 25th and 75th percentile IRFs."""
    arrays = [v[irf_type] for v in member_irfs.values()]
    if not arrays:
        return None, None
    stacked = np.stack(arrays, axis=0)
    return np.percentile(stacked, 25, axis=0), np.percentile(stacked, 75, axis=0)


def plot_bivariate_irfs(member_irfs, title, save_path, irf_type='composite'):
    """Plot 2x2 IRF grid with individual members in gray and median in blue."""
    size = len(VARIABLE_ORDER)
    median_irf = compute_median_irf(member_irfs, irf_type)
    p25, p75 = compute_iqr_irfs(member_irfs, irf_type)
    if median_irf is None:
        return

    fig, axes = plt.subplots(size, size, figsize=(10, 7), sharex=True)
    var_labels = ['Price Level', 'Liquidation']
    shock_labels = SHOCKS

    for i in range(size):
        for j in range(size):
            ax = axes[i, j]
            steps = np.arange(median_irf.shape[0])

            # Individual members in gray
            for member, data in member_irfs.items():
                ax.plot(steps, data[irf_type][:, i, j], color='gray', alpha=0.2, linewidth=0.6)

            # IQR band
            if p25 is not None:
                ax.fill_between(steps, p25[:, i, j], p75[:, i, j], alpha=0.3, color='steelblue')

            # Median
            ax.plot(steps, median_irf[:, i, j], 'b-', linewidth=2, label='Median')
            ax.axhline(0, color='black', linestyle=':', linewidth=0.5)
            ax.set_title(f'{shock_labels[j]} $\\varepsilon$ \u2192 {var_labels[i]}', fontsize=10)
            ax.set_xlim(0, 12)
            if i == size - 1:
                ax.set_xlabel('Days')
            if j == 0:
                ax.set_ylabel(f'{var_labels[i]} ($\\sigma$)', fontsize=9)

    fig.suptitle(title, fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def plot_comparison_irfs(label_a, irf_a, label_b, irf_b, title, save_path):
    """Plot median IRFs for two subsamples side by side."""
    size = len(VARIABLE_ORDER)
    var_labels = ['Price Level', 'Liquidation']
    shock_labels = SHOCKS

    fig, axes = plt.subplots(size, size, figsize=(10, 7), sharex=True)

    for i in range(size):
        for j in range(size):
            ax = axes[i, j]
            steps = np.arange(irf_a.shape[0])
            ax.plot(steps, irf_a[:, i, j], 'b-', linewidth=1.5, label=label_a)
            ax.plot(steps, irf_b[:, i, j], 'r--', linewidth=1.5, label=label_b)
            ax.axhline(0, color='black', linestyle=':', linewidth=0.5)
            ax.set_title(f'{shock_labels[j]} $\\varepsilon$ \u2192 {var_labels[i]}', fontsize=10)
            ax.set_xlim(0, 12)
            if i == 0 and j == 0:
                ax.legend(fontsize=8)
            if i == size - 1:
                ax.set_xlabel('Days')
            if j == 0:
                ax.set_ylabel(f'{var_labels[i]} ($\\sigma$)', fontsize=9)

    fig.suptitle(title, fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def print_results(label, member_irfs):
    """Print summary statistics for a subsample."""
    median_ir = compute_median_irf(member_irfs, 'composite')
    if median_ir is None:
        print(f"  {label}: No results")
        return

    size = len(VARIABLE_ORDER)
    var_labels = ['Price Level', 'Liquidation']
    shock_labels = SHOCKS

    # IRFs at key horizons
    # Price Level (idx 0): already cumulated by SVAR.py, value at h IS the level effect
    # Liquidation (idx 1): cumulative (sum of point IRFs)
    for h in [1, 5, 10]:
        price_level = median_ir[h, 0, :]
        cum_liq = median_ir[:h+1, 1, :].sum(axis=0)
        print(f"\n  {label} - IRF at h={h}:")
        for j in range(size):
            print(f"    Price Level              <- {shock_labels[j]}: {price_level[j]:.4f}")
            print(f"    Liquidation (cumulative) <- {shock_labels[j]}: {cum_liq[j]:.4f}")

    # Lambda decomposition
    lam_vals = {}
    for var_idx, var in enumerate(VARIABLE_ORDER):
        lambdas = [data['lambda'][var_idx, var_idx] for data in member_irfs.values()]
        lam_vals[var] = lambdas
        print(f"\n  {label} - Lambda ({var}):")
        print(f"    mean = {np.mean(lambdas):.4f}, median = {np.median(lambdas):.4f}")
        print(f"    min = {np.min(lambdas):.4f}, max = {np.max(lambdas):.4f}")

    # FEVD-style: fraction of price variance from cascade shock
    # At h=10, the variance contribution of shock j to variable i is proportional
    # to Σ_{s=0}^{h} A(s)_{i,j}^2
    cascade_price_var = np.sum(median_ir[:11, 0, 0]**2)
    mechanical_price_var = np.sum(median_ir[:11, 0, 1]**2)
    total_price_var = cascade_price_var + mechanical_price_var
    if total_price_var > 0:
        pct_cascade = cascade_price_var / total_price_var * 100
        print(f"\n  {label} - Price Level FEVD at h=10:")
        print(f"    Cascade shock: {pct_cascade:.1f}%")
        print(f"    Mechanical shock: {100-pct_cascade:.1f}%")


def run_panel(label, df, csus, output_dir):
    """Run bivariate BQ Panel SVAR on a set of CSUs."""
    sub_df = df[df['csu'].isin(csus)].copy()
    actual = sorted(sub_df['csu'].unique())
    print(f"\n  {label}: {len(actual)} CSUs, {len(sub_df)} obs")

    var_input = make_var_input(sub_df)
    try:
        panel_out = panelSVAR(var_input)
    except Exception as e:
        print(f"  Panel SVAR failed for {label}: {e}")
        return {}

    member_irfs = parse_panel_output(panel_out, NSTEPS, len(VARIABLE_ORDER))
    print(f"  Successfully estimated {len(member_irfs)}/{len(actual)} members")

    # Plot
    plot_bivariate_irfs(
        member_irfs,
        f'Bivariate BQ: {label} (N={len(member_irfs)})',
        output_dir / f'bivariate_bq_{label.lower().replace(" ", "_")}_irfs.png',
    )

    # Print results
    print_results(label, member_irfs)

    return member_irfs


def main():
    print("=" * 70)
    print("Bivariate BQ Panel SVAR")
    print("Cascade vs Mechanical Liquidation Shocks")
    print("Identification: BQ long-run restriction")
    print(f"Variables: {VARIABLE_ORDER}")
    print(f"Shocks: {SHOCKS}")
    print(f"Lags: BIC (max {MAXLAGS}), IRF steps: {NSTEPS}")
    print("=" * 70)

    df = load_panel()
    print(f"\nLoaded panel: {len(df)} obs, {df['csu'].nunique()} CSUs")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    output_dir = PROJECT_ROOT / 'results' / 'pedroni' / 'bivariate_bq'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Change to script directory so panelSVAR.py can write to ./output/
    original_cwd = os.getcwd()
    os.chdir(Path(__file__).parent)
    os.makedirs('output', exist_ok=True)

    try:
        # 1. Full panel — use all CSUs from the qualified data
        all_csus = sorted(df['csu'].unique())
        print(f"\n{'='*70}")
        print("1. Full Panel")
        print(f"{'='*70}")
        full_irfs = run_panel('Full Panel', df, all_csus, output_dir)

        # 2. Denomination comparison: Stablecoin vs Volatile (CV3 isolated)
        print(f"\n{'='*70}")
        print("2. Denomination Comparison (Compound V3 Isolated Markets)")
        print(f"{'='*70}")
        stable_irfs = run_panel('Stablecoin', df, STABLECOIN_BASE_CSUS, output_dir)
        volatile_irfs = run_panel('Volatile', df, VOLATILE_BASE_CSUS, output_dir)

        # Comparison plot
        median_s = compute_median_irf(stable_irfs, 'composite')
        median_v = compute_median_irf(volatile_irfs, 'composite')
        if median_s is not None and median_v is not None:
            plot_comparison_irfs(
                'Stablecoin', median_s, 'Volatile', median_v,
                'Denomination: Stablecoin vs Volatile Base',
                output_dir / 'bivariate_bq_denomination_comparison.png',
            )

        # 3. Save summary CSV
        summary_rows = []
        for label, irfs in [('Full Panel', full_irfs), ('Stablecoin', stable_irfs), ('Volatile', volatile_irfs)]:
            median_ir = compute_median_irf(irfs, 'composite')
            if median_ir is None:
                continue
            for h in [1, 5, 10]:
                for j, shock in enumerate(SHOCKS):
                    summary_rows.append({
                        'subsample': label,
                        'horizon': h,
                        'response': 'log_price',
                        'shock': shock,
                        'value': median_ir[h, 0, j],
                        'type': 'level',
                    })
                    summary_rows.append({
                        'subsample': label,
                        'horizon': h,
                        'response': 'liquidation',
                        'shock': shock,
                        'value': median_ir[:h+1, 1, j].sum(),
                        'type': 'cumulative',
                    })
        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_csv(output_dir / 'bivariate_bq_summary.csv', index=False)
        print(f"\n  Saved summary: bivariate_bq_summary.csv")

    finally:
        os.chdir(original_cwd)

    print("\n" + "=" * 70)
    print("Bivariate BQ analysis complete.")
    print(f"Results: {output_dir}")
    print("=" * 70)


if __name__ == '__main__':
    main()
