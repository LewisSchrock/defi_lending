#!/usr/bin/env python3
"""
Debug version to trace where dates are being dropped in basket return calculation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pandas as pd
import numpy as np

def load_collateral_composition():
    """Load collateral composition data from all chains."""
    overall_path = Path('data/gold/collateral_composition/all_chains_composition.parquet')
    if overall_path.exists():
        return pd.read_parquet(overall_path)
    raise FileNotFoundError("No collateral composition data found")

def load_price_cache():
    """Load historical price cache."""
    path = Path('data/reference/price_cache_ethereum.json')
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

def calculate_basket_returns_debug(comp_df, price_cache, target_csu='aave_v3_arbitrum'):
    """Debug version of basket returns calculation."""

    print(f"\n{'='*80}")
    print(f"Debugging basket returns for: {target_csu}")
    print(f"{'='*80}\n")

    # Filter to target CSU
    csu_data = comp_df[comp_df['csu'] == target_csu].copy()

    print(f"Composition data for {target_csu}:")
    print(f"  Total rows: {len(csu_data):,}")
    print(f"  Unique dates: {csu_data['date'].nunique()}")
    print(f"  Date range: {csu_data['date'].min()} to {csu_data['date'].max()}")
    print()

    dates = sorted(csu_data['date'].unique())
    print(f"Sorted dates list:")
    print(f"  Length: {len(dates)}")
    print(f"  First date: {dates[0]}")
    print(f"  Last date: {dates[-1]}")
    print()

    # Now iterate like the original function
    results = []
    skipped_dates = []

    for i, date in enumerate(dates):
        if i == 0:
            continue  # Need previous day for returns

        prev_date = dates[i - 1]

        # Get weights from previous day
        prev_comp = csu_data[csu_data['date'] == prev_date]

        if prev_comp.empty:
            print(f"WARNING: No prev composition for date {date} (prev_date={prev_date})")
            skipped_dates.append({'date': date, 'reason': 'no_prev_comp'})
            continue

        # Calculate weighted return
        basket_return = 0.0
        total_weight = 0.0

        for _, row in prev_comp.iterrows():
            symbol = row['symbol']
            weight = row.get('pct_of_total')

            if pd.isna(weight) or weight <= 0:
                continue

            weight = weight / 100.0

            # Get prices
            price_today_key = f"{date}_{symbol}"
            price_prev_key = f"{prev_date}_{symbol}"

            price_today = price_cache.get(price_today_key)
            price_prev = price_cache.get(price_prev_key)

            if price_today and price_prev and price_today > 0 and price_prev > 0:
                log_return = np.log(price_today) - np.log(price_prev)
                basket_return += weight * log_return
                total_weight += weight

        # Check coverage
        if total_weight > 0.5:
            results.append({
                'date': date,
                'csu': target_csu,
                'basket_return': basket_return,
                'weight_coverage': total_weight,
            })
        else:
            skipped_dates.append({
                'date': date,
                'reason': 'insufficient_weight',
                'weight': total_weight
            })

    print(f"Results:")
    print(f"  Successfully calculated: {len(results)} dates")
    print(f"  Skipped: {len(skipped_dates)} dates")
    print(f"  Expected: {len(dates) - 1} dates (minus first)")
    print()

    if skipped_dates:
        print(f"First 10 skipped dates:")
        for item in skipped_dates[:10]:
            print(f"  {item}")

    return pd.DataFrame(results)


def main():
    print("Loading data...")
    comp_df = load_collateral_composition()
    price_cache = load_price_cache()

    print(f"  Composition: {len(comp_df):,} rows")
    print(f"  Price cache: {len(price_cache):,} entries")

    # Run debug calculation
    basket_df = calculate_basket_returns_debug(comp_df, price_cache)

    print(f"\n{'='*80}")
    print("Final basket returns DataFrame:")
    print(f"{'='*80}")
    print(f"  Rows: {len(basket_df)}")
    if len(basket_df) > 0:
        print(f"  Date range: {basket_df['date'].min()} to {basket_df['date'].max()}")
        print(f"  Mean weight coverage: {basket_df['weight_coverage'].mean():.3f}")


if __name__ == '__main__':
    main()
