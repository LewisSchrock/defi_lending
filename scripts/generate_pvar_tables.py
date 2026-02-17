#!/usr/bin/env python3
"""
Generate publication-quality tables for Panel VAR results.
Outputs: LaTeX tables + PNG rendered versions.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from statsmodels.tsa.api import VAR
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

RESULTS_DIR = Path('results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CONFIG (mirrors run_pvar_analysis.py)
# ============================================================================

DATA_PATH = Path('data/analysis/vol_util_panel.xlsx')

exclude_csus = [
    'fluid_lending_arbitrum', 'fluid_lending_ethereum',
    'gearbox_ethereum', 'sumermoney_meter', 'compound_v3_base_usdbc',
]
min_observations = 300

pooled_csus = [
    'aave_v3_arbitrum', 'aave_v3_avalanche', 'aave_v3_base',
    'aave_v3_binance', 'aave_v3_ethereum', 'aave_v3_linea',
    'aave_v3_optimism', 'aave_v3_polygon', 'aave_v3_xdai',
    'benqi_lending_avalanche', 'moonwell_lending_base',
    'sparklend_ethereum', 'venus_core_pool_binance',
]

isolated_csus = [
    'compound_v3_arb_usdc', 'compound_v3_arb_usdc_e',
    'compound_v3_arb_usdt', 'compound_v3_arb_weth',
    'compound_v3_base_aero', 'compound_v3_base_usdc',
    'compound_v3_base_weth', 'compound_v3_eth_usdc',
    'compound_v3_eth_usds', 'compound_v3_eth_usdt',
    'compound_v3_eth_weth', 'compound_v3_eth_wsteth',
    'compound_v3_op_usdc', 'compound_v3_op_usdt',
    'compound_v3_op_weth', 'compound_v3_poly_usdc',
]

stablecoin_markets = [
    'compound_v3_arb_usdc', 'compound_v3_arb_usdc_e',
    'compound_v3_arb_usdt', 'compound_v3_base_usdc',
    'compound_v3_eth_usdc', 'compound_v3_eth_usds',
    'compound_v3_eth_usdt', 'compound_v3_op_usdc',
    'compound_v3_op_usdt', 'compound_v3_poly_usdc',
]

volatile_asset_markets = [
    'compound_v3_arb_weth', 'compound_v3_base_aero',
    'compound_v3_base_weth', 'compound_v3_eth_weth',
    'compound_v3_eth_wsteth', 'compound_v3_op_weth',
]

analyses = [
    ('Full Sample',       pooled_csus + isolated_csus),
    ('Pooled',            pooled_csus),
    ('Isolated',          isolated_csus),
    ('Stable Base',       stablecoin_markets),
    ('Volatile Base',     volatile_asset_markets),
]


def load_data():
    df = pd.read_excel(DATA_PATH, sheet_name='panel_data')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['csu', 'date'])
    df = df[~df['csu'].isin(exclude_csus)]
    counts = df.groupby('csu').size()
    short = counts[counts < min_observations].index
    df = df[~df['csu'].isin(short)]
    df['volatility'] = df.groupby('csu')['volatility'].ffill().bfill()
    df = df.dropna(subset=['utilization', 'volatility'])
    return df


def run_var(df, csus, max_lags=10):
    sub = df[df['csu'].isin(csus)].copy()
    sub['util_fe'] = sub.groupby('csu')['utilization'].transform(lambda x: x - x.mean())
    sub['vol_fe'] = sub.groupby('csu')['volatility'].transform(lambda x: x - x.mean())
    panel = sub[['util_fe', 'vol_fe']].dropna()

    model = VAR(panel)
    try:
        lo = model.select_order(maxlags=min(max_lags, len(panel) // 3))
        optimal = max(1, min(lo.bic, 5))
    except:
        optimal = 2

    results = model.fit(optimal)
    irf = results.irf(20)

    # Bootstrap
    rng = np.random.RandomState(42)
    boot_irfs = []
    resids = results.resid.values
    fitted = results.fittedvalues.values
    for _ in range(500):
        idx = rng.choice(len(resids), size=len(resids), replace=True)
        boot_data = fitted + resids[idx]
        try:
            br = VAR(pd.DataFrame(boot_data, columns=panel.columns)).fit(optimal)
            boot_irfs.append(br.irf(20).orth_irfs)
        except:
            continue

    ci_lo = ci_hi = None
    if len(boot_irfs) > 50:
        ba = np.array(boot_irfs)
        ci_lo = np.percentile(ba, 2.5, axis=0)
        ci_hi = np.percentile(ba, 97.5, axis=0)

    return {
        'results': results,
        'irf_orth': irf.orth_irfs,
        'ci_lo': ci_lo,
        'ci_hi': ci_hi,
        'optimal': optimal,
        'n_obs': len(sub),
        'n_csus': sub['csu'].nunique(),
        'sub': sub,
    }


def stars(p):
    if p < 0.01: return '***'
    if p < 0.05: return '**'
    if p < 0.10: return '*'
    return ''


def render_table_png(fig, save_path, title=None):
    """Common render settings."""
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    plt.savefig(save_path, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"  Saved: {save_path}")


# ============================================================================
# TABLE 1: Panel Summary Statistics
# ============================================================================

def table_summary_stats(df):
    print("\n--- Table 1: Panel Summary Statistics ---")

    rows = []
    for label, csus in analyses:
        sub = df[df['csu'].isin(csus)]
        if len(sub) == 0:
            continue
        rows.append({
            'Sample': label,
            'N (CSUs)': sub['csu'].nunique(),
            'T (dates)': sub['date'].nunique(),
            'Obs': len(sub),
            'Util Mean': sub['utilization'].mean(),
            'Util SD': sub['utilization'].std(),
            'Vol Mean': sub['volatility'].mean(),
            'Vol SD': sub['volatility'].std(),
        })

    tbl = pd.DataFrame(rows)

    # Render as figure
    fig, ax = plt.subplots(figsize=(12, 3.5))
    ax.axis('off')

    col_labels = ['Sample', 'N', 'T', 'Obs',
                  'Mean', 'Std Dev', 'Mean', 'Std Dev']
    cell_text = []
    for _, r in tbl.iterrows():
        cell_text.append([
            r['Sample'],
            str(r['N (CSUs)']),
            str(r['T (dates)']),
            f"{r['Obs']:,}",
            f"{r['Util Mean']:.3f}",
            f"{r['Util SD']:.3f}",
            f"{r['Vol Mean']:.4f}",
            f"{r['Vol SD']:.4f}",
        ])

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.6)

    # Style header
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold')

    # Alternating row colors
    for i in range(len(cell_text)):
        color = '#f8f9fa' if i % 2 == 0 else 'white'
        for j in range(len(col_labels)):
            table[i + 1, j].set_facecolor(color)

    # Add column group headers
    fig.text(0.42, 0.92, 'Utilization', ha='center', fontsize=12, fontweight='bold')
    fig.text(0.42, 0.88, '(Leverage Proxy)', ha='center', fontsize=9, color='gray')
    fig.text(0.72, 0.92, 'Volatility', ha='center', fontsize=12, fontweight='bold')
    fig.text(0.72, 0.88, '(Collateral Basket)', ha='center', fontsize=9, color='gray')

    render_table_png(fig, RESULTS_DIR / 'table1_summary_stats.png',
                     'Table 1: Panel Summary Statistics')

    # LaTeX
    latex = tbl.to_latex(index=False, float_format='%.4f', escape=False)
    (RESULTS_DIR / 'table1_summary_stats.tex').write_text(latex)
    return tbl


# ============================================================================
# TABLE 2: Granger Causality Tests
# ============================================================================

def table_granger(df):
    print("\n--- Table 2: Granger Causality Tests ---")

    rows = []
    for label, csus in analyses:
        sub = df[df['csu'].isin(csus)]
        if len(sub) == 0:
            continue

        res = run_var(df, csus)

        try:
            gc_uv = res['results'].test_causality('vol_fe', ['util_fe'], kind='f')
            f_uv, p_uv = gc_uv.test_statistic, gc_uv.pvalue
        except:
            f_uv, p_uv = np.nan, np.nan

        try:
            gc_vu = res['results'].test_causality('util_fe', ['vol_fe'], kind='f')
            f_vu, p_vu = gc_vu.test_statistic, gc_vu.pvalue
        except:
            f_vu, p_vu = np.nan, np.nan

        rows.append({
            'Sample': label,
            'Lags': res['optimal'],
            'F_uv': f_uv, 'p_uv': p_uv, 's_uv': stars(p_uv),
            'F_vu': f_vu, 'p_vu': p_vu, 's_vu': stars(p_vu),
        })

    tbl = pd.DataFrame(rows)

    # Render
    fig, ax = plt.subplots(figsize=(12, 3.8))
    ax.axis('off')

    col_labels = ['Sample', 'Lags', 'F-stat', 'p-value', '', 'F-stat', 'p-value', '']
    cell_text = []
    for _, r in tbl.iterrows():
        cell_text.append([
            r['Sample'],
            str(r['Lags']),
            f"{r['F_uv']:.3f}",
            f"{r['p_uv']:.4f}",
            r['s_uv'],
            f"{r['F_vu']:.3f}",
            f"{r['p_vu']:.4f}",
            r['s_vu'],
        ])

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 1.6)

    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold')

    for i in range(len(cell_text)):
        color = '#f8f9fa' if i % 2 == 0 else 'white'
        for j in range(len(col_labels)):
            table[i + 1, j].set_facecolor(color)
            # Bold significant results
            if j in (3, 4) and '**' in cell_text[i][4]:
                table[i + 1, j].set_text_props(fontweight='bold')
            if j in (6, 7) and '**' in cell_text[i][7]:
                table[i + 1, j].set_text_props(fontweight='bold')

    fig.text(0.40, 0.93, 'Utilization → Volatility', ha='center', fontsize=12, fontweight='bold')
    fig.text(0.73, 0.93, 'Volatility → Utilization', ha='center', fontsize=12, fontweight='bold')
    fig.text(0.50, 0.05, '*** p < 0.01,  ** p < 0.05,  * p < 0.10', ha='center', fontsize=9, color='gray')

    render_table_png(fig, RESULTS_DIR / 'table2_granger_causality.png',
                     'Table 2: Granger Causality Tests')

    latex = tbl[['Sample', 'Lags', 'F_uv', 'p_uv', 's_uv', 'F_vu', 'p_vu', 's_vu']].to_latex(
        index=False, float_format='%.4f', escape=False)
    (RESULTS_DIR / 'table2_granger_causality.tex').write_text(latex)
    return tbl


# ============================================================================
# TABLE 3: IRF Summary — Utilization → Volatility
# ============================================================================

def table_irf_summary(df):
    print("\n--- Table 3: IRF Summary (Util → Vol) ---")

    rows = []
    for label, csus in analyses:
        sub = df[df['csu'].isin(csus)]
        if len(sub) == 0:
            continue

        res = run_var(df, csus)
        irf_uv = res['irf_orth'][:, 0, 1]  # util→vol
        irf_vu = res['irf_orth'][:, 1, 0]  # vol→util

        # Significance: check if CI excludes zero at each horizon
        sig_horizons_uv = []
        sig_horizons_vu = []
        if res['ci_lo'] is not None:
            for h in range(21):
                lo_uv = res['ci_lo'][h, 0, 1]
                hi_uv = res['ci_hi'][h, 0, 1]
                if lo_uv > 0 or hi_uv < 0:
                    sig_horizons_uv.append(h)
                lo_vu = res['ci_lo'][h, 1, 0]
                hi_vu = res['ci_hi'][h, 1, 0]
                if lo_vu > 0 or hi_vu < 0:
                    sig_horizons_vu.append(h)

        peak_idx = int(np.argmax(np.abs(irf_uv)))
        cumul = np.sum(irf_uv)

        rows.append({
            'Sample': label,
            'N': res['n_csus'],
            'Obs': res['n_obs'],
            'Impact (t=1)': irf_uv[1],
            'Peak': irf_uv[peak_idx],
            'Peak Period': peak_idx,
            'Cumulative': cumul,
            'Sign': '+' if cumul > 0 else '−',
            'Sig Horizons': f"{len(sig_horizons_uv)}/21" if res['ci_lo'] is not None else 'N/A',
        })

    tbl = pd.DataFrame(rows)

    # Render
    fig, ax = plt.subplots(figsize=(13, 3.8))
    ax.axis('off')

    col_labels = ['Sample', 'N', 'Obs', 'Impact (t=1)', 'Peak', 'Peak t',
                  'Cumulative (Σ)', 'Sign', 'Sig. Horizons']
    cell_text = []
    for _, r in tbl.iterrows():
        cell_text.append([
            r['Sample'],
            str(r['N']),
            f"{r['Obs']:,}",
            f"{r['Impact (t=1)']:.5f}",
            f"{r['Peak']:.5f}",
            f"t+{r['Peak Period']}",
            f"{r['Cumulative']:.5f}",
            r['Sign'],
            r['Sig Horizons'],
        ])

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10.5)
    table.scale(1, 1.6)

    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold')

    for i in range(len(cell_text)):
        color = '#f8f9fa' if i % 2 == 0 else 'white'
        for j in range(len(col_labels)):
            table[i + 1, j].set_facecolor(color)

    # Highlight the sign column for contrast
    for i in range(len(cell_text)):
        sign_cell = table[i + 1, 7]
        if cell_text[i][7] == '+':
            sign_cell.set_text_props(color='#e74c3c', fontweight='bold')
        else:
            sign_cell.set_text_props(color='#2980b9', fontweight='bold')

    fig.text(0.50, 0.05, 'Orthogonalized IRF. Cholesky ordering: Utilization → Volatility. 95% bootstrap CI (500 replications).',
             ha='center', fontsize=9, color='gray')

    render_table_png(fig, RESULTS_DIR / 'table3_irf_summary.png',
                     'Table 3: Impulse Response Summary — Utilization Shock → Volatility')

    latex = tbl.to_latex(index=False, float_format='%.5f', escape=False)
    (RESULTS_DIR / 'table3_irf_summary.tex').write_text(latex)
    return tbl


# ============================================================================
# TABLE 4: Subsample Architecture Comparison
# ============================================================================

def table_architecture_comparison(df):
    print("\n--- Table 4: Architecture Comparison ---")

    compare = [
        ('Pooled', pooled_csus),
        ('Isolated', isolated_csus),
        ('Stable Base', stablecoin_markets),
        ('Volatile Base', volatile_asset_markets),
    ]

    rows = []
    for label, csus in compare:
        sub = df[df['csu'].isin(csus)]
        if len(sub) == 0:
            continue

        res = run_var(df, csus)
        irf_uv = res['irf_orth'][:, 0, 1]
        irf_vu = res['irf_orth'][:, 1, 0]

        try:
            gc_uv = res['results'].test_causality('vol_fe', ['util_fe'], kind='f')
            p_uv = gc_uv.pvalue
        except:
            p_uv = np.nan
        try:
            gc_vu = res['results'].test_causality('util_fe', ['vol_fe'], kind='f')
            p_vu = gc_vu.pvalue
        except:
            p_vu = np.nan

        rows.append({
            'Architecture': label,
            'Protocols': _get_protocols(csus),
            'N': res['n_csus'],
            'Util Mean': sub['utilization'].mean(),
            'Vol Mean': sub['volatility'].mean(),
            'GC Util→Vol p': p_uv,
            'GC Vol→Util p': p_vu,
            'IRF Cumul (U→V)': np.sum(irf_uv),
            'IRF Cumul (V→U)': np.sum(irf_vu),
            'IRF Sign (U→V)': '+' if np.sum(irf_uv) > 0 else '−',
        })

    tbl = pd.DataFrame(rows)

    # Render
    fig, ax = plt.subplots(figsize=(14, 4.2))
    ax.axis('off')

    col_labels = ['Architecture', 'Protocols', 'N',
                  'Util\nMean', 'Vol\nMean',
                  'GC p\n(U→V)', 'GC p\n(V→U)',
                  'Cumul IRF\n(U→V)', 'Cumul IRF\n(V→U)', 'Sign\n(U→V)']
    cell_text = []
    for _, r in tbl.iterrows():
        cell_text.append([
            r['Architecture'],
            r['Protocols'],
            str(r['N']),
            f"{r['Util Mean']:.3f}",
            f"{r['Vol Mean']:.4f}",
            f"{r['GC Util→Vol p']:.4f}" + stars(r['GC Util→Vol p']),
            f"{r['GC Vol→Util p']:.4f}" + stars(r['GC Vol→Util p']),
            f"{r['IRF Cumul (U→V)']:.5f}",
            f"{r['IRF Cumul (V→U)']:.5f}",
            r['IRF Sign (U→V)'],
        ])

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)

    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold', fontsize=9)

    for i in range(len(cell_text)):
        color = '#f8f9fa' if i % 2 == 0 else 'white'
        for j in range(len(col_labels)):
            table[i + 1, j].set_facecolor(color)

    # Color the sign column
    for i in range(len(cell_text)):
        sign_cell = table[i + 1, 9]
        if cell_text[i][9] == '+':
            sign_cell.set_text_props(color='#e74c3c', fontweight='bold', fontsize=12)
        else:
            sign_cell.set_text_props(color='#2980b9', fontweight='bold', fontsize=12)

    fig.text(0.50, 0.04,
             'Pooled = shared collateral pool. Isolated = single base asset per market. '
             'Stable Base = USDC/USDT/USDS markets. Volatile Base = WETH/wstETH/AERO markets.',
             ha='center', fontsize=8.5, color='gray', style='italic')

    render_table_png(fig, RESULTS_DIR / 'table4_architecture_comparison.png',
                     'Table 4: Subsample Comparison — Pooled vs. Isolated Architecture')

    latex = tbl.to_latex(index=False, float_format='%.5f', escape=False)
    (RESULTS_DIR / 'table4_architecture_comparison.tex').write_text(latex)
    return tbl


def _get_protocols(csus):
    protos = set()
    for c in csus:
        if c.startswith('aave'): protos.add('Aave V3')
        elif c.startswith('compound'): protos.add('Compound V3')
        elif c.startswith('benqi'): protos.add('Benqi')
        elif c.startswith('moonwell'): protos.add('Moonwell')
        elif c.startswith('spark'): protos.add('SparkLend')
        elif c.startswith('venus'): protos.add('Venus')
    return ', '.join(sorted(protos))


# ============================================================================
# FIGURE: Key IRF comparison (Stable vs Volatile)
# ============================================================================

def figure_key_comparison(df):
    print("\n--- Figure: Stable vs Volatile IRF Comparison ---")

    res_stable = run_var(df, stablecoin_markets)
    res_volatile = run_var(df, volatile_asset_markets)
    res_pooled = run_var(df, pooled_csus)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

    specs = [
        (axes[0], res_pooled, 'Pooled Architecture\n(Aave, Benqi, Moonwell, Spark, Venus)', '#3498db'),
        (axes[1], res_stable, 'Isolated — Stablecoin Base\n(USDC, USDT, USDS markets)', '#2ecc71'),
        (axes[2], res_volatile, 'Isolated — Volatile Base\n(WETH, wstETH, AERO markets)', '#e74c3c'),
    ]

    for ax, res, title, color in specs:
        irf_uv = res['irf_orth'][:, 0, 1]
        periods = range(len(irf_uv))
        ax.plot(periods, irf_uv, color=color, lw=2.5)
        if res['ci_lo'] is not None:
            ax.fill_between(periods,
                            res['ci_lo'][:, 0, 1],
                            res['ci_hi'][:, 0, 1],
                            alpha=0.2, color=color)
        ax.axhline(0, color='black', ls='--', lw=0.8)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_xlabel('Days After Shock', fontsize=10)
        ax.set_ylabel('Response of Volatility', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Add N and significance annotation
        try:
            gc = res['results'].test_causality('vol_fe', ['util_fe'], kind='f')
            gc_str = f"GC p={gc.pvalue:.4f}{stars(gc.pvalue)}"
        except:
            gc_str = ""
        ax.text(0.95, 0.95, f"N={res['n_csus']}, {res['n_obs']:,} obs\n{gc_str}",
                transform=ax.transAxes, fontsize=8.5, va='top', ha='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    fig.suptitle('Impulse Response: Utilization Shock → Volatility\nby Market Architecture',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / 'figure_key_irf_comparison.png', dpi=200, bbox_inches='tight',
                facecolor='white')
    plt.close()
    print(f"  Saved: {RESULTS_DIR / 'figure_key_irf_comparison.png'}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("GENERATING PUBLICATION TABLES")
    print("=" * 70)

    df = load_data()
    print(f"Data: {len(df):,} obs, {df['csu'].nunique()} CSUs")

    table_summary_stats(df)
    table_granger(df)
    table_irf_summary(df)
    table_architecture_comparison(df)
    figure_key_comparison(df)

    print(f"\n{'='*70}")
    print(f"All tables saved to {RESULTS_DIR}/")
    print(f"  table1_summary_stats.png / .tex")
    print(f"  table2_granger_causality.png / .tex")
    print(f"  table3_irf_summary.png / .tex")
    print(f"  table4_architecture_comparison.png / .tex")
    print(f"  figure_key_irf_comparison.png")


if __name__ == '__main__':
    main()
