#!/usr/bin/env python3
"""
IPS + Maddala-Wu panel unit root test on TOTAL BORROWED (outstanding debt).

Uses the same qualified panel as price_utilization.ipynb to keep consistency
with the BQ setup. Tests USD levels, log levels, and first differences.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from run_unit_root_tvl import ips_test, maddala_wu_test, extract_time_effects, _format

PANEL = PROJECT_ROOT / 'data' / 'analysis' / 'tvl_borrow_supply_daily_clean.parquet'


def main():
    df = pd.read_parquet(PANEL)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['csu', 'date']).reset_index(drop=True)
    df = df.rename(columns={'tvl_borrow_usd': 'total_borrow_usd'})

    print(f"Loaded {PANEL.name}: {df['csu'].nunique()} CSUs, {len(df):,} obs")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"total_borrow_usd: mean=${df['total_borrow_usd'].mean():,.0f}, "
          f"median=${df['total_borrow_usd'].median():,.0f}")
    print()

    df = df.dropna(subset=['total_borrow_usd']).copy()
    df = df[df['total_borrow_usd'] > 0].copy()  # drop zeros so log works

    # Transforms
    df['borrow_usd']      = df['total_borrow_usd']
    df['log_borrow_usd']  = np.log(df['total_borrow_usd'])
    df['dlog_borrow_usd'] = df.groupby('csu')['log_borrow_usd'].diff()

    for v in ['borrow_usd', 'log_borrow_usd', 'dlog_borrow_usd']:
        df[f'{v}_demeaned'] = extract_time_effects(df, v)

    specs = [
        ('borrow_usd',              'c',  'Total Borrow (USD levels) — constant'),
        ('borrow_usd',              'ct', 'Total Borrow (USD levels) — constant + trend'),
        ('borrow_usd_demeaned',     'c',  'Total Borrow (USD levels) — TIME EFFECTS EXTRACTED'),
        ('log_borrow_usd',          'c',  'log(Total Borrow USD) — constant'),
        ('log_borrow_usd',          'ct', 'log(Total Borrow USD) — constant + trend'),
        ('log_borrow_usd_demeaned', 'c',  'log(Total Borrow USD) — TIME EFFECTS EXTRACTED'),
        ('dlog_borrow_usd',         'c',  'Δ log(Total Borrow USD)'),
        ('dlog_borrow_usd_demeaned','c',  'Δ log(Total Borrow USD) — TIME EFFECTS EXTRACTED'),
    ]

    for var, reg, label in specs:
        ips = ips_test(df, var, regression=reg)
        mw = maddala_wu_test(df, var, regression=reg)
        _format(ips, mw, label)
        print()


if __name__ == '__main__':
    main()
