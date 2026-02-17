#!/usr/bin/env python3
"""
Run Pedroni Panel SVAR for Thesis Analyses

Three comparisons using heterogeneous member-specific SVARs:
  1. Architecture: Pooled (Aave-style) vs Isolated (Compound V3)
  2. Mechanism: Aave-Style (Instant) vs Compound V3 (Absorb)
  3. Chain: Ethereum (L1) vs Base (L2)

Variables (all stationary):
  utilization → liquidation → volatility  (Cholesky ordering)

Based on: Pedroni (2013), Econometrics 1(2), 180-206
"""

import sys
import os
import warnings
from pathlib import Path

# Add project root and this directory to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import copy

warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")
warnings.filterwarnings("ignore", category=FutureWarning)

from SVAR import VAR_input, SVAR, VAR_output
from panelSVAR import panelSVAR, Panel_output
from identification import findM


# === Configuration ===

VARIABLE_ORDER = ['utilization', 'liquidation', 'volatility']
VARIABLES = {
    'utilization': [0, 0],   # stationary in, stationary out
    'liquidation': [0, 0],
    'volatility':  [0, 0],
}
SHOCKS = ['Utilization', 'Liquidation', 'Volatility']

# Cholesky: lower-triangular M → zeros in upper triangle of sr_constraint
SR_CONSTRAINT = np.array([
    ['.', '0', '0'],
    ['.', '.', '0'],
    ['.', '.', '.'],
])
SR_SIGN = np.array([
    ['+', '.', '.'],
    ['.', '+', '.'],
    ['.', '.', '+'],
])

MAXLAGS = 10
NSTEPS = 20
LAGMETHOD = 'bic'

# Subsample definitions
AAVE_STYLE_CSUS = ['aave_v3_ethereum', 'aave_v3_base', 'moonwell_lending_base', 'sparklend_ethereum']
COMPOUND_V3_CSUS = [
    'compound_v3_eth_usdc', 'compound_v3_eth_usdt', 'compound_v3_eth_usds',
    'compound_v3_eth_weth', 'compound_v3_eth_wsteth',
    'compound_v3_base_usdc', 'compound_v3_base_weth', 'compound_v3_base_aero',
]
ETHEREUM_CSUS = [
    'aave_v3_ethereum', 'compound_v3_eth_usdc', 'compound_v3_eth_usdt',
    'compound_v3_eth_usds', 'compound_v3_eth_weth', 'compound_v3_eth_wsteth',
    'sparklend_ethereum',
]
BASE_CSUS = [
    'aave_v3_base', 'compound_v3_base_usdc', 'compound_v3_base_weth',
    'compound_v3_base_aero', 'moonwell_lending_base',
]


def load_panel() -> pd.DataFrame:
    """Load gold panel data and prepare for Pedroni SVAR."""
    path = PROJECT_ROOT / 'data' / 'gold' / 'panel_base_eth' / 'gold_panel_base_eth.parquet'
    df = pd.read_parquet(path)

    # Use log1p(collateral) as liquidation variable
    df['liquidation'] = df['log_collateral_usd']

    # Keep only needed columns
    cols = ['date', 'csu'] + VARIABLE_ORDER
    df = df[cols].copy()

    # Drop rows with NaN in any variable
    df = df.dropna(subset=VARIABLE_ORDER)

    return df


