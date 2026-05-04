#!/usr/bin/env python3
"""
Second-stage: per-CSU volume-weighted stablecoin-debt share vs price-triggering IRF.

Direct mechanical test of the denomination channel.  For each liquidation
event we know the debt symbol and its USD value; the stablecoin-debt share
for CSU i is

    stable_share_i = (sum of debt_usd across events with stable debt)
                   / (sum of debt_usd across all events),

bounded in [0, 1].  Under the HF microfoundation, stablecoin debt severs the
offsetting debt-return term, so markets with a high stablecoin-debt share
should show a LARGER price-triggering IRF in absolute value.

In the bivariate_return_liq SVAR, the IRF of liquidation to return_shock is
negative (positive return shock => lower liquidation).  Larger absolute
response = more negative.  Expected sign:  beta < 0  on stable_share.

Outputs:
  - results/data_analysis/second_stage/bivariate_return_liq/stable_share_second_stage.csv
  - results/data_analysis/second_stage/bivariate_return_liq/stable_share_scatter.png
"""

from pathlib import Path
import glob
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent
IRFS_DIR     = PROJECT_ROOT / 'results' / 'pedroni' / 'bivariate_return_liq'
SILVER_GLOB  = str(PROJECT_ROOT / 'data' / 'silver' / 'liquidations' / '*' / 'liquidations.parquet')
OUT_DIR      = PROJECT_ROOT / 'results' / 'data_analysis' / 'second_stage' / 'bivariate_return_liq'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Use the canonical stablecoin classifier from the FE pipeline so the two
# denomination tests use identical classification rules.
import sys
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from build_gold_panel_by_denomination import is_stablecoin as is_stable


def load_irf(kind, variable='liquidation', shock='return_shock'):
    df = pd.read_csv(IRFS_DIR / f'irfs_{kind}.csv')
    return df[(df['variable']==variable) & (df['shock']==shock)].copy()


