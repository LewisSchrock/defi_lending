#!/usr/bin/env python3
"""
IPS + Maddala-Wu panel unit root test on UTILIZATION.

Uses the same Pedroni-correct machinery as run_unit_root_tvl.py:
  - Time-effect extraction for cross-sectional dependence
  - Step-down lag selection per member
  - IPS asymptotic moments (const: mu=-1.533, v=0.706; const+trend: mu=-2.184, v=0.625)

Utilization = borrow / supply ratio (bounded in [0, 1]); theoretically I(0) by
construction but we test empirically to confirm.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from run_unit_root_tvl import ips_test, maddala_wu_test, extract_time_effects, _format

PANEL = PROJECT_ROOT / 'data' / 'analysis' / 'panel_svar_data_qualified.parquet'


def main():
    df = pd.read_parquet(PANEL)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['csu', 'date']).reset_index(drop=True)

    n_missing_util = df['utilization'].isna().sum()
    print(f"Loaded {PANEL.name}: {df['csu'].nunique()} CSUs, {len(df):,} obs")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Utilization: missing={n_missing_util}, "
          f"mean={df['utilization'].mean():.3f}, "
          f"std={df['utilization'].std():.3f}, "
          f"range=[{df['utilization'].min():.3f}, {df['utilization'].max():.3f}]")
    print()

    # Drop NaNs
    df = df.dropna(subset=['utilization']).copy()

    # Transforms
    df['util']         = df['utilization']
    df['d_util']       = df.groupby('csu')['util'].diff()
    # Logit transform maps (0,1) to real line — useful for a bounded variable
    util_clipped = df['util'].clip(lower=1e-6, upper=1 - 1e-6)
    df['logit_util']   = np.log(util_clipped / (1 - util_clipped))
    df['d_logit_util'] = df.groupby('csu')['logit_util'].diff()

    # Time-effect-extracted versions
    for v in ['util', 'd_util', 'logit_util', 'd_logit_util']:
        df[f'{v}_demeaned'] = extract_time_effects(df, v)

    specs = [
        ('util',              'c',  'Utilization — levels (constant)'),
        ('util',              'ct', 'Utilization — levels (constant + trend)'),
        ('util_demeaned',     'c',  'Utilization — levels, TIME EFFECTS EXTRACTED'),
        ('d_util',            'c',  'Utilization — first difference'),
        ('d_util_demeaned',   'c',  'Utilization — first difference, TIME EFFECTS EXTRACTED'),
        ('logit_util',          'c',  'logit(Utilization) — levels'),
        ('logit_util_demeaned', 'c',  'logit(Utilization) — levels, TIME EFFECTS EXTRACTED'),
        ('d_logit_util',         'c', 'Δ logit(Utilization)'),
        ('d_logit_util_demeaned','c', 'Δ logit(Utilization), TIME EFFECTS EXTRACTED'),
    ]

    for var, reg, label in specs:
        ips = ips_test(df, var, regression=reg)
        mw = maddala_wu_test(df, var, regression=reg)
        _format(ips, mw, label)
        print()


if __name__ == '__main__':
    main()
