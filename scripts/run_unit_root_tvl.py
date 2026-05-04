#!/usr/bin/env python3
"""
IPS + Maddala-Wu panel unit root tests on tvl_borrow_supply_daily.parquet.

Follows Pedroni's prescription (Econ 471 packet, pp. 61-64, 99-103):
  1. Extract time effects (demean by cross-sectional mean at each date)
     to handle cross-sectional dependence from common crypto-market factors.
  2. Per-member ADF with step-down lag selection (start high, drop until
     the largest lag's coefficient is significant at 5% two-tailed).
  3. Construct IPS: Z = sqrt(N/v) * (t-bar - mu), compare to N(0,1) left tail.
  4. Construct Maddala-Wu Fisher: P = -2*sum(ln p_i), compare to chi2(2N).

We report both with and without time-effect extraction so the effect of
cross-sectional dependence is visible.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.tsa.stattools import adfuller

PROJECT_ROOT = Path(__file__).parent.parent
PARQUET = PROJECT_ROOT / 'data' / 'analysis' / 'tvl_borrow_supply_daily.parquet'
PRICE_CACHE = PROJECT_ROOT / 'data' / 'reference' / 'price_cache_all.json'


def load_eth_prices():
    """Load ETH USD price per date from the symbol cache."""
    with open(PRICE_CACHE) as f:
        cache = json.load(f)
    records = []
    for key, price in cache.items():
        if key.endswith('_ETH') and price and price > 0:
            date = key[:-4]  # strip '_ETH'
            records.append((date, float(price)))
    df = pd.DataFrame(records, columns=['date', 'eth_price_usd'])
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)

# IPS (2003) asymptotic moments for ADF with constant (no trend), demeaned
# These are invariant to lag truncation as T -> infinity (Pedroni packet p. 102-103)
IPS_MU_C = -1.533
IPS_V_C = 0.706
# With constant + trend
IPS_MU_CT = -2.184
IPS_V_CT = 0.625


def _fit_adf(y, K, regression='c'):
    """
    Fit ADF regression manually:
        dy_t = alpha + [beta*t] + rho*y_{t-1} + sum_{k=1..K} phi_k * dy_{t-k} + eta_t

    Returns: (t_rho, t_phi_K, nobs) or (None, None, None) if not enough obs.
    t_phi_K is None when K=0.
    """
    y = np.asarray(y, dtype=float)
    dy = np.diff(y)
    T_diff = len(dy)
    if T_diff - K < 10:
        return None, None, None

    Y = dy[K:]
    n = len(Y)

    cols = [np.ones(n)]
    if regression == 'ct':
        cols.append(np.arange(K + 1, K + 1 + n, dtype=float))  # trend index
    cols.append(y[K:-1])  # y_{t-1}
    rho_idx = len(cols) - 1
    for k in range(1, K + 1):
        cols.append(dy[K - k:T_diff - k])

    X = np.column_stack(cols)
    p = X.shape[1]
    if n <= p:
        return None, None, None

    XtX = X.T @ X
    try:
        XtX_inv = np.linalg.inv(XtX)
    except np.linalg.LinAlgError:
        return None, None, None

    beta = XtX_inv @ X.T @ Y
    resid = Y - X @ beta
    sigma2 = (resid @ resid) / (n - p)
    se = np.sqrt(np.diag(sigma2 * XtX_inv))
    t_stats = beta / se

    t_rho = t_stats[rho_idx]
    t_phi_K = t_stats[-1] if K > 0 else None
    return t_rho, t_phi_K, n


def step_down_adf(series, maxlag=None, alpha=0.05, regression='c'):
    """
    Pedroni step-down lag selection (packet p. 101): start at K_max, drop K
    until the largest lag's t-stat is significant at alpha (two-sided).
    Returns (t_rho, K_selected, nobs) or (None, None, None) on failure.
    """
    s = pd.Series(series).dropna().values
    T = len(s)
    if T < 30:
        return None, None, None
    if maxlag is None:
        maxlag = max(1, int(12 * (T / 100) ** 0.25))  # Schwert

    crit = scipy_stats.norm.ppf(1 - alpha / 2)  # ~1.96

    for K in range(maxlag, 0, -1):
        t_rho, t_phi_K, n = _fit_adf(s, K, regression)
        if t_rho is None or t_phi_K is None:
            continue
        if abs(t_phi_K) > crit:
            return t_rho, K, n

    t_rho, _, n = _fit_adf(s, 0, regression)
    if t_rho is None:
        return None, None, None
    return t_rho, 0, n


def ips_test(df, var, regression='c', maxlag=None):
    """Run IPS test across CSUs. Returns dict with t-bar, Z, p-value, etc."""
    t_stats, K_used, Ns = [], [], []
    for _, grp in df.groupby('csu'):
        s = grp[var].dropna()
        if s.std() < 1e-12:
            continue
        t_rho, K, n = step_down_adf(s.values, maxlag=maxlag, regression=regression)
        if t_rho is None or np.isnan(t_rho):
            continue
        t_stats.append(t_rho)
        K_used.append(K)
        Ns.append(n)

    N = len(t_stats)
    if N == 0:
        return None

    t_arr = np.array(t_stats)
    mu, v = (IPS_MU_CT, IPS_V_CT) if regression == 'ct' else (IPS_MU_C, IPS_V_C)
    t_bar = t_arr.mean()
    Z = np.sqrt(N / v) * (t_bar - mu)
    p = scipy_stats.norm.cdf(Z)

    return {
        'N': N, 't_bar': t_bar, 'Z': Z, 'p': p,
        'K_median': int(np.median(K_used)), 'K_max': int(np.max(K_used)),
        'reject_individual': int((t_arr < scipy_stats.norm.ppf(0.05)).sum()),
    }


def maddala_wu_test(df, var, regression='c', maxlag=None):
    """Fisher-type test using p-values from per-CSU ADF."""
    p_vals = []
    for _, grp in df.groupby('csu'):
        s = grp[var].dropna()
        if len(s) < 30 or s.std() < 1e-12:
            continue
        try:
            # Use statsmodels' adfuller just to get the p-value (MacKinnon surface)
            _, p_adf, _, _, _, _ = adfuller(
                s.values, maxlag=maxlag, autolag='AIC', regression=regression
            )
            p_vals.append(p_adf)
        except Exception:
            continue
    N = len(p_vals)
    if N == 0:
        return None
    p_arr = np.clip(np.array(p_vals), 1e-15, 1.0)
    P = -2 * np.log(p_arr).sum()
    p_panel = 1 - scipy_stats.chi2.cdf(P, 2 * N)
    return {'N': N, 'P': P, 'p': p_panel}


def _format(r_ips, r_mw, label):
    print(f"{'='*74}")
    print(f"  {label}")
    print(f"{'='*74}")
    if r_ips is None:
        print("  IPS: insufficient data"); return
    verdict_ips = "REJECT H0 (stationary)" if r_ips['p'] < 0.05 else "FAIL TO REJECT H0 (unit root)"
    print(f"  IPS:  N={r_ips['N']}  t-bar={r_ips['t_bar']:+.3f}  "
          f"Z={r_ips['Z']:+.3f}  p={r_ips['p']:.4f}  "
          f"K(med/max)={r_ips['K_median']}/{r_ips['K_max']}  "
          f"individ-reject={r_ips['reject_individual']}/{r_ips['N']}")
    print(f"        {verdict_ips}")
    if r_mw is not None:
        verdict_mw = "REJECT H0 (stationary)" if r_mw['p'] < 0.05 else "FAIL TO REJECT H0 (unit root)"
        print(f"  MW:   N={r_mw['N']}  P={r_mw['P']:.2f}  p={r_mw['p']:.4f}")
        print(f"        {verdict_mw}")


def extract_time_effects(df, var):
    """Demean by cross-sectional average at each date (Pedroni p. 51, 62)."""
    means = df.groupby('date')[var].transform('mean')
    return df[var] - means


def main():
    df = pd.read_parquet(PARQUET)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['csu', 'date']).reset_index(drop=True)
    print(f"Loaded {PARQUET.name}: {df['csu'].nunique()} CSUs, {len(df):,} obs")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}\n")

    # Merge ETH prices
    eth = load_eth_prices()
    df = df.merge(eth, on='date', how='left')
    missing_eth = df['eth_price_usd'].isna().sum()
    if missing_eth:
        print(f"WARNING: {missing_eth} rows missing ETH price — filling with nearest available")
        df = df.sort_values(['csu', 'date'])
        df['eth_price_usd'] = df.groupby('csu')['eth_price_usd'].ffill().bfill()

    # Build USD-denominated transforms
    df['log_supply'] = np.log(df['tvl_supply_usd'].where(df['tvl_supply_usd'] > 0))
    df['log_borrow'] = np.log(df['tvl_borrow_usd'].where(df['tvl_borrow_usd'] > 0))
    df['dlog_supply'] = df.groupby('csu')['log_supply'].diff()
    df['dlog_borrow'] = df.groupby('csu')['log_borrow'].diff()

    # ETH-denominated transforms (TVL_in_ETH = TVL_USD / ETH_price_USD)
    df['supply_eth'] = df['tvl_supply_usd'] / df['eth_price_usd']
    df['borrow_eth'] = df['tvl_borrow_usd'] / df['eth_price_usd']
    df['log_supply_eth'] = np.log(df['supply_eth'].where(df['supply_eth'] > 0))
    df['log_borrow_eth'] = np.log(df['borrow_eth'].where(df['borrow_eth'] > 0))
    df['dlog_supply_eth'] = df.groupby('csu')['log_supply_eth'].diff()
    df['dlog_borrow_eth'] = df.groupby('csu')['log_borrow_eth'].diff()

    # Time-effect-extracted versions (key Pedroni step)
    for v in ['log_supply', 'log_borrow', 'dlog_supply', 'dlog_borrow',
              'log_supply_eth', 'log_borrow_eth', 'dlog_supply_eth', 'dlog_borrow_eth']:
        df[f'{v}_demeaned'] = extract_time_effects(df, v)

    specs = [
        # (variable, regression_mode, label)
        # --- USD-denominated ---
        ('log_supply',          'ct', 'USD  SUPPLY — log levels (const + trend)'),
        ('log_supply_demeaned', 'c',  'USD  SUPPLY — log levels, time effects extracted'),
        ('dlog_supply',         'c',  'USD  SUPPLY — dlog'),
        ('dlog_supply_demeaned','c',  'USD  SUPPLY — dlog, time effects extracted'),
        ('log_borrow',          'ct', 'USD  BORROW — log levels (const + trend)'),
        ('log_borrow_demeaned', 'c',  'USD  BORROW — log levels, time effects extracted'),
        ('dlog_borrow',         'c',  'USD  BORROW — dlog'),
        ('dlog_borrow_demeaned','c',  'USD  BORROW — dlog, time effects extracted'),
        # --- ETH-denominated ---
        ('log_supply_eth',          'ct', 'ETH  SUPPLY — log levels (const + trend)'),
        ('log_supply_eth_demeaned', 'c',  'ETH  SUPPLY — log levels, time effects extracted'),
        ('dlog_supply_eth',         'c',  'ETH  SUPPLY — dlog'),
        ('dlog_supply_eth_demeaned','c',  'ETH  SUPPLY — dlog, time effects extracted'),
        ('log_borrow_eth',          'ct', 'ETH  BORROW — log levels (const + trend)'),
        ('log_borrow_eth_demeaned', 'c',  'ETH  BORROW — log levels, time effects extracted'),
        ('dlog_borrow_eth',         'c',  'ETH  BORROW — dlog'),
        ('dlog_borrow_eth_demeaned','c',  'ETH  BORROW — dlog, time effects extracted'),
    ]

    for var, reg, label in specs:
        ips = ips_test(df, var, regression=reg)
        mw = maddala_wu_test(df, var, regression=reg)
        _format(ips, mw, label)
        print()


if __name__ == '__main__':
    main()
