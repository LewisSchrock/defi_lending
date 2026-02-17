#!/usr/bin/env python3
"""
Two additional analyses for the Pedroni Panel SVAR:

1. BOOTSTRAP CONFIDENCE INTERVALS
   Run member-level SVARs with bootstrap to get 95% CIs.
   Reports significance for each IRF path per member.

2. ALTERNATIVE CHOLESKY ORDERING (Robustness)
   Ordering: util → vol → liq  (instead of baseline util → liq → vol)
   Clearly labeled as "ALT_ORDER" in all output files.

Output directory: results/pedroni/
"""

import sys
import os
import warnings
import copy
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")
warnings.filterwarnings("ignore", category=FutureWarning)

from SVAR import VAR_input, SVAR, VAR_output

# ============================================================
# Shared configuration
# ============================================================

NSTEPS = 20
MAXLAGS = 10
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


def load_panel():
    path = PROJECT_ROOT / 'data' / 'gold' / 'panel_base_eth' / 'gold_panel_base_eth.parquet'
    df = pd.read_parquet(path)
    df['liquidation'] = df['log_collateral_usd']
    return df


def run_member_svar(member_df, variable_order, variables, shocks, sr_constraint, sr_sign,
                    bootstrap=False, ndraws=500):
    """Run a single-member SVAR. Returns VAR_output or None on failure."""
    vinput = VAR_input(
        variables=copy.deepcopy(variables),
        variable_order=variable_order,
        shocks=shocks,
        td_col=['date'],
        member_col='',
        M=None,
        sr_constraint=sr_constraint.copy(),
        lr_constraint=np.array([]),
        sr_sign=sr_sign.copy(),
        lr_sign=np.array([]),
        maxlags=MAXLAGS,
        nsteps=NSTEPS,
        lagmethod=LAGMETHOD,
        bootstrap=bootstrap,
        ndraws=ndraws,
        signif=0.05,
        df=member_df,
        plot=False,
        savefig_path='',
    )
    try:
        out = SVAR(vinput)
        if out.lag_order == 0:
            return None
        return out
    except Exception as e:
        print(f'    SVAR failed: {e}')
        return None


# ============================================================
# PART 1: Bootstrap Confidence Intervals
# ============================================================

