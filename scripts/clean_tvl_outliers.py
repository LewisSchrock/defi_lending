#!/usr/bin/env python3
"""
Clean pricing outliers from tvl_borrow_supply_daily.parquet.

Rules:
  1. Drop morpho_ethereum entirely (31 bad rows / 622; unrecoverable).

Single-day pricing glitches in other CSUs are left in place.

Output: data/analysis/tvl_borrow_supply_daily_clean.parquet
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
SRC = PROJECT_ROOT / 'data' / 'analysis' / 'tvl_borrow_supply_daily.parquet'
DST = PROJECT_ROOT / 'data' / 'analysis' / 'tvl_borrow_supply_daily_clean.parquet'

DROP_CSUS = ['morpho_ethereum']


def main():
    df = pd.read_parquet(SRC)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['csu', 'date']).reset_index(drop=True)

    print(f"Before cleanup: {df['csu'].nunique()} CSUs, {len(df):,} obs")

    before = len(df)
    df_clean = df[~df['csu'].isin(DROP_CSUS)].copy()
    print(f"  Dropped CSU(s) entirely: {DROP_CSUS}")
    print(f"    Removed {before - len(df_clean):,} rows")

    print(f"\nAfter cleanup: {df_clean['csu'].nunique()} CSUs, {len(df_clean):,} obs")

    df_clean.to_parquet(DST, index=False)
    print(f"\nSaved: {DST}")


if __name__ == '__main__':
    main()
