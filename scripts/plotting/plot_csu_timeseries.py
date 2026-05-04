#!/usr/bin/env python3
"""
Plot per-CSU timeseries:
  Left:  Liquidation volume (filled area) + liquidation count (line, right y-axis)
  Right: Collateral basket price level, broken down by top 4 tokens (stacked area)
One PNG per CSU in results/pedroni/csu_timeseries/.
"""

import pandas as pd
import numpy as np
import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def load_stablecoins():
    """Load stablecoin set from token_classification.csv."""
    csv_path = PROJECT_ROOT / 'results' / 'data_analysis' / 'token_prices' / 'token_classification.csv'
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        stable = set(df.loc[df['classification'] == 'stablecoin', 'token'].tolist())
        print(f"Loaded {len(stable)} stablecoins from {csv_path.name}")
        return stable
    print(f"WARNING: {csv_path} not found, using empty stablecoin set")
    return set()


STABLECOINS = load_stablecoins()


def load_composition():
    """Load all collateral composition data from per-CSU parquet files."""
    frames = []
    for f in glob.glob(str(PROJECT_ROOT / 'data' / 'gold' / 'collateral_composition' / '*' / '*.parquet')):
        # Skip the chain-level aggregates (may be stale)
        if 'all_csus_composition' in f or 'all_chains_composition' in f:
            continue
        frames.append(pd.read_parquet(f))
    if not frames:
        return pd.DataFrame()
    comp = pd.concat(frames, ignore_index=True)
    comp['date'] = pd.to_datetime(comp['date'])
    # Normalize CSU names to match BQ panel
    CSU_ALIASES = {'aave_v3_bsc': 'aave_v3_binance'}
    comp['csu'] = comp['csu'].replace(CSU_ALIASES)
    return comp


def get_top4_tokens(comp, csu):
    """Get the top 4 tokens by average weight for a CSU."""
    sub = comp[comp['csu'] == csu]
    if sub.empty:
        return []
    avg_weight = sub.groupby('symbol')['pct_of_total'].mean().sort_values(ascending=False)
    return list(avg_weight.head(4).index)


def build_token_weight_series(comp, csu, top4):
    """Build daily weight series for top 4 tokens and 'Other'.

    Returns a DataFrame indexed by date with columns for each top4 token
    and 'Other', where weights sum to 1.0 on each day.
    """
    sub = comp[comp['csu'] == csu].copy()
    sub = sub.dropna(subset=['pct_of_total'])
    # Deduplicate: keep the row with the most non-NaN fields per (date, symbol)
    sub = sub.drop_duplicates(subset=['date', 'symbol'], keep='last')
    sub = sub.sort_values('date')

    # Pivot: date x symbol -> pct_of_total
    pivot = sub.pivot_table(index='date', columns='symbol', values='pct_of_total', aggfunc='sum')
    # Normalize each row to sum to 100 in case of rounding
    row_sums = pivot.sum(axis=1)
    pivot = pivot.div(row_sums, axis=0)  # now fractions summing to 1.0

    result = pd.DataFrame(index=pivot.index)
    for sym in top4:
        if sym in pivot.columns:
            result[sym] = pivot[sym]
        else:
            result[sym] = 0.0

    # 'Other' is everything not in top4
    other_cols = [c for c in pivot.columns if c not in top4]
    result['Other'] = pivot[other_cols].sum(axis=1) if other_cols else 0.0

    return result