def run_bootstrap_analysis(panel_df, output_dir):
    """Run member-level SVARs with bootstrap CIs."""
    print("\n" + "=" * 70)
    print("PART 1: Bootstrap Confidence Intervals")
    print("Ordering: utilization → liquidation → volatility (BASELINE)")
    print("=" * 70)

    variable_order = ['utilization', 'liquidation', 'volatility']
    variables = {'utilization': [0, 0], 'liquidation': [0, 0], 'volatility': [0, 0]}
    shocks = ['Utilization', 'Liquidation', 'Volatility']
    sr_constraint = np.array([['.', '0', '0'], ['.', '.', '0'], ['.', '.', '.']])
    sr_sign = np.array([['+', '.', '.'], ['.', '+', '.'], ['.', '.', '+']])

    NDRAWS = 500
    all_csus = panel_df['csu'].unique().tolist()
    size = len(variable_order)

    sig_rows = []
    ci_rows = []

    for csu in sorted(all_csus):
        print(f"\n  {csu}...")
        member_df = panel_df[panel_df['csu'] == csu][['date'] + variable_order].dropna().copy()

        out = run_member_svar(member_df, variable_order, variables, shocks,
                              sr_constraint, sr_sign, bootstrap=True, ndraws=NDRAWS)
        if out is None:
            print(f"    Skipped (failed or 0 lags)")
            continue

        print(f"    Lags: {out.lag_order}, Bootstrap: {NDRAWS} draws")

        # Check significance: CI does not include zero
        for i, var in enumerate(variable_order):
            for j, shock in enumerate(shocks):
                for h in [0, 5, 10, 20]:
                    if h >= out.ir.shape[0]:
                        continue
                    point = out.ir[h, i, j]
                    lower = out.ir_lower[h, i, j] if len(out.ir_lower) > 0 else np.nan
                    upper = out.ir_upper[h, i, j] if len(out.ir_upper) > 0 else np.nan

                    significant = False
                    if not np.isnan(lower) and not np.isnan(upper):
                        significant = (lower > 0 and upper > 0) or (lower < 0 and upper < 0)

                    ci_rows.append({
                        'member': csu,
                        'response': var,
                        'shock': shock,
                        'horizon': h,
                        'point_estimate': point,
                        'ci_lower_95': lower,
                        'ci_upper_95': upper,
                        'significant_95': significant,
                    })

        # Cumulative significance at h=10
        cum_ir = out.ir[:11].sum(axis=0)
        cum_lower = out.ir_lower[:11].sum(axis=0) if len(out.ir_lower) > 0 else np.full((size, size), np.nan)
        cum_upper = out.ir_upper[:11].sum(axis=0) if len(out.ir_upper) > 0 else np.full((size, size), np.nan)

        for i, var in enumerate(variable_order):
            for j, shock in enumerate(shocks):
                cl = cum_lower[i, j]
                cu = cum_upper[i, j]
                sig = False
                if not np.isnan(cl) and not np.isnan(cu):
                    sig = (cl > 0 and cu > 0) or (cl < 0 and cu < 0)
                sig_rows.append({
                    'member': csu,
                    'response': var,
                    'shock': shock,
                    'cum_irf_h10': cum_ir[i, j],
                    'cum_ci_lower': cl,
                    'cum_ci_upper': cu,
                    'significant_95': sig,
                })

    # Save detailed CIs
    ci_df = pd.DataFrame(ci_rows)
    ci_df.to_csv(output_dir / 'bootstrap_ci_by_member.csv', index=False)
    print(f"\n  Saved: bootstrap_ci_by_member.csv ({len(ci_df)} rows)")

    # Save cumulative significance
    sig_df = pd.DataFrame(sig_rows)
    sig_df.to_csv(output_dir / 'bootstrap_cumulative_significance.csv', index=False)
    print(f"  Saved: bootstrap_cumulative_significance.csv")

    # Summary: fraction of members with significant IRF per path
    print("\n--- Significance Summary (Cumulative IRF at h=10, 95% CI) ---")
    summary_rows = []
    for shock in shocks:
        for var in variable_order:
            path_df = sig_df[(sig_df['shock'] == shock) & (sig_df['response'] == var)]
            n_total = len(path_df)
            n_sig = path_df['significant_95'].sum()
            mean_cum = path_df['cum_irf_h10'].mean()
            median_cum = path_df['cum_irf_h10'].median()
            summary_rows.append({
                'response': var,
                'shock': shock,
                'n_members': n_total,
                'n_significant': int(n_sig),
                'pct_significant': round(n_sig / n_total * 100, 1) if n_total > 0 else 0,
                'mean_cum_irf': mean_cum,
                'median_cum_irf': median_cum,
            })
            print(f"  {var} ← {shock}: {int(n_sig)}/{n_total} significant ({n_sig/n_total*100:.0f}%), median cum IRF = {median_cum:.6f}")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_dir / 'bootstrap_significance_summary.csv', index=False)
    print(f"\n  Saved: bootstrap_significance_summary.csv")

    # Significance by subsample
    print("\n--- Significance by Subsample (Cumulative h=10) ---")
    subsample_rows = []
    for sub_label, sub_csus in [('Aave-Style', AAVE_STYLE_CSUS), ('Compound V3', COMPOUND_V3_CSUS),
                                 ('Ethereum L1', ETHEREUM_CSUS), ('Base L2', BASE_CSUS)]:
        sub_sig = sig_df[sig_df['member'].isin(sub_csus)]
        print(f"\n  {sub_label}:")
        for shock in shocks:
            for var in variable_order:
                path_df = sub_sig[(sub_sig['shock'] == shock) & (sub_sig['response'] == var)]
                n_total = len(path_df)
                n_sig = path_df['significant_95'].sum()
                if n_total > 0:
                    subsample_rows.append({
                        'subsample': sub_label,
                        'response': var,
                        'shock': shock,
                        'n_members': n_total,
                        'n_significant': int(n_sig),
                        'pct_significant': round(n_sig / n_total * 100, 1),
                    })
                    if n_sig > 0:
                        print(f"    {var} ← {shock}: {int(n_sig)}/{n_total} sig")

    pd.DataFrame(subsample_rows).to_csv(output_dir / 'bootstrap_significance_by_subsample.csv', index=False)
    print(f"\n  Saved: bootstrap_significance_by_subsample.csv")

    return ci_df, sig_df


