#!/usr/bin/env python3
"""
IPS + Maddala-Wu panel unit root tests on CUMULATIVE LIQUIDATION VOLUME.

Rationale: TVL was stationary in our 2-year window; BQ long-run identification
needs at least one I(1) variable. Cumulative flows (integrated series) are
natural I(1) candidates — a sum of stationary increments is I(1) by construction.

We construct cum_liq_usd per CSU from panel_svar_data_qualified.parquet
(total_debt_usd is daily liquidation debt), then test both the level and
log(1 + cum_liq) per Pedroni's IPS procedure.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

# Reuse the IPS machinery from the TVL script
from run_unit_root_tvl import (
    ips_test, maddala_wu_test, extract_time_effects, _format
)

PANEL = PROJECT_ROOT / 'data' / 'analysis' / 'panel_svar_data_qualified.parquet'


def main():
    df = pd.read_parquet(PANEL)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['csu', 'date']).reset_index(drop=True)

    print(f"Loaded {PANEL.name}: {df['csu'].nunique()} CSUs, {len(df):,} obs")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    daily_liq = df['total_debt_usd'].fillna(0).clip(lower=0)
    print(f"Daily liq: mean=${daily_liq.mean():,.0f}, median=${daily_liq.median():,.0f}, "
          f"zero-days={(daily_liq == 0).sum()}/{len(daily_liq)}\n")

    # Per-CSU cumulative sum
    df['daily_liq_usd'] = daily_liq
    df['cum_liq_usd'] = df.groupby('csu')['daily_liq_usd'].cumsum()
    df['log_cum_liq'] = np.log1p(df['cum_liq_usd'])
    df['dlog_cum_liq'] = df.groupby('csu')['log_cum_liq'].diff()

    # Time-effect extraction
    for v in ['cum_liq_usd', 'log_cum_liq', 'dlog_cum_liq']:
        df[f'{v}_demeaned'] = extract_time_effects(df, v)

    # Quick summary of the cum series
    print("Per-CSU cumulative-liquidation summary (first/last):")
    summary = df.groupby('csu').agg(
        first_date=('date', 'min'),
        last_date=('date', 'max'),
        final_cum_usd=('cum_liq_usd', 'last'),
        n_obs=('date', 'count'),
    ).reset_index()
    print(summary.to_string(index=False, max_colwidth=30))
    print()

    specs = [
        ('cum_liq_usd',           'ct', 'Cumulative liq (USD) — levels (const + trend)'),
        ('cum_liq_usd_demeaned',  'c',  'Cumulative liq (USD) — levels, time effects extracted'),
        ('log_cum_liq',           'ct', 'log(1 + cum liq) — levels (const + trend)'),
        ('log_cum_liq_demeaned',  'c',  'log(1 + cum liq) — levels, time effects extracted'),
        ('dlog_cum_liq',          'c',  'dlog(1 + cum liq)'),
        ('dlog_cum_liq_demeaned', 'c',  'dlog(1 + cum liq), time effects extracted'),
    ]

    for var, reg, label in specs:
        ips = ips_test(df, var, regression=reg)
        mw = maddala_wu_test(df, var, regression=reg)
        _format(ips, mw, label)
        print()


if __name__ == '__main__':
    main()