def plot_csu(csu, panel_df, comp_df, output_dir):
    """Plot a single CSU: liquidation (left) and price level (right)."""
    sub = panel_df[panel_df['csu'] == csu].sort_values('date').copy()
    if sub.empty:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    # === Left panel: Liquidation volume + count ===
    ax1.fill_between(sub['date'], 0, sub['liquidation'], alpha=0.35, color='firebrick')
    ax1.plot(sub['date'], sub['liquidation'], color='firebrick', linewidth=0.5)
    ax1.set_ylabel('log(1 + collateral USD)', color='firebrick')
    ax1.tick_params(axis='y', labelcolor='firebrick')
    ax1.set_xlim(sub['date'].min(), sub['date'].max())
    ax1.set_title('Liquidation')

    # Liquidation count on right y-axis
    ax1r = ax1.twinx()
    ax1r.plot(sub['date'], sub['n_liquidations'], color='darkblue', linewidth=0.8, alpha=0.7)
    ax1r.set_ylabel('Count', color='darkblue')
    ax1r.tick_params(axis='y', labelcolor='darkblue')

    # === Right panel: Price level as stacked area by token weight ===
    basket_price = np.exp(sub['log_price'].values)
    if len(basket_price) > 0 and basket_price[0] != 0:
        basket_price = basket_price / basket_price[0]

    top4 = get_top4_tokens(comp_df, csu) if not comp_df.empty else []
    colors = ['#2166ac', '#d6604d', '#4daf4a', '#ff7f00', '#999999']
    labels = top4 + ['Other'] if top4 else []

    if top4:
        weights = build_token_weight_series(comp_df, csu, top4)
        # Align weights to panel dates
        weight_aligned = weights.reindex(sub['date'].values).ffill().bfill().fillna(0)
        # Re-normalize rows to sum to 1.0 after alignment (bfill can inflate totals)
        row_sums = weight_aligned.sum(axis=1).values
        row_sums[row_sums == 0] = 1.0  # avoid division by zero
        weight_aligned = weight_aligned.div(row_sums, axis=0)

        # Each token's contribution = weight * basket_price
        # Order: stablecoins on bottom, then volatile, then Other on top
        stable_tokens = [t for t in top4 if t in STABLECOINS]
        volatile_tokens = [t for t in top4 if t not in STABLECOINS]
        ordered_cols = stable_tokens + volatile_tokens + ['Other']

        stacks = {}
        for col in ordered_cols:
            stacks[col] = weight_aligned[col].values * basket_price

        # Manual stacked fill_between so we can apply hatching to stablecoins
        cumulative = np.zeros(len(basket_price))
        for col in ordered_cols:
            stack_vals = stacks[col]
            is_stable = col in STABLECOINS
            hatch = '///' if is_stable else ('...' if col == 'Other' else '')
            color_idx = top4.index(col) if col in top4 else 4
            ax2.fill_between(
                sub['date'], cumulative, cumulative + stack_vals,
                color=colors[color_idx], alpha=0.8, label=col,
                hatch=hatch, edgecolor='white', linewidth=0.3,
            )
            cumulative = cumulative + stack_vals

        ax2.legend(loc='upper left', fontsize=7, framealpha=0.9)
    else:
        # No composition data — just plot basket as filled area
        ax2.fill_between(sub['date'], 0, basket_price, alpha=0.5, color='steelblue', label='Basket')
        ax2.legend(loc='upper left', fontsize=8, framealpha=0.9)

    ax2.plot(sub['date'], basket_price, color='black', linewidth=1.0, alpha=0.6)
    ax2.set_ylabel('Price Level (normalized)')
    ax2.set_title('Collateral Basket Price Level')
    ax2.set_xlim(sub['date'].min(), sub['date'].max())
    ax2.axhline(1.0, color='gray', linestyle=':', linewidth=0.5)

    fig.suptitle(csu, fontsize=13, fontweight='bold')
    fig.autofmt_xdate(rotation=30)
    plt.tight_layout(rect=[0, 0, 1, 0.93])

    save_path = output_dir / f'{csu}.png'
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()


def main():
    df = pd.read_parquet(PROJECT_ROOT / 'data' / 'analysis' / 'panel_svar_data_qualified.parquet')
    df['date'] = pd.to_datetime(df['date'])

    comp = load_composition()
    print(f"Loaded composition: {len(comp)} rows, {comp['csu'].nunique()} CSUs")

    output_dir = PROJECT_ROOT / 'results' / 'data_analysis' / 'csu_timeseries'
    output_dir.mkdir(parents=True, exist_ok=True)

    csus = sorted(df['csu'].unique())
    print(f"Generating plots for {len(csus)} CSUs...")
    for i, csu in enumerate(csus):
        plot_csu(csu, df, comp, output_dir)
        print(f"  [{i+1}/{len(csus)}] {csu}")
    print(f"Done. {len(csus)} plots saved to {output_dir}")


if __name__ == '__main__':
    main()
