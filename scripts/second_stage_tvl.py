#!/usr/bin/env python3
"""
Second-stage: log(TVL) predicts per-CSU lambda_liq and peak IRF.

TVL definition:
  TVL_i = mean daily tvl_supply_usd for CSU i over the sample window
  (standard DeFi supply-side TVL, morpho excluded for corrupted pricing).

Robustness:
  log(TVL_borrow_i) = mean daily tvl_borrow_usd for CSU i.

OLS with HC3 robust SEs.
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
TVL_PARQUET  = PROJECT_ROOT / 'data' / 'analysis' / 'tvl_borrow_supply_daily_clean.parquet'
OUT_DIR      = PROJECT_ROOT / 'results' / 'data_analysis' / 'second_stage'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def chain_short_to_name(csu):
    """Normalize CSU name so that it matches tvl_borrow_supply_daily_clean (base CSU level)."""
    # The clean TVL panel uses base CSU names directly (e.g. aave_v3_arbitrum, compound_v3_arb_usdc)
    # Our SVAR panel is also at the base-CSU level, so no mapping needed in this version.
    return csu


def main():
    # Per-CSU lambda and IRF_h1 (composite)
    lam = pd.read_csv(IRFS_DIR / 'lambda.csv')[['csu', 'lam_liquidation_liquidation']] \
            .rename(columns={'lam_liquidation_liquidation': 'lam_liq'})

    irfs = pd.read_csv(IRFS_DIR / 'irfs_composite.csv')
    irf_h1 = irfs[(irfs['variable']=='liquidation') &
                  (irfs['shock']=='return_shock') &
                  (irfs['horizon']==1)][['csu','irf']].rename(columns={'irf':'irf_h1'})

    y = lam.merge(irf_h1, on='csu')

    # Cross-sectional TVL: mean daily supply and borrow per CSU
    tvl = pd.read_parquet(TVL_PARQUET)
    tvl_agg = tvl.groupby('csu').agg(
        tvl_supply_mean_usd = ('tvl_supply_usd', 'mean'),
        tvl_borrow_mean_usd = ('tvl_borrow_usd', 'mean'),
        tvl_days            = ('date', 'count'),
    ).reset_index()
    print(f'TVL panel CSUs: {len(tvl_agg)}   SVAR CSUs: {len(y)}')

    df = y.merge(tvl_agg, on='csu', how='left')
    missing = df[df['tvl_supply_mean_usd'].isna()]['csu'].tolist()
    if missing:
        print(f'\nMissing TVL for {len(missing)} SVAR CSUs: {missing}')
    df = df.dropna(subset=['tvl_supply_mean_usd'])
    df = df[df['tvl_supply_mean_usd'] > 0]
    df['log_tvl_supply'] = np.log(df['tvl_supply_mean_usd'])
    df = df[df['tvl_borrow_mean_usd'] > 0]
    df['log_tvl_borrow'] = np.log(df['tvl_borrow_mean_usd'])

    print(f'\nAnalysis sample: N = {len(df)}')
    print(f'log(TVL_supply):  range = [{df["log_tvl_supply"].min():.2f}, {df["log_tvl_supply"].max():.2f}]')
    print(f'                  mean  = {df["log_tvl_supply"].mean():.2f},  SD = {df["log_tvl_supply"].std():.2f}')
    print(f'log(TVL_borrow):  range = [{df["log_tvl_borrow"].min():.2f}, {df["log_tvl_borrow"].max():.2f}]')

    def run_ols(y_col, x_col, label):
        X = sm.add_constant(df[x_col])
        res = sm.OLS(df[y_col], X).fit(cov_type='HC3')
        print(f'\nOLS: {y_col} ~ const + {x_col}    (HC3-robust)')
        print(f'  N = {int(res.nobs)}   R^2 = {res.rsquared:.3f}')
        print(f'  const  = {res.params["const"]:+.4f}   SE = {res.bse["const"]:.4f}   t = {res.tvalues["const"]:+.2f}   p = {res.pvalues["const"]:.4f}')
        print(f'  {x_col:14s} = {res.params[x_col]:+.4f}   SE = {res.bse[x_col]:.4f}   t = {res.tvalues[x_col]:+.2f}   p = {res.pvalues[x_col]:.4f}')
        ci = res.conf_int().loc[x_col]
        print(f'  95% CI on slope: [{ci[0]:+.4f}, {ci[1]:+.4f}]')
        return res

    for y_col in ['lam_liq', 'irf_h1']:
        run_ols(y_col, 'log_tvl_supply', 'TVL supply')
        run_ols(y_col, 'log_tvl_borrow', 'TVL borrow (robustness)')

    # Scatter plots
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    specs = [
        (axes[0,0], 'log_tvl_supply', 'lam_liq',  r'$\lambda_{liq}$',       'log(mean TVL supply, USD)'),
        (axes[0,1], 'log_tvl_supply', 'irf_h1',   'IRF at h=1',              'log(mean TVL supply, USD)'),
        (axes[1,0], 'log_tvl_borrow', 'lam_liq',  r'$\lambda_{liq}$',       'log(mean TVL borrow, USD)'),
        (axes[1,1], 'log_tvl_borrow', 'irf_h1',   'IRF at h=1',              'log(mean TVL borrow, USD)'),
    ]
    for ax, xc, yc, ylab, xlab in specs:
        x = df[xc].values; y = df[yc].values
        rho = np.corrcoef(x, y)[0, 1]
        X = sm.add_constant(x)
        res = sm.OLS(y, X).fit(cov_type='HC3')
        xs = np.linspace(x.min(), x.max(), 50)
        ys = res.params[0] + res.params[1] * xs
        ax.scatter(x, y, s=40, alpha=0.65, color='#4c72b0', edgecolor='black', linewidth=0.5)
        ax.plot(xs, ys, '-', color='#c7573b', lw=1.6, alpha=0.85,
                label=f'β={res.params[1]:+.3f}  ρ={rho:+.2f}  R²={res.rsquared:.2f}')
        ax.axhline(0, color='black', lw=0.6, ls=':')
        ax.set_xlabel(xlab)
        ax.set_ylabel(ylab)
        ax.legend(loc='best', fontsize=9)
        ax.grid(alpha=0.3)

    fig.suptitle(f'Second-stage: per-CSU outcomes vs log(TVL)  (N={len(df)})',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig_path = OUT_DIR / 'tvl_second_stage.png'
    fig.savefig(fig_path, dpi=140, bbox_inches='tight')
    plt.close(fig)

    print(f'\nSaved: {fig_path.name}')

    print('\nSorted by log(TVL_supply):')
    print(df[['csu','log_tvl_supply','log_tvl_borrow','lam_liq','irf_h1']]
          .sort_values('log_tvl_supply').to_string(index=False, float_format='{:.3f}'.format))

    df.to_csv(OUT_DIR / 'second_stage_tvl.csv', index=False)


if __name__ == '__main__':
    main()
