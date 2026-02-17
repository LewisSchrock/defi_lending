#!/usr/bin/env python3
"""
Diagnose Volatility Coverage Issues

Traces through the basket return calculation to identify where data is being dropped.
Does NOT modify any data or code - diagnostic only.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pandas as pd
import numpy as np
from collections import defaultdict

def diagnose_csu(csu, comp_df, price_cache, date_range=None):
    """Diagnose why a CSU has low volatility coverage."""

    csu_data = comp_df[comp_df['csu'] == csu].copy()

    if date_range:
        csu_data = csu_data[(csu_data['date'] >= date_range[0]) &
                           (csu_data['date'] <= date_range[1])]

    dates = sorted(csu_data['date'].unique())

    print(f"\n{'='*80}")
    print(f"Diagnosing: {csu}")
    print(f"{'='*80}")
    print(f"Date range: {dates[0]} to {dates[-1]}")
    print(f"Total dates: {len(dates)}")
    print()

    # Track failures by reason
    stats = {
        'total_dates': len(dates) - 1,  # Minus 1 for first date
        'no_prev_comp': 0,
        'insufficient_weight': 0,
        'success': 0,
        'weight_distribution': [],
    }

    insufficient_weight_details = []

    for i, date in enumerate(dates):
        if i == 0:
            continue  # Need previous day

        prev_date = dates[i - 1]

        # Get previous day composition
        prev_comp = csu_data[csu_data['date'] == prev_date]

        if prev_comp.empty:
            stats['no_prev_comp'] += 1
            continue

        # Calculate weighted return
        total_weight = 0.0
        missing_prices = []

        for _, row in prev_comp.iterrows():
            symbol = row['symbol']
            weight = row.get('pct_of_total')

            if pd.isna(weight) or weight <= 0:
                continue

            weight = weight / 100.0  # Convert to decimal

            # Check prices
            price_today_key = f"{date}_{symbol}"
            price_prev_key = f"{prev_date}_{symbol}"

            price_today = price_cache.get(price_today_key)
            price_prev = price_cache.get(price_prev_key)

            if price_today and price_prev and price_today > 0 and price_prev > 0:
                total_weight += weight
            else:
                missing_prices.append({
                    'symbol': symbol,
                    'weight': weight * 100,
                    'has_today': bool(price_today),
                    'has_prev': bool(price_prev),
                })

        stats['weight_distribution'].append(total_weight)

        if total_weight > 0.5:
            stats['success'] += 1
        else:
            stats['insufficient_weight'] += 1

            if len(insufficient_weight_details) < 5:  # Keep first 5 examples
                insufficient_weight_details.append({
                    'date': date,
                    'total_weight': total_weight,
                    'missing_prices': missing_prices,
                    'n_tokens': len(prev_comp),
                })

    # Print results
    print("Results:")
    print(f"  Total dates analyzed: {stats['total_dates']}")
    print(f"  Successful (weight >50%): {stats['success']} ({stats['success']/stats['total_dates']*100:.1f}%)")
    print(f"  Failed - insufficient weight: {stats['insufficient_weight']} ({stats['insufficient_weight']/stats['total_dates']*100:.1f}%)")
    print(f"  Failed - no prev composition: {stats['no_prev_comp']}")
    print()

    # Weight distribution
    if stats['weight_distribution']:
        weights = stats['weight_distribution']
        print("Weight Coverage Distribution:")
        print(f"  Mean: {np.mean(weights):.3f}")
        print(f"  Median: {np.median(weights):.3f}")
        print(f"  Min: {np.min(weights):.3f}")
        print(f"  Max: {np.max(weights):.3f}")
        print()

        # Histogram
        bins = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        hist, _ = np.histogram(weights, bins=bins)
        print("  Weight distribution:")
        for i in range(len(bins)-1):
            count = hist[i]
            pct = count / len(weights) * 100
            print(f"    {bins[i]:.1f}-{bins[i+1]:.1f}: {count:>4} ({pct:>5.1f}%)")
        print()

    # Show examples of insufficient weight
    if insufficient_weight_details:
        print("Examples of dates with insufficient weight (<50%):")
        print()
        for detail in insufficient_weight_details[:3]:
            date = detail['date']
            weight = detail['total_weight']
            missing = detail['missing_prices']

            print(f"  {date}: total_weight={weight:.3f}")
            if missing:
                print(f"    Tokens without prices:")
                for m in missing[:5]:
                    today = '✓' if m['has_today'] else '✗'
                    prev = '✓' if m['has_prev'] else '✗'
                    print(f"      {m['symbol']:<15} weight:{m['weight']:>5.1f}%  today:{today} prev:{prev}")
            print()

    return stats


def main():
    print("="*80)
    print("Volatility Coverage Diagnostic")
    print("="*80)

    # Load data
    print("\nLoading data...")
    comp = pd.read_parquet('data/gold/collateral_composition/all_chains_composition.parquet')

    with open('data/reference/price_cache_ethereum.json') as f:
        price_cache = json.load(f)

    print(f"  Composition: {len(comp):,} rows, {comp['csu'].nunique()} CSUs")
    print(f"  Price cache: {len(price_cache):,} entries")

    # Test CSUs with different coverage levels
    test_csus = [
        ('aave_v3_ethereum', '2024-01-01', '2024-12-31'),  # High coverage (99%)
        ('aave_v3_arbitrum', '2024-01-01', '2024-12-31'),  # Medium coverage (62%)
        ('aave_v3_linea', '2025-02-11', '2025-12-31'),     # Low coverage (26%)
    ]

    results = {}

    for csu, start, end in test_csus:
        stats = diagnose_csu(csu, comp, price_cache, date_range=(start, end))
        results[csu] = stats

    # Summary
    print("\n" + "="*80)
    print("Summary Comparison")
    print("="*80)
    print()
    print(f"{'CSU':<40} {'Success Rate':<15} {'Main Issue'}")
    print("-"*80)

    for csu, stats in results.items():
        if stats['total_dates'] > 0:
            success_rate = stats['success'] / stats['total_dates'] * 100

            if stats['insufficient_weight'] > stats['total_dates'] * 0.1:
                issue = f"{stats['insufficient_weight']} dates with <50% weight"
            else:
                issue = "Good coverage"

            print(f"{csu:<40} {success_rate:>5.1f}%          {issue}")


if __name__ == '__main__':
    main()
