#!/usr/bin/env python3
"""
Second-stage: systematic share of liquidation response vs log(TVL).

For each CSU, the Pedroni decomposition splits the composite IRF into
  composite = common + idiosyncratic
where the common piece is driven by the panel's common factor (the
market-wide liquidation wave) and idiosyncratic is the protocol-specific
remainder.  We build two summary share metrics:

  sys_share_peak  = common_sq(h*) / (common_sq(h*) + idio_sq(h*))
                    at h* = argmax |composite| over horizons 0..H

  sys_share_area  = sum_h common(h)^2 / sum_h (common(h)^2 + idio(h)^2)
                    integrated across horizons 0..H

Both are in [0,1]; higher = more systemically driven (less insulated).

Depth-insulation hypothesis:
  deeper markets should be LESS driven by the common factor, so we
  expect beta < 0 on log(TVL).
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

HORIZON_MAX = 20   # integrate shares over h = 0..HORIZON_MAX


def load_irf(kind):
    df = pd.read_csv(IRFS_DIR / f'irfs_{kind}.csv')
    return df[(df['variable']=='liquidation') & (df['shock']=='return_shock')].copy()


def main():
    lam = pd.read_csv(IRFS_DIR / 'lambda.csv')[['csu', 'lam_liquidation_liquidation']] \
            .rename(columns={'lam_liquidation_liquidation': 'lam_liq'})

    comp = load_irf('composite')
    comm = load_irf('common')
    idio = load_irf('idiosyncratic')

    rows = []
    for csu in lam['csu']:
        c = comp[(comp['csu']==csu) & (comp['horizon']<=HORIZON_MAX)].sort_values('horizon')
        m = comm[(comm['csu']==csu) & (comm['horizon']<=HORIZON_MAX)].sort_values('horizon')
        i = idio[(idio['csu']==csu) & (idio['horizon']<=HORIZON_MAX)].sort_values('horizon')
        if len(c) == 0 or len(m) == 0 or len(i) == 0:
            continue

        h_star = int(c.iloc[c['irf'].abs().values.argmax()]['horizon'])
        m_peak = float(m[m['horizon']==h_star]['irf'].iloc[0])
        i_peak = float(i[i['horizon']==h_star]['irf'].iloc[0])
        peak_share = m_peak**2 / (m_peak**2 + i_peak**2) if (m_peak**2 + i_peak**2) > 0 else np.nan

        m_ss = float((m['irf'].values**2).sum())
        i_ss = float((i['irf'].values**2).sum())
        area_share = m_ss / (m_ss + i_ss) if (m_ss + i_ss) > 0 else np.nan

        rows.append({
            'csu': csu,
            'h_star': h_star,
            'irf_h_star_composite': float(c.iloc[c['irf'].abs().values.argmax()]['irf']),
            'irf_h_star_common': m_peak,
            'irf_h_star_idio':   i_peak,
            'sys_share_peak':    peak_share,
            'sys_share_area':    area_share,
        })

    shares = pd.DataFrame(rows).merge(lam, on='csu')

    # TVL aggregation
    tvl = pd.read_parquet(TVL_PARQUET)
    tvl_agg = tvl.groupby('csu').agg(
        tvl_supply_mean_usd = ('tvl_supply_usd', 'mean'),
        tvl_borrow_mean_usd = ('tvl_borrow_usd', 'mean'),
    ).reset_index()

    df = shares.merge(tvl_agg, on='csu', how='left')
    df = df.dropna(subset=['tvl_supply_mean_usd'])
    df = df[df['tvl_supply_mean_usd'] > 0]
    df['log_tvl_supply'] = np.log(df['tvl_supply_mean_usd'])

    print(f'Analysis sample: N = {len(df)}')
    print()
    print('Systematic share distribution:')
    print(df[['sys_share_peak', 'sys_share_area']].describe().round(3).to_string())
    print()

    def run_ols(y_col, x_col):
        X = sm.add_constant(df[x_col])
        res = sm.OLS(df[y_col], X).fit(cov_type='HC3')
        print(f'OLS: {y_col} ~ const + {x_col}    (HC3-robust)')
        print(f'  N = {int(res.nobs)}   R^2 = {res.rsquared:.3f}')
        print(f'  const           = {res.params["const"]:+.4f}   SE = {res.bse["const"]:.4f}   '
              f't = {res.tvalues["const"]:+.2f}   p = {res.pvalues["const"]:.4f}')
        print(f'  {x_col:15s} = {res.params[x_col]:+.4f}   SE = {res.bse[x_col]:.4f}   '
              f't = {res.tvalues[x_col]:+.2f}   p = {res.pvalues[x_col]:.4f}')
        ci = res.conf_int().loc[x_col]
        print(f'  95% CI on slope: [{ci[0]:+.4f}, {ci[1]:+.4f}]')
        print()
        return res

    for y_col in ['sys_share_peak', 'sys_share_area']:
        run_ols(y_col, 'log_tvl_supply')

    # Scatter plots
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, ycol, ylab in [(axes[0], 'sys_share_peak', 'Common share at peak horizon'),
                            (axes[1], 'sys_share_area', 'Common share integrated over h=0..20')]:
        x = df['log_tvl_supply'].values
        y = df[ycol].values
        rho = np.corrcoef(x, y)[0, 1]
        X = sm.add_constant(x)
        res = sm.OLS(y, X).fit(cov_type='HC3')
        xs = np.linspace(x.min(), x.max(), 50)
        ys = res.params[0] + res.params[1] * xs
        ax.scatter(x, y, s=40, alpha=0.65, color='#4c72b0', edgecolor='black', linewidth=0.5)
        ax.plot(xs, ys, '-', color='#c7573b', lw=1.6, alpha=0.85,
                label=f'β={res.params[1]:+.3f}  ρ={rho:+.2f}  R²={res.rsquared:.2f}')
        ax.set_xlabel('log(mean TVL supply, USD)')
        ax.set_ylabel(ylab)
        ax.legend(loc='best', fontsize=9)
        ax.grid(alpha=0.3)

    fig.suptitle(f'Systematic share of liquidation IRF vs log(TVL)  (N={len(df)})',
                 fontsize=12, fontweight='bold')
    fig.tight_layout()
    fig_path = OUT_DIR / 'systematic_share_vs_tvl.png'
    fig.savefig(fig_path, dpi=140, bbox_inches='tight')
    plt.close(fig)
    print(f'Saved: {fig_path.name}')

    print()
    print('Sorted by sys_share_area (ascending = more insulated):')
    print(df[['csu','log_tvl_supply','sys_share_peak','sys_share_area','lam_liq']]
          .sort_values('sys_share_area').to_string(index=False, float_format='{:.3f}'.format))

    df.to_csv(OUT_DIR / 'systematic_share.csv', index=False)


if __name__ == '__main__':
    main()