def main():
    # Build stable-share per CSU
    files = glob.glob(SILVER_GLOB)
    print(f'Loading {len(files)} silver liquidation files...')
    dfs = [pd.read_parquet(p) for p in files]
    events = pd.concat(dfs, ignore_index=True)
    events = events[events['debt_usd'] > 0].copy()
    events['is_stable'] = events['debt_symbol'].apply(is_stable)

    agg = events.groupby('csu').apply(lambda g: pd.Series({
        'n_events':      len(g),
        'total_usd':     g['debt_usd'].sum(),
        'stable_usd':    g.loc[g['is_stable'], 'debt_usd'].sum(),
        'stable_share':  g.loc[g['is_stable'], 'debt_usd'].sum() / g['debt_usd'].sum(),
        'stable_count_share': g['is_stable'].mean(),
    }), include_groups=False).reset_index()

    # Per-CSU lambda and IRFs at h=1
    lam = pd.read_csv(IRFS_DIR / 'lambda.csv')[['csu', 'lam_liquidation_liquidation']] \
            .rename(columns={'lam_liquidation_liquidation': 'lam_liq'})
    comp = load_irf('composite')
    comm = load_irf('common')
    idio = load_irf('idiosyncratic')

    def h1(df, col):
        return df[df['horizon']==1][['csu','irf']].rename(columns={'irf': col})
    irf_h1 = h1(comp, 'irf_h1_composite') \
        .merge(h1(comm, 'irf_h1_common'),        on='csu') \
        .merge(h1(idio, 'irf_h1_idiosyncratic'), on='csu')

    df = lam.merge(irf_h1, on='csu').merge(agg, on='csu', how='left').dropna(subset=['stable_share'])
    print(f'\nMerged analysis sample: N = {len(df)}')
    print(f'stable_share (USD-weighted) range: [{df["stable_share"].min():.3f}, {df["stable_share"].max():.3f}]')
    print(df[['csu','stable_share','n_events','total_usd','lam_liq','irf_h1_common']]
          .sort_values('stable_share')
          .to_string(index=False, float_format='{:.4f}'.format))
    print()

    def run_ols(y_col, x_col, label=''):
        s = df.dropna(subset=[y_col, x_col])
        X = sm.add_constant(s[x_col])
        res = sm.OLS(s[y_col], X).fit(cov_type='HC3')
        ci_lo, ci_hi = res.conf_int().loc[x_col]
        rho = np.corrcoef(s[x_col], s[y_col])[0, 1]
        print(f'OLS: {y_col} ~ const + {x_col}    [{label}]    (HC3-robust)')
        print(f'  N = {int(res.nobs)}   rho = {rho:+.3f}   R^2 = {res.rsquared:.3f}')
        print(f'  const         = {res.params["const"]:+.4f}   SE = {res.bse["const"]:.4f}   t = {res.tvalues["const"]:+.2f}   p = {res.pvalues["const"]:.4f}')
        print(f'  {x_col:13s} = {res.params[x_col]:+.4f}   SE = {res.bse[x_col]:.4f}   t = {res.tvalues[x_col]:+.2f}   p = {res.pvalues[x_col]:.4f}')
        print(f'  95% CI on slope: [{ci_lo:+.4f}, {ci_hi:+.4f}]')
        print()
        return res

    results_rows = []
    for y in ['irf_h1_composite', 'irf_h1_common', 'irf_h1_idiosyncratic', 'lam_liq']:
        for x in ['stable_share']:
            res = run_ols(y, x, label=f'{y} vs {x}')
            results_rows.append({
                'y': y, 'x': x, 'N': int(res.nobs),
                'beta':  res.params[x], 'se': res.bse[x],
                't': res.tvalues[x], 'p': res.pvalues[x],
                'r2': res.rsquared,
            })
    pd.DataFrame(results_rows).to_csv(OUT_DIR / 'stable_share_second_stage.csv', index=False)

    # Scatter figure
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
    for ax, y, label in [
        (axes[0], 'irf_h1_composite',     'composite'),
        (axes[1], 'irf_h1_common',        'common'),
        (axes[2], 'irf_h1_idiosyncratic', 'idiosyncratic'),
    ]:
        x = df['stable_share'].values
        yv = df[y].values
        rho = np.corrcoef(x, yv)[0, 1]
        X = sm.add_constant(x)
        res = sm.OLS(yv, X).fit(cov_type='HC3')
        xs = np.linspace(0, 1, 100)
        pred = res.get_prediction(sm.add_constant(xs)).summary_frame(alpha=0.05)

        ax.fill_between(xs, pred['mean_ci_lower'], pred['mean_ci_upper'],
                        color='#c7573b', alpha=0.15, label='95% CI (HC3)')
        ax.plot(xs, pred['mean'], '-', color='#c7573b', lw=1.8,
                label=f'β = {res.params[1]:+.3f}  (p = {res.pvalues[1]:.3f})')
        ax.scatter(x, yv, s=55, color='#4c72b0', edgecolor='black', linewidth=0.5, alpha=0.9, zorder=3)
        for _, r in df.iterrows():
            ax.annotate(r['csu'], xy=(r['stable_share'], r[y]), xytext=(3, 2),
                        textcoords='offset points', fontsize=5.5, color='#333', alpha=0.8)
        ax.axhline(0, color='black', lw=0.5, ls=':')
        ax.set_xlabel('Stablecoin-debt USD share')
        ax.set_ylabel(f'IRF at h=1  [{label}]')
        ax.set_title(f'[{label}]   ρ = {rho:+.2f},  R² = {res.rsquared:.2f}', fontsize=10)
        ax.grid(alpha=0.25)
        ax.legend(loc='best', fontsize=8)
        ax.set_xlim(-0.02, 1.02)

    fig.suptitle(
        r'Per-CSU stablecoin-debt share vs price-triggering IRF     $\mathrm{IRF}_{i,h=1} = \alpha + \beta \cdot \mathrm{StableShare}_i + \varepsilon_i$'
        + f'     (N = {len(df)})',
        fontsize=12, fontweight='bold',
    )
    fig.tight_layout()
    fig_path = OUT_DIR / 'stable_share_scatter.png'
    fig.savefig(fig_path, dpi=140, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {fig_path.name}')

    df.to_csv(OUT_DIR / 'stable_share_panel.csv', index=False)


if __name__ == '__main__':
    main()