def make_var_input(df: pd.DataFrame) -> VAR_input:
    """Create a VAR_input object from a panel DataFrame."""
    return VAR_input(
        variables=copy.deepcopy(VARIABLES),
        variable_order=VARIABLE_ORDER,
        shocks=SHOCKS,
        td_col=['date'],
        member_col='csu',
        M=None,
        sr_constraint=SR_CONSTRAINT.copy(),
        lr_constraint=np.array([]),
        sr_sign=SR_SIGN.copy(),
        lr_sign=np.array([]),
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


def parse_panel_output(panel_out: Panel_output, nsteps: int, size: int, variable_order: list, shocks: list):
    """Parse Panel_output DataFrames into structured IRF arrays per member.

    Returns dict: member -> {
        'composite': np.array (nsteps+1, size, size),
        'common': ...,
        'idiosyncratic': ...,
        'lambda': np.array (size, size),
    }
    """
    results = {}
    for member in panel_out.comp_df.index:
        comp_row = panel_out.comp_df.loc[member]
        comm_row = panel_out.comm_df.loc[member]
        idio_row = panel_out.idio_df.loc[member]
        lam_row = panel_out.lambda_df.loc[member]

        if comp_row.isna().all():
            continue

        # Unflatten: stored as var×shock×lag (var and shock are 1-indexed)
        # Format: IR{vr}{sk}_{lg}, with lag as innermost
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
    """Compute median IRF across members."""
    arrays = [v[irf_type] for v in member_irfs.values()]
    if not arrays:
        return None
    stacked = np.stack(arrays, axis=0)
    return np.median(stacked, axis=0)


def compute_mean_irf(member_irfs: dict, irf_type: str = 'composite'):
    """Compute mean IRF across members."""
    arrays = [v[irf_type] for v in member_irfs.values()]
    if not arrays:
        return None
    stacked = np.stack(arrays, axis=0)
    return np.mean(stacked, axis=0)


def plot_comparison_irfs(label_a, irf_a, label_b, irf_b, variable_order, shocks, title, save_path):
    """Plot median composite IRFs for two subsamples side by side."""
    size = len(variable_order)
    fig, axes = plt.subplots(size, size, figsize=(5 * size, 3.5 * size), sharex=True)

    for i, var in enumerate(variable_order):
        for j, shock in enumerate(shocks):
            ax = axes[i, j]
            steps = np.arange(irf_a.shape[0])
            ax.plot(steps, irf_a[:, i, j], 'b-', linewidth=1.5, label=label_a)
            ax.plot(steps, irf_b[:, i, j], 'r--', linewidth=1.5, label=label_b)
            ax.axhline(0, color='black', linestyle=':', linewidth=0.5)
            ax.set_title(f'{var} ← {shock}', fontsize=10)
            if i == 0 and j == 0:
                ax.legend(fontsize=8)

    fig.suptitle(title, fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def plot_member_irfs(member_irfs, variable_order, shocks, title, save_path, irf_type='composite'):
    """Plot individual member IRFs overlaid, with median highlighted."""
    size = len(variable_order)
    median_irf = compute_median_irf(member_irfs, irf_type)
    if median_irf is None:
        return

    fig, axes = plt.subplots(size, size, figsize=(5 * size, 3.5 * size), sharex=True)

    for i, var in enumerate(variable_order):
        for j, shock in enumerate(shocks):
            ax = axes[i, j]
            steps = np.arange(median_irf.shape[0])

            # Individual members in gray
            for member, data in member_irfs.items():
                ax.plot(steps, data[irf_type][:, i, j], color='gray', alpha=0.3, linewidth=0.8)

            # Median in blue
            ax.plot(steps, median_irf[:, i, j], 'b-', linewidth=2, label='Median')
            ax.axhline(0, color='black', linestyle=':', linewidth=0.5)
            ax.set_title(f'{var} ← {shock}', fontsize=10)
            if i == 0 and j == 0:
                ax.legend(fontsize=8)

    fig.suptitle(title, fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def irf_to_dataframe(member_irfs, variable_order, shocks, irf_type='composite'):
    """Convert member IRFs to a tidy DataFrame."""
    rows = []
    for member, data in member_irfs.items():
        ir = data[irf_type]
        for lg in range(ir.shape[0]):
            for i, var in enumerate(variable_order):
                for j, shock in enumerate(shocks):
                    rows.append({
                        'member': member,
                        'step': lg,
                        'response': var,
                        'shock': shock,
                        'value': ir[lg, i, j],
                    })
    return pd.DataFrame(rows)


def lambda_to_dataframe(member_irfs, variable_order):
    """Convert Lambda matrices to DataFrame."""
    rows = []
    for member, data in member_irfs.items():
        lam = data['lambda']
        for i, var in enumerate(variable_order):
            rows.append({
                'member': member,
                'variable': var,
                'lambda': lam[i, i],  # diagonal
            })
    return pd.DataFrame(rows)


def run_comparison(name: str, df: pd.DataFrame, csus_a: list, label_a: str,
                   csus_b: list, label_b: str, output_dir: Path):
    """Run Pedroni Panel SVAR on two subsamples and compare."""
    print(f"\n{'='*70}")
    print(f"Comparison: {name}")
    print(f"  {label_a}: {len(csus_a)} CSUs")
    print(f"  {label_b}: {len(csus_b)} CSUs")
    print(f"{'='*70}")

    # Ensure output dir for panelSVAR.py (it writes to ./output/)
    os.makedirs('output', exist_ok=True)

    results = {}
    for label, csus in [(label_a, csus_a), (label_b, csus_b)]:
        print(f"\n--- Running Pedroni SVAR: {label} ---")
        sub_df = df[df['csu'].isin(csus)].copy()
        print(f"  Observations: {len(sub_df)}, Members: {sub_df['csu'].nunique()}")

        var_input = make_var_input(sub_df)
        panel_out = panelSVAR(var_input)

        member_irfs = parse_panel_output(panel_out, NSTEPS, len(VARIABLE_ORDER), VARIABLE_ORDER, SHOCKS)
        print(f"  Successfully estimated {len(member_irfs)}/{len(csus)} members")

        results[label] = {
            'panel_out': panel_out,
            'member_irfs': member_irfs,
        }

        # Plot individual member IRFs
        plot_member_irfs(
            member_irfs, VARIABLE_ORDER, SHOCKS,
            f'{name}: {label} - Member Composite IRFs',
            output_dir / f'pedroni_{name.lower().replace(" ", "_")}_{label.lower().replace(" ", "_")}_members.png',
        )

    # Comparison plot: median composite IRFs
    median_a = compute_median_irf(results[label_a]['member_irfs'], 'composite')
    median_b = compute_median_irf(results[label_b]['member_irfs'], 'composite')

    if median_a is not None and median_b is not None:
        plot_comparison_irfs(
            label_a, median_a, label_b, median_b,
            VARIABLE_ORDER, SHOCKS,
            f'{name}: Median Composite IRFs',
            output_dir / f'pedroni_{name.lower().replace(" ", "_")}_comparison.png',
        )

    # Save IRF data
    for label in [label_a, label_b]:
        irfs_df = irf_to_dataframe(results[label]['member_irfs'], VARIABLE_ORDER, SHOCKS, 'composite')
        fname = f'pedroni_{name.lower().replace(" ", "_")}_{label.lower().replace(" ", "_")}_irfs.csv'
        irfs_df.to_csv(output_dir / fname, index=False)
        print(f"  Saved: {fname}")

    # Save Lambda
    for label in [label_a, label_b]:
        lam_df = lambda_to_dataframe(results[label]['member_irfs'], VARIABLE_ORDER)
        fname = f'pedroni_{name.lower().replace(" ", "_")}_{label.lower().replace(" ", "_")}_lambda.csv'
        lam_df.to_csv(output_dir / fname, index=False)
        print(f"  Saved: {fname}")

    # Summary table: cumulative IRF at step 10 and 20
    print(f"\n--- Cumulative IRF Summary (Median across members) ---")
    summary_rows = []
    for label in [label_a, label_b]:
        median_ir = compute_median_irf(results[label]['member_irfs'], 'composite')
        if median_ir is None:
            continue
        for horizon in [5, 10, 20]:
            cum_ir = median_ir[:horizon+1].sum(axis=0)
            for i, var in enumerate(VARIABLE_ORDER):
                for j, shock in enumerate(SHOCKS):
                    summary_rows.append({
                        'subsample': label,
                        'horizon': horizon,
                        'response': var,
                        'shock': shock,
                        'cumulative_irf': cum_ir[i, j],
                    })
    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_dir / f'pedroni_{name.lower().replace(" ", "_")}_summary.csv'
    summary_df.to_csv(summary_path, index=False)
    print(f"  Saved: {summary_path.name}")

    # Print key results
    for label in [label_a, label_b]:
        median_ir = compute_median_irf(results[label]['member_irfs'], 'composite')
        if median_ir is None:
            continue
        cum10 = median_ir[:11].sum(axis=0)
        print(f"\n  {label} - Cumulative IRF at h=10:")
        for i, var in enumerate(VARIABLE_ORDER):
            for j, shock in enumerate(SHOCKS):
                print(f"    {var} ← {shock}: {cum10[i,j]:.6f}")

    # Common vs idiosyncratic decomposition summary
    print(f"\n--- Lambda Decomposition (diagonal elements) ---")
    for label in [label_a, label_b]:
        lam_df = lambda_to_dataframe(results[label]['member_irfs'], VARIABLE_ORDER)
        if len(lam_df) == 0:
            continue
        print(f"\n  {label}:")
        for var in VARIABLE_ORDER:
            vals = lam_df[lam_df['variable'] == var]['lambda']
            print(f"    {var}: mean λ = {vals.mean():.4f}, median = {vals.median():.4f}")

    return results


def main():
    print("=" * 70)
    print("Pedroni Panel SVAR - Thesis Analysis")
    print("Methodology: Pedroni (2013)")
    print("Variables: utilization → liquidation → volatility (Cholesky)")
    print(f"Lags: BIC (max {MAXLAGS}), IRF steps: {NSTEPS}")
    print("=" * 70)

    # Load data
    df = load_panel()
    print(f"\nLoaded panel: {len(df)} obs, {df['csu'].nunique()} CSUs")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    # Output directory
    output_dir = PROJECT_ROOT / 'results' / 'pedroni'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Change to script directory so panelSVAR.py can write to ./output/
    original_cwd = os.getcwd()
    os.chdir(Path(__file__).parent)
    os.makedirs('output', exist_ok=True)

    try:
        # 1. Mechanism comparison
        mech_results = run_comparison(
            'Mechanism', df,
            AAVE_STYLE_CSUS, 'Aave-Style',
            COMPOUND_V3_CSUS, 'Compound V3',
            output_dir,
        )

        # 2. Chain comparison
        chain_results = run_comparison(
            'Chain', df,
            ETHEREUM_CSUS, 'Ethereum L1',
            BASE_CSUS, 'Base L2',
            output_dir,
        )

        # 3. Architecture comparison
        arch_results = run_comparison(
            'Architecture', df,
            AAVE_STYLE_CSUS, 'Pooled',
            COMPOUND_V3_CSUS, 'Isolated',
            output_dir,
        )
    finally:
        os.chdir(original_cwd)

    print("\n" + "=" * 70)
    print("All analyses complete.")
    print(f"Results saved to: {output_dir}")
    print("=" * 70)


if __name__ == '__main__':
    main()