# ============================================================
# PART 2: Alternative Cholesky Ordering (Robustness)
# ============================================================

def run_alt_ordering(panel_df, output_dir):
    """Run Pedroni-style member SVARs with ALTERNATIVE ordering: util → vol → liq."""
    print("\n" + "=" * 70)
    print("PART 2: ALTERNATIVE Cholesky Ordering (Robustness)")
    print("Ordering: utilization → volatility → liquidation (ALT_ORDER)")
    print("Compare with baseline: utilization → liquidation → volatility")
    print("=" * 70)

    # ALT ordering
    alt_variable_order = ['utilization', 'volatility', 'liquidation']
    alt_variables = {'utilization': [0, 0], 'volatility': [0, 0], 'liquidation': [0, 0]}
    alt_shocks = ['Utilization', 'Volatility', 'Liquidation']
    alt_sr_constraint = np.array([['.', '0', '0'], ['.', '.', '0'], ['.', '.', '.']])
    alt_sr_sign = np.array([['+', '.', '.'], ['.', '+', '.'], ['.', '.', '+']])

    # BASELINE ordering (for comparison)
    base_variable_order = ['utilization', 'liquidation', 'volatility']
    base_variables = {'utilization': [0, 0], 'liquidation': [0, 0], 'volatility': [0, 0]}
    base_shocks = ['Utilization', 'Liquidation', 'Volatility']
    base_sr_constraint = np.array([['.', '0', '0'], ['.', '.', '0'], ['.', '.', '.']])
    base_sr_sign = np.array([['+', '.', '.'], ['.', '+', '.'], ['.', '.', '+']])

    all_csus = sorted(panel_df['csu'].unique().tolist())
    size = 3

    # Collect IRFs under both orderings
    baseline_irfs = {}  # member -> ir array
    alt_irfs = {}

    for csu in all_csus:
        print(f"\n  {csu}...")
        member_df = panel_df[panel_df['csu'] == csu].copy()

        # Baseline
        base_df = member_df[['date'] + base_variable_order].dropna()
        out_base = run_member_svar(base_df, base_variable_order, base_variables, base_shocks,
                                   base_sr_constraint, base_sr_sign, bootstrap=False)

        # Alt
        alt_df = member_df[['date'] + alt_variable_order].dropna()
        out_alt = run_member_svar(alt_df, alt_variable_order, alt_variables, alt_shocks,
                                  alt_sr_constraint, alt_sr_sign, bootstrap=False)

        if out_base is not None:
            baseline_irfs[csu] = out_base.ir
            print(f"    Baseline: {out_base.lag_order} lags")
        if out_alt is not None:
            alt_irfs[csu] = out_alt.ir
            print(f"    Alt order: {out_alt.lag_order} lags")

    print(f"\n  Baseline estimated: {len(baseline_irfs)} members")
    print(f"  Alt order estimated: {len(alt_irfs)} members")

    # Map IRF paths between orderings for comparison
    # Baseline: [util=0, liq=1, vol=2], shocks [Util=0, Liq=1, Vol=2]
    # Alt:      [util=0, vol=1, liq=2], shocks [Util=0, Vol=1, Liq=2]

    # Key cross-variable paths (in economic terms):
    economic_paths = [
        ('Util ← Liq',    (0, 1), (0, 2)),  # (base_resp, base_shock), (alt_resp, alt_shock)
        ('Util ← Vol',    (0, 2), (0, 1)),
        ('Liq ← Util',    (1, 0), (2, 0)),
        ('Liq ← Vol',     (1, 2), (2, 1)),
        ('Vol ← Util',    (2, 0), (1, 0)),
        ('Vol ← Liq',     (2, 1), (1, 2)),
        ('Util ← Util',   (0, 0), (0, 0)),
        ('Liq ← Liq',     (1, 1), (2, 2)),
        ('Vol ← Vol',     (2, 2), (1, 1)),
    ]

    # Save comparison data
    comp_rows = []
    common_members = set(baseline_irfs.keys()) & set(alt_irfs.keys())
    for csu in sorted(common_members):
        base_ir = baseline_irfs[csu]
        alt_ir = alt_irfs[csu]
        for path_name, (br, bs), (ar, as_) in economic_paths:
            for h in [0, 5, 10, 20]:
                if h < base_ir.shape[0] and h < alt_ir.shape[0]:
                    comp_rows.append({
                        'member': csu,
                        'path': path_name,
                        'horizon': h,
                        'baseline_irf': base_ir[h, br, bs],
                        'alt_order_irf': alt_ir[h, ar, as_],
                    })

    comp_df = pd.DataFrame(comp_rows)
    comp_df.to_csv(output_dir / 'ALT_ORDER_comparison_by_member.csv', index=False)
    print(f"\n  Saved: ALT_ORDER_comparison_by_member.csv")

    # Summary: median IRFs across members
    print("\n--- Ordering Robustness: Median IRF Comparison ---")
    summary_rows = []
    for path_name, (br, bs), (ar, as_) in economic_paths:
        base_vals = [baseline_irfs[m][:11].sum(axis=0)[br, bs] for m in common_members]
        alt_vals = [alt_irfs[m][:11].sum(axis=0)[ar, as_] for m in common_members]
        base_med = np.median(base_vals)
        alt_med = np.median(alt_vals)
        corr = np.corrcoef(base_vals, alt_vals)[0, 1] if len(base_vals) > 1 else np.nan
        summary_rows.append({
            'path': path_name,
            'baseline_median_cum_h10': base_med,
            'alt_order_median_cum_h10': alt_med,
            'member_correlation': corr,
            'same_sign': np.sign(base_med) == np.sign(alt_med),
        })
        sign_match = "✓" if np.sign(base_med) == np.sign(alt_med) else "✗"
        print(f"  {path_name:15s}  baseline={base_med:+.6f}  alt={alt_med:+.6f}  corr={corr:.3f}  sign={sign_match}")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_dir / 'ALT_ORDER_robustness_summary.csv', index=False)
    print(f"\n  Saved: ALT_ORDER_robustness_summary.csv")

    # Plot comparison: 3×3 grid, baseline vs alt median IRFs
    fig, axes = plt.subplots(3, 3, figsize=(15, 12), sharex=True)
    plot_paths = [
        ('Util ← Util', (0,0), (0,0)),
        ('Util ← Liq', (0,1), (0,2)),
        ('Util ← Vol', (0,2), (0,1)),
        ('Liq ← Util', (1,0), (2,0)),
        ('Liq ← Liq', (1,1), (2,2)),
        ('Liq ← Vol', (1,2), (2,1)),
        ('Vol ← Util', (2,0), (1,0)),
        ('Vol ← Liq', (2,1), (1,2)),
        ('Vol ← Vol', (2,2), (1,1)),
    ]
    steps = np.arange(NSTEPS + 1)
    for idx, (path_name, (br, bs), (ar, as_)) in enumerate(plot_paths):
        ax = axes[idx // 3, idx % 3]
        base_med = np.median([baseline_irfs[m][:, br, bs] for m in common_members], axis=0)
        alt_med = np.median([alt_irfs[m][:, ar, as_] for m in common_members], axis=0)
        ax.plot(steps, base_med, 'b-', linewidth=2, label='Baseline (U→L→V)')
        ax.plot(steps, alt_med, 'r--', linewidth=2, label='Alt (U→V→L)')
        ax.axhline(0, color='gray', linestyle=':', linewidth=0.5)
        ax.set_title(path_name, fontsize=11, fontweight='bold')
        if idx == 0:
            ax.legend(fontsize=8)
        if idx >= 6:
            ax.set_xlabel('Steps')

    fig.suptitle('Cholesky Ordering Robustness: Baseline vs Alternative\n(Median across members)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(output_dir / 'ALT_ORDER_robustness_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: ALT_ORDER_robustness_comparison.png")

    # Plot by subsample
    for sub_label, sub_csus in [('Mechanism', None), ('Chain', None)]:
        if sub_label == 'Mechanism':
            pairs = [('Aave-Style', AAVE_STYLE_CSUS), ('Compound V3', COMPOUND_V3_CSUS)]
        else:
            pairs = [('Ethereum L1', ETHEREUM_CSUS), ('Base L2', BASE_CSUS)]

        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        key_econ_paths = [
            ('Util ← Liq', (0,1), (0,2)),
            ('Liq ← Util', (1,0), (2,0)),
            ('Liq ← Vol', (1,2), (2,1)),
            ('Vol ← Liq', (2,1), (1,2)),
            ('Vol ← Util', (2,0), (1,0)),
            ('Util ← Vol', (0,2), (0,1)),
        ]
        for idx, (path_name, (br, bs), (ar, as_)) in enumerate(key_econ_paths):
            ax = axes[idx // 3, idx % 3]
            for pair_label, pair_csus in pairs:
                members = [m for m in pair_csus if m in common_members]
                if not members:
                    continue
                base_med = np.median([baseline_irfs[m][:, br, bs] for m in members], axis=0)
                alt_med = np.median([alt_irfs[m][:, ar, as_] for m in members], axis=0)
                color = 'blue' if pair_label in ('Aave-Style', 'Ethereum L1') else 'red'
                ax.plot(steps, base_med, '-', color=color, linewidth=2, label=f'{pair_label} (baseline)')
                ax.plot(steps, alt_med, '--', color=color, linewidth=1.5, alpha=0.6, label=f'{pair_label} (alt)')
            ax.axhline(0, color='gray', linestyle=':', linewidth=0.5)
            ax.set_title(path_name, fontsize=11, fontweight='bold')
            ax.legend(fontsize=7)
            if idx >= 3:
                ax.set_xlabel('Steps')

        fig.suptitle(f'ALT ORDER Robustness — {sub_label} Comparison\nSolid=Baseline (U→L→V), Dashed=Alt (U→V→L)',
                     fontsize=13, fontweight='bold')
        plt.tight_layout(rect=[0, 0, 1, 0.93])
        plt.savefig(output_dir / f'ALT_ORDER_{sub_label.lower()}_comparison.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: ALT_ORDER_{sub_label.lower()}_comparison.png")

    return comp_df, summary_df


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 70)
    print("Pedroni Panel SVAR — Bootstrap CIs & Alt Ordering")
    print("=" * 70)

    panel_df = load_panel()
    cols = ['date', 'csu', 'utilization', 'liquidation', 'volatility']
    panel_df = panel_df[cols].dropna(subset=['utilization', 'liquidation', 'volatility'])
    print(f"Panel: {len(panel_df)} obs, {panel_df['csu'].nunique()} CSUs")

    output_dir = PROJECT_ROOT / 'results' / 'pedroni'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure panelSVAR output dir exists (not used here but just in case)
    os.makedirs('output', exist_ok=True)

    # Part 1: Bootstrap CIs
    ci_df, sig_df = run_bootstrap_analysis(panel_df, output_dir)

    # Part 2: Alt ordering
    comp_df, robustness_df = run_alt_ordering(panel_df, output_dir)

    print("\n" + "=" * 70)
    print("All done.")
    print(f"Results in: {output_dir}")
    print("=" * 70)


if __name__ == '__main__':
    main()
