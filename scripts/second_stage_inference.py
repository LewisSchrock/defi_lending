#!/usr/bin/env python3
"""
Second-stage OLS inference:
  IRF_{i,h} = alpha + beta * lambda_liq_i + epsilon_i

Estimated per horizon h, per IRF type (composite / common / idiosyncratic).
HC3-robust standard errors.

Outputs:
  - Table printed to stdout (headline coefficients at each horizon)
  - results/data_analysis/second_stage/ols_horizon_table.csv
  - results/data_analysis/second_stage/ols_progression.png
    (beta and 95% CI as functions of horizon)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent
IRFS_DIR     = PROJECT_ROOT / 'results' / 'pedroni' / 'bivariate_return_liq'
OUT_DIR      = PROJECT_ROOT / 'results' / 'data_analysis' / 'second_stage'
OUT_DIR.mkdir(parents=True, exist_ok=True)

IRF_TYPES = ['composite', 'common', 'idiosyncratic']


def main():
    lam = pd.read_csv(IRFS_DIR / 'lambda.csv')[['csu', 'lam_liquidation_liquidation']] \
            .rename(columns={'lam_liquidation_liquidation': 'lam_liq'})

    all_rows = []
    fig, axes = plt.subplots(1, len(IRF_TYPES), figsize=(15, 4.5), sharey=True)

    for ax, it in zip(axes, IRF_TYPES):
        irfs = pd.read_csv(IRFS_DIR / f'irfs_{it}.csv')
        sub = irfs[(irfs['variable']=='liquidation') & (irfs['shock']=='return_shock')]
        horizons = sorted(sub['horizon'].unique())

        rows = []
        for h in horizons:
            df = sub[sub['horizon']==h][['csu','irf']].merge(lam, on='csu').dropna()
            y = df['irf'].values
            X = sm.add_constant(df['lam_liq'].values)
            res = sm.OLS(y, X).fit(cov_type='HC3')
            ci_lo, ci_hi = res.conf_int()[1]
            rows.append({
                'irf_type': it, 'horizon': h, 'N': int(res.nobs),
                'alpha':    res.params[0], 'alpha_se': res.bse[0], 'alpha_p': res.pvalues[0],
                'beta':     res.params[1], 'beta_se':  res.bse[1], 'beta_t': res.tvalues[1],
                'beta_p':   res.pvalues[1], 'beta_ci_lo': ci_lo, 'beta_ci_hi': ci_hi,
                'r2':       res.rsquared,  'r2_adj':    res.rsquared_adj,
            })

        rdf = pd.DataFrame(rows)
        all_rows.append(rdf)

        # Progression plot: beta with 95% CI ribbon
        ax.fill_between(rdf['horizon'], rdf['beta_ci_lo'], rdf['beta_ci_hi'],
                        color='#4c72b0', alpha=0.22, label='95% CI (HC3)')
        ax.plot(rdf['horizon'], rdf['beta'], '-o', color='#2d4a7a', markersize=4)
        ax.axhline(0, color='black', lw=0.6, ls=':')
        ax.set_xlabel('Horizon h')
        ax.set_ylabel(r'OLS $\beta$: IRF on $\lambda_{liq}$')
        ax.set_title(f'[{it}]')
        ax.legend(loc='best', fontsize=8)
        ax.grid(alpha=0.3)

    fig.suptitle(r'Second-stage OLS  $\mathrm{IRF}_{i,h} = \alpha + \beta \cdot \lambda_{liq,i} + \varepsilon_i$   by horizon',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    out_fig = OUT_DIR / 'ols_progression.png'
    fig.savefig(out_fig, dpi=130, bbox_inches='tight')
    plt.close(fig)

    full = pd.concat(all_rows, ignore_index=True)
    full.to_csv(OUT_DIR / 'ols_horizon_table.csv', index=False)

    # Print a compact summary table for selected horizons
    print(f'N = {int(full["N"].iloc[0])} CSUs')
    print()
    print(f'{"type":14s} {"h":>3s} {"beta":>8s} {"SE":>7s} {"t":>7s} {"p":>7s} {"CI_lo":>8s} {"CI_hi":>8s} {"R2":>6s}')
    print('-' * 78)
    key_horizons = [0, 1, 2, 5, 10, 15, 30]
    for it in IRF_TYPES:
        for h in key_horizons:
            r = full[(full['irf_type']==it) & (full['horizon']==h)]
            if r.empty: continue
            r = r.iloc[0]
            print(f'{it:14s} {h:>3d} {r["beta"]:+8.3f} {r["beta_se"]:7.3f} '
                  f'{r["beta_t"]:+7.2f} {r["beta_p"]:7.4f} '
                  f'{r["beta_ci_lo"]:+8.3f} {r["beta_ci_hi"]:+8.3f} {r["r2"]:6.3f}')
        print()
    print(f'Saved: {out_fig.name}')
    print(f'Saved: ols_horizon_table.csv')


if __name__ == '__main__':
    main()
