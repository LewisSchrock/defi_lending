#!/usr/bin/env python3
"""
Trivariate Panel VAR Analysis — Liquidations × Utilization × Volatility
Runs full_sample, pooled_only, isolated_only, stablecoin, volatile subsample analyses.
Produces IRFs and publication-quality plots.
Cholesky ordering: log_liquidations → utilization → volatility
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.api import VAR
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIG
# ============================================================================

DATA_PATH = Path('data/gold/panel_all_csus/gold_panel_all_csus.parquet')
RESULTS_DIR = Path('results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Variables for the trivariate VAR (Cholesky ordering: util → liq → vol)
VAR_VARS = ['utilization', 'log_n_liquidations', 'volatility']
VAR_LABELS = {'utilization': 'Utilization', 'log_n_liquidations': 'Log Liquidations', 'volatility': 'Volatility'}
FE_NAMES = ['util_fe', 'liq_fe', 'vol_fe']

exclude_csus = [
    'cap_ethereum',
    'sonne_lending_optimism',
]

min_observations = 300

pooled_csus = [
    'aave_v3_arbitrum', 'aave_v3_avalanche', 'aave_v3_base',
    'aave_v3_binance', 'aave_v3_ethereum', 'aave_v3_linea',
    'aave_v3_optimism', 'aave_v3_polygon', 'aave_v3_xdai',
    'aave_v3_scroll',
    'benqi_lending_avalanche', 'moonwell_lending_base',
    'sparklend_ethereum', 'venus_core_pool_binance',
    'fluid_lending_ethereum', 'fluid_lending_arbitrum',
    'compound_v2_ethereum',
    'lodestar_lending_arbitrum', 'mendi_lending_linea',
]

isolated_csus = [
    'compound_v3_arb_usdc', 'compound_v3_arb_usdc_e',
    'compound_v3_arb_usdt', 'compound_v3_arb_weth',
    'compound_v3_base_aero', 'compound_v3_base_usdc',
    'compound_v3_base_usdbc', 'compound_v3_base_weth',
    'compound_v3_eth_usdc', 'compound_v3_eth_usds',
    'compound_v3_eth_usdt', 'compound_v3_eth_weth',
]

stablecoin_markets = [
    'compound_v3_arb_usdc', 'compound_v3_arb_usdc_e',
    'compound_v3_arb_usdt', 'compound_v3_base_usdc',
    'compound_v3_eth_usdc', 'compound_v3_eth_usds',
    'compound_v3_eth_usdt',
]

volatile_asset_markets = [
    'compound_v3_arb_weth', 'compound_v3_base_aero',
    'compound_v3_base_weth', 'compound_v3_eth_weth',
]

analyses = [
    {'name': 'full_sample', 'desc': 'All CSUs (after quality filters)', 'csus': pooled_csus + isolated_csus},
    {'name': 'pooled_only', 'desc': 'Pooled architecture (Aave, Benqi, Moonwell, Spark, Venus, Fluid, etc.)', 'csus': pooled_csus},
    {'name': 'isolated_only', 'desc': 'Isolated architecture (Compound V3)', 'csus': isolated_csus},
    {'name': 'stablecoin_markets', 'desc': 'Compound V3 stablecoin base markets', 'csus': stablecoin_markets},
    {'name': 'volatile_markets', 'desc': 'Compound V3 WETH/volatile base markets', 'csus': volatile_asset_markets},
]

IRF_PERIODS = 20
N_BOOTSTRAP = 500
MAX_LAGS = 10


# ============================================================================
# FUNCTIONS
# ============================================================================

def run_pvar(df, name, desc, max_lags=MAX_LAGS, irf_periods=IRF_PERIODS, n_boot=N_BOOTSTRAP):
    """Run trivariate Panel VAR with fixed effects and IRFs."""
    n_vars = len(VAR_VARS)
    print(f"\n{'='*70}")
    print(f"  {name}: {desc}")
    print(f"{'='*70}")
    print(f"  Observations: {len(df):,}")
    print(f"  CSUs: {df['csu'].nunique()}")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Summary stats
    print(f"\n  Variable Summary:")
    for var in VAR_VARS:
        print(f"    {var}: mean={df[var].mean():.4f}, std={df[var].std():.4f}, "
              f"min={df[var].min():.4f}, max={df[var].max():.4f}")

    # Fixed effects: within-transformation (demean by CSU)
    df = df.copy()
    for var, fe in zip(VAR_VARS, FE_NAMES):
        df[fe] = df.groupby('csu')[var].transform(lambda x: x - x.mean())

    panel = df[FE_NAMES].dropna()

    # Fit VAR
    model = VAR(panel)

    # Lag selection
    try:
        lag_order = model.select_order(maxlags=min(max_lags, len(panel) // 3))
        aic_lag = lag_order.aic
        bic_lag = lag_order.bic
        hqic_lag = lag_order.hqic
        optimal = max(1, min(bic_lag, 5))
        print(f"\n  Lag Selection: AIC={aic_lag}, BIC={bic_lag}, HQIC={hqic_lag}")
    except Exception as e:
        print(f"\n  Lag selection failed ({e}), using 2 lags")
        optimal = 2

    results = model.fit(optimal)
    print(f"  Using {optimal} lag(s)")

    # IRFs (orthogonalized — Cholesky ordering: liq → util → vol)
    irf = results.irf(periods=irf_periods)
    irf_orth = irf.orth_irfs  # shape: (periods+1, n_vars, n_vars)

    # Bootstrap CIs via manual resampling
    ci_lo = ci_hi = None
    try:
        rng = np.random.RandomState(42)
        boot_irfs = []
        resids = results.resid.values
        fitted = results.fittedvalues.values

        for b in range(n_boot):
            idx = rng.choice(len(resids), size=len(resids), replace=True)
            boot_resid = resids[idx]
            boot_data = fitted + boot_resid
            boot_df = pd.DataFrame(boot_data, columns=panel.columns)
            try:
                boot_model = VAR(boot_df)
                boot_res = boot_model.fit(optimal)
                boot_irf = boot_res.irf(irf_periods)
                boot_irfs.append(boot_irf.orth_irfs)
            except:
                continue

        if len(boot_irfs) > 50:
            boot_arr = np.array(boot_irfs)
            ci_lo = np.percentile(boot_arr, 2.5, axis=0)
            ci_hi = np.percentile(boot_arr, 97.5, axis=0)
            print(f"  Bootstrap: {len(boot_irfs)}/{n_boot} successful replications")
        else:
            print(f"  Bootstrap: only {len(boot_irfs)} successful replications, skipping CIs")
    except Exception as e:
        print(f"  Bootstrap CI failed ({e}), using None")

    # Extract all 9 IRF paths (3x3)
    # Column order: util=0, liq=1, vol=2
    var_short = ['util', 'liq', 'vol']
    irfs = {}
    cis = {}
    for i, imp in enumerate(var_short):
        for j, resp in enumerate(var_short):
            key = f'{imp}→{resp}'
            irfs[key] = irf_orth[:, i, j]
            if ci_lo is not None:
                cis[key] = (ci_lo[:, i, j], ci_hi[:, i, j])

    # Print key IRFs
    key_paths = ['liq→util', 'liq→vol', 'util→vol', 'vol→liq']
    for path_key in key_paths:
        irf_vals = irfs[path_key]
        print(f"\n  IRF: {path_key}")
        for t in range(min(11, len(irf_vals))):
            ci_str = ""
            if path_key in cis:
                lo, hi = cis[path_key][0][t], cis[path_key][1][t]
                sig = " *" if lo > 0 or hi < 0 else ""
                ci_str = f"  [{lo:9.6f}, {hi:9.6f}]{sig}"
            print(f"    t+{t:2d}: {irf_vals[t]:9.6f}{ci_str}")

    return {
        'name': name,
        'desc': desc,
        'n_obs': len(df),
        'n_csus': df['csu'].nunique(),
        'lags': optimal,
        'results': results,
        'irfs': irfs,
        'cis': cis,
        'df': df,
    }


def plot_irfs_grid(result, save_path):
    """Plot 2x2 IRF grid for a single analysis."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle(f"Orthogonalized IRFs — {result['desc']}\n"
                 f"(N={result['n_csus']} CSUs, T={result['n_obs']:,} obs, {result['lags']} lag(s))",
                 fontsize=13, fontweight='bold')

    titles = {
        'util→util': 'Utilization → Utilization',
        'util→vol':  'Utilization → Volatility',
        'vol→util':  'Volatility → Utilization',
        'vol→vol':   'Volatility → Volatility',
    }
    positions = {
        'util→util': (0, 0), 'util→vol': (0, 1),
        'vol→util': (1, 0), 'vol→vol': (1, 1),
    }

    for key, (r, c) in positions.items():
        ax = axes[r, c]
        vals = result['irfs'][key]
        periods = range(len(vals))

        ax.plot(periods, vals, 'b-', lw=2)
        if key in result['cis']:
            lo, hi = result['cis'][key]
            ax.fill_between(periods, lo, hi, alpha=0.2, color='blue')
        ax.axhline(0, color='black', ls='--', lw=0.5)
        ax.set_title(titles[key], fontsize=11)
        ax.set_xlabel('Days')
        ax.set_ylabel('Response')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def plot_key_irf(result, save_path):
    """Plot the key Utilization → Volatility IRF."""
    fig, ax = plt.subplots(figsize=(10, 6))

    vals = result['irfs']['util→vol']
    periods = range(len(vals))

    ax.plot(periods, vals, 'b-', lw=2.5, label='IRF (orthogonalized)')
    if 'util→vol' in result['cis']:
        lo, hi = result['cis']['util→vol']
        ax.fill_between(periods, lo, hi, alpha=0.2, color='blue', label='95% Bootstrap CI')
    ax.axhline(0, color='black', ls='--', lw=0.8)

    ax.set_title(f"Utilization Shock → Volatility Response\n{result['desc']}",
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Days After Shock', fontsize=12)
    ax.set_ylabel('Response of Volatility', fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Annotation
    peak_idx = np.argmax(np.abs(vals))
    ax.annotate(f'Peak: {vals[peak_idx]:.5f} at t+{peak_idx}',
                xy=(peak_idx, vals[peak_idx]),
                xytext=(peak_idx + 3, vals[peak_idx]),
                fontsize=10, ha='left',
                arrowprops=dict(arrowstyle='->', color='gray'))

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def plot_subsample_comparison(results_dict, save_path):
    """Compare IRFs across subsamples."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors = {
        'full_sample': ('black', 'gray'),
        'pooled_only': ('blue', 'lightblue'),
        'isolated_only': ('red', 'lightsalmon'),
        'stablecoin_markets': ('green', 'lightgreen'),
        'volatile_markets': ('orange', 'moccasin'),
    }

    labels = {
        'full_sample': 'Full Sample',
        'pooled_only': 'Pooled (Aave etc.)',
        'isolated_only': 'Isolated (Compound V3)',
        'stablecoin_markets': 'Stablecoin Markets',
        'volatile_markets': 'Volatile Asset Markets',
    }

    # Left panel: util → vol
    ax = axes[0]
    for name, res in results_dict.items():
        vals = res['irfs']['util→vol']
        c, _ = colors.get(name, ('gray', 'lightgray'))
        lw = 2.5 if name == 'full_sample' else 1.8
        ls = '-' if name in ('full_sample', 'pooled_only', 'isolated_only') else '--'
        ax.plot(range(len(vals)), vals, color=c, lw=lw, ls=ls, label=labels.get(name, name))
    ax.axhline(0, color='black', ls='--', lw=0.5)
    ax.set_title('Utilization → Volatility', fontsize=13, fontweight='bold')
    ax.set_xlabel('Days')
    ax.set_ylabel('Response')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Right panel: vol → util
    ax = axes[1]
    for name, res in results_dict.items():
        vals = res['irfs']['vol→util']
        c, _ = colors.get(name, ('gray', 'lightgray'))
        lw = 2.5 if name == 'full_sample' else 1.8
        ls = '-' if name in ('full_sample', 'pooled_only', 'isolated_only') else '--'
        ax.plot(range(len(vals)), vals, color=c, lw=lw, ls=ls, label=labels.get(name, name))
    ax.axhline(0, color='black', ls='--', lw=0.5)
    ax.set_title('Volatility → Utilization', fontsize=13, fontweight='bold')
    ax.set_xlabel('Days')
    ax.set_ylabel('Response')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.suptitle('Panel VAR: Subsample Comparison of IRFs', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {save_path}")


def save_summary_table(results_dict, save_path):
    """Save summary table across all analyses."""
    rows = []
    for name, res in results_dict.items():
        row = {
            'Analysis': name,
            'Description': res['desc'],
            'N_CSUs': res['n_csus'],
            'N_Obs': res['n_obs'],
            'Lags': res['lags'],
        }

        # Granger causality
        gc = res['gc']
        if 'util→vol' in gc:
            row['GC_util_vol_F'] = gc['util→vol']['f_stat']
            row['GC_util_vol_p'] = gc['util→vol']['p']
        if 'vol→util' in gc:
            row['GC_vol_util_F'] = gc['vol→util']['f_stat']
            row['GC_vol_util_p'] = gc['vol→util']['p']

        # IRF summary
        irf_uv = res['irfs']['util→vol']
        row['IRF_util_vol_peak'] = irf_uv[np.argmax(np.abs(irf_uv))]
        row['IRF_util_vol_peak_period'] = int(np.argmax(np.abs(irf_uv)))
        row['IRF_util_vol_cumulative'] = np.sum(irf_uv)

        irf_vu = res['irfs']['vol→util']
        row['IRF_vol_util_peak'] = irf_vu[np.argmax(np.abs(irf_vu))]
        row['IRF_vol_util_peak_period'] = int(np.argmax(np.abs(irf_vu)))
        row['IRF_vol_util_cumulative'] = np.sum(irf_vu)

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(save_path, index=False)
    print(f"\nSaved summary table: {save_path}")
    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("PANEL VAR ANALYSIS — Utilization × Volatility")
    print("=" * 70)

    # Load full data once
    df_all = pd.read_excel(DATA_PATH, sheet_name='panel_data')
    df_all['date'] = pd.to_datetime(df_all['date'])
    df_all = df_all.sort_values(['csu', 'date'])

    # Remove excluded CSUs
    df_all = df_all[~df_all['csu'].isin(exclude_csus)]

    # Remove CSUs below min_obs
    csu_counts = df_all.groupby('csu').size()
    short_csus = csu_counts[csu_counts < min_observations].index.tolist()
    if short_csus:
        print(f"\nExcluding CSUs with < {min_observations} obs: {short_csus}")
    df_all = df_all[~df_all['csu'].isin(short_csus)]

    # Fill missing volatility
    df_all['volatility'] = df_all.groupby('csu')['volatility'].ffill().bfill()
    df_all = df_all.dropna(subset=['utilization', 'volatility'])

    print(f"\nFull dataset after filters: {len(df_all):,} obs, {df_all['csu'].nunique()} CSUs")
    print(f"CSUs: {sorted(df_all['csu'].unique())}")

    # Run each analysis
    all_results = {}
    for spec in analyses:
        name = spec['name']
        csus = [c for c in spec['csus'] if c in df_all['csu'].values]
        if not csus:
            print(f"\n  SKIP {name}: no valid CSUs")
            continue

        df_sub = df_all[df_all['csu'].isin(csus)].copy()
        if len(df_sub) < 100:
            print(f"\n  SKIP {name}: too few observations ({len(df_sub)})")
            continue

        result = run_pvar(df_sub, name, spec['desc'])
        all_results[name] = result

        # Plot IRFs
        plot_irfs_grid(result, RESULTS_DIR / f'irf_grid_{name}.png')
        plot_key_irf(result, RESULTS_DIR / f'irf_util_vol_{name}.png')

    # Subsample comparison plot
    if len(all_results) > 1:
        plot_subsample_comparison(all_results, RESULTS_DIR / 'irf_subsample_comparison.png')

    # Summary table
    summary = save_summary_table(all_results, RESULTS_DIR / 'pvar_summary.csv')
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(summary.to_string(index=False))

    print(f"\n\nAll results saved to {RESULTS_DIR}/")


if __name__ == '__main__':
    main()
