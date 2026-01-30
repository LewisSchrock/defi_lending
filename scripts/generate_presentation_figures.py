#!/usr/bin/env python3
"""
Generate figures for mid-year thesis presentation.
Outputs to figures/presentation/ for Overleaf integration.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

# Style
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'figure.dpi': 200,
})

PURPLE = '#512888'
GOLD = '#FFC72C'
COLORS = ['#512888', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

OUTPUT_DIR = Path('figures/presentation')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. TVL Coverage Heatmap - CSUs x Months
# ============================================================
def plot_tvl_coverage_heatmap():
    """Show TVL data coverage across CSUs and months."""
    tvl = pd.read_csv('data/silver/tvl/daily_tvl.csv')
    tvl['date'] = pd.to_datetime(tvl['date'])
    tvl['month'] = tvl['date'].dt.to_period('M')

    # Coverage: fraction of days with data per CSU per month
    pivot = tvl.groupby(['csu', 'month']).size().unstack(fill_value=0)

    # Group by chain for ordering
    chain_order = []
    for chain in ['ethereum', 'base', 'arbitrum', 'optimism', 'polygon',
                  'avalanche', 'binance', 'xdai', 'meter', 'linea', 'scroll']:
        chain_csus = [c for c in pivot.index if chain in c]
        chain_order.extend(sorted(chain_csus))
    remaining = [c for c in pivot.index if c not in chain_order]
    chain_order.extend(remaining)
    pivot = pivot.reindex(chain_order)

    fig, ax = plt.subplots(figsize=(14, 8))
    data = (pivot > 0).astype(int).values
    im = ax.imshow(data, aspect='auto', cmap='Purples', interpolation='nearest')

    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([c.replace('_', ' ').title() for c in pivot.index], fontsize=8)

    months = pivot.columns.astype(str)
    step = max(1, len(months) // 12)
    ax.set_xticks(range(0, len(months), step))
    ax.set_xticklabels([months[i] for i in range(0, len(months), step)], rotation=45, ha='right', fontsize=8)

    ax.set_title(f'TVL Data Coverage: {len(pivot.index)} CSUs Across {len(months)} Months', fontweight='bold')
    ax.set_xlabel('Month')
    ax.set_ylabel('CSU (Protocol × Chain)')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'tvl_coverage_heatmap.png', bbox_inches='tight')
    plt.close()
    print("Saved: tvl_coverage_heatmap.png")


# ============================================================
# 2. TVL Time Series - Aggregate by Chain
# ============================================================
def plot_tvl_by_chain():
    """Aggregate TVL over time grouped by chain."""
    tvl = pd.read_csv('data/silver/tvl/daily_tvl.csv')
    tvl['date'] = pd.to_datetime(tvl['date'])

    # Extract chain from CSU name
    def get_chain(csu):
        parts = csu.split('_')
        return parts[-1] if parts[-1] not in ['usdc', 'usdt', 'usds', 'weth', 'wsteth',
                                                'usdbc', 'aero', 'usdc_e', 'pool'] else parts[-2]
    tvl['chain'] = tvl['csu'].apply(get_chain)

    agg = tvl.groupby(['date', 'chain'])['net_tvl_usd'].sum().reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    chains = agg.groupby('chain')['net_tvl_usd'].mean().sort_values(ascending=False).index

    for i, chain in enumerate(chains[:8]):
        chain_data = agg[agg['chain'] == chain].sort_values('date')
        ax.plot(chain_data['date'], chain_data['net_tvl_usd'] / 1e9,
                label=chain.title(), color=COLORS[i % len(COLORS)], linewidth=1.5)

    ax.set_title('Total Value Locked by Chain', fontweight='bold')
    ax.set_ylabel('TVL (Billions USD)')
    ax.set_xlabel('')
    ax.legend(loc='upper left', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.1f}B'))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'tvl_by_chain.png', bbox_inches='tight')
    plt.close()
    print("Saved: tvl_by_chain.png")


# ============================================================
# 3. Ethereum Liquidation Time Series
# ============================================================
def plot_eth_liquidation_timeseries():
    """Daily liquidation volume on Ethereum by CSU."""
    panel = pd.read_parquet('data/gold/liquidations/ethereum/daily_panel.parquet')
    panel['date'] = pd.to_datetime(panel['date'])

    # Aggregate daily total
    daily = panel.groupby('date')['total_collateral_usd'].sum().reset_index()

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})

    # Top: aggregate
    ax = axes[0]
    ax.bar(daily['date'], daily['total_collateral_usd'] / 1e6, width=1,
           color=PURPLE, alpha=0.7)
    ax.set_title('Ethereum Liquidation Volume (Aggregate)', fontweight='bold')
    ax.set_ylabel('Collateral Seized (Millions USD)')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:.1f}M'))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    # Bottom: by CSU stacked
    ax2 = axes[1]
    csus = sorted(panel['csu'].unique())
    bottom = np.zeros(len(daily))
    date_vals = daily['date'].values

    for i, csu in enumerate(csus):
        csu_data = panel[panel['csu'] == csu].set_index('date')['total_collateral_usd']
        csu_daily = csu_data.reindex(pd.to_datetime(date_vals), fill_value=0).values / 1e6
        ax2.bar(date_vals, csu_daily, bottom=bottom, width=1,
                color=COLORS[i % len(COLORS)], alpha=0.8,
                label=csu.replace('_', ' ').replace('ethereum', 'ETH'))
        bottom += csu_daily

    ax2.set_title('Liquidation Volume by CSU', fontweight='bold')
    ax2.set_ylabel('USD (M)')
    ax2.legend(fontsize=7, ncol=3, loc='upper left')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'eth_liquidation_timeseries.png', bbox_inches='tight')
    plt.close()
    print("Saved: eth_liquidation_timeseries.png")


# ============================================================
# 4. Liquidation Count Distribution by CSU
# ============================================================
def plot_liquidation_distribution():
    """Histogram of daily liquidation counts per CSU."""
    panel = pd.read_parquet('data/gold/liquidations/ethereum/daily_panel.parquet')
    has_liq = panel[panel['n_liquidations'] > 0]

    csus = sorted(has_liq['csu'].unique())
    n = len(csus)
    cols = 3
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(14, 4 * rows))
    axes = axes.flatten()

    for i, csu in enumerate(csus):
        ax = axes[i]
        data = has_liq[has_liq['csu'] == csu]['total_collateral_usd'] / 1e3
        ax.hist(data, bins=30, color=COLORS[i % len(COLORS)], alpha=0.8, edgecolor='white')
        ax.set_title(csu.replace('_', ' ').title(), fontsize=10, fontweight='bold')
        ax.set_xlabel('Collateral Seized ($K)')
        ax.set_ylabel('Days')

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle('Distribution of Daily Liquidation Volume (Days with Liquidations)', fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'liquidation_distribution_by_csu.png', bbox_inches='tight')
    plt.close()
    print("Saved: liquidation_distribution_by_csu.png")


# ============================================================
# 5. Utilization Time Series by CSU
# ============================================================
def plot_utilization_timeseries():
    """Show utilization ratio over time per Ethereum CSU."""
    tvl = pd.read_csv('data/silver/tvl/daily_tvl.csv')
    tvl['date'] = pd.to_datetime(tvl['date'])

    eth_csus = ['aave_v3_ethereum', 'compound_v3_eth_usdc', 'compound_v3_eth_usdt',
                'compound_v3_eth_usds', 'compound_v3_eth_weth', 'sparklend_ethereum']
    eth = tvl[tvl['csu'].isin(eth_csus)].copy()
    eth['utilization'] = eth['total_borrow_usd'] / eth['total_supply_usd']
    eth['utilization'] = eth['utilization'].clip(0, 1)

    fig, ax = plt.subplots(figsize=(12, 5))
    for i, csu in enumerate(eth_csus):
        csu_data = eth[eth['csu'] == csu].sort_values('date')
        if len(csu_data) == 0:
            continue
        label = csu.replace('_', ' ').replace('ethereum', 'ETH').replace('eth ', '')
        ax.plot(csu_data['date'], csu_data['utilization'],
                label=label, color=COLORS[i % len(COLORS)], linewidth=1.2, alpha=0.85)

    ax.set_title('Utilization Ratio (Leverage Proxy) — Ethereum CSUs', fontweight='bold')
    ax.set_ylabel('Utilization (Borrowed / Supplied)')
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, ncol=2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'utilization_timeseries.png', bbox_inches='tight')
    plt.close()
    print("Saved: utilization_timeseries.png")


# ============================================================
# 6. Pipeline Overview Summary Table (as figure)
# ============================================================
def plot_pipeline_summary():
    """Create a summary statistics table as a figure."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('off')

    data = [
        ['Block Cache', '17 chains', '730 days each', '100%'],
        ['TVL (Silver)', '36 CSUs, 11 chains', '22,390 records', '100%'],
        ['Liquidations (Gold)', '6 CSUs, Ethereum', '4,380 panel obs', '100%'],
        ['Liquidations (Bronze)', '3 chains', '37,670 raw events', 'Expanding'],
        ['Price Cache', 'Ethereum tokens', '9,003 entries', '~85%'],
        ['Collateral Comp.', '6 CSUs, Ethereum', '62,115 records', '~45% USD'],
    ]

    table = ax.table(
        cellText=data,
        colLabels=['Dataset', 'Scope', 'Volume', 'Coverage'],
        loc='center',
        cellLoc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)

    # Style header
    for j in range(4):
        table[0, j].set_facecolor(PURPLE)
        table[0, j].set_text_props(color='white', fontweight='bold')

    # Alternate row colors
    for i in range(1, len(data) + 1):
        for j in range(4):
            if i % 2 == 0:
                table[i, j].set_facecolor('#f0e8f5')

    ax.set_title('Data Pipeline Summary', fontweight='bold', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'pipeline_summary_table.png', bbox_inches='tight')
    plt.close()
    print("Saved: pipeline_summary_table.png")


# ============================================================
# 7. Liquidation vs Utilization scatter
# ============================================================
def plot_liq_vs_utilization():
    """Scatter of liquidation volume vs utilization by CSU."""
    panel = pd.read_parquet('data/gold/liquidations/ethereum/daily_panel.parquet')
    tvl = pd.read_csv('data/silver/tvl/daily_tvl.csv')

    panel['date'] = pd.to_datetime(panel['date']).dt.strftime('%Y-%m-%d')
    tvl['date'] = pd.to_datetime(tvl['date']).dt.strftime('%Y-%m-%d')

    tvl['utilization'] = tvl['total_borrow_usd'] / tvl['total_supply_usd']
    tvl['utilization'] = tvl['utilization'].clip(0, 1)

    merged = panel.merge(tvl[['date', 'csu', 'utilization']], on=['date', 'csu'], how='left')
    has_liq = merged[merged['total_collateral_usd'] > 0]

    fig, ax = plt.subplots(figsize=(10, 6))
    csus = sorted(has_liq['csu'].unique())
    for i, csu in enumerate(csus):
        d = has_liq[has_liq['csu'] == csu]
        label = csu.replace('_', ' ').replace('ethereum', 'ETH')
        ax.scatter(d['utilization'], d['total_collateral_usd'] / 1e3,
                   alpha=0.5, s=25, color=COLORS[i % len(COLORS)], label=label)

    ax.set_xlabel('Utilization Ratio')
    ax.set_ylabel('Collateral Seized ($K)')
    ax.set_title('Liquidation Volume vs. Utilization (Days with Liquidations)', fontweight='bold')
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'liq_vs_utilization_scatter.png', bbox_inches='tight')
    plt.close()
    print("Saved: liq_vs_utilization_scatter.png")


# ============================================================
# 8. Data completeness roadmap
# ============================================================
def plot_data_roadmap():
    """Visual showing what's done vs what's next."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.axis('off')

    steps = [
        ('Block Cache\n(17 chains)', 1.0, '✓'),
        ('TVL Collection\n(36 CSUs)', 1.0, '✓'),
        ('Ethereum\nLiquidations', 1.0, '✓'),
        ('Price Cache\n(Chainlink)', 0.85, '~85%'),
        ('Collateral\nComposition', 0.7, '~70%'),
        ('Multi-Chain\nLiquidations', 0.15, 'Testing'),
        ('Panel SVAR\nData Prep', 0.5, '50%'),
        ('Econometric\nAnalysis', 0.0, 'Next'),
    ]

    for i, (label, pct, status) in enumerate(steps):
        x = i * 1.3
        # Background bar
        rect_bg = plt.Rectangle((x, 0), 1.0, 3.0, facecolor='#e0e0e0', edgecolor='#999', linewidth=1)
        ax.add_patch(rect_bg)
        # Fill bar
        fill_color = PURPLE if pct >= 0.9 else (GOLD if pct >= 0.5 else '#cccccc')
        rect_fill = plt.Rectangle((x, 0), 1.0, 3.0 * pct, facecolor=fill_color, edgecolor='none', alpha=0.8)
        ax.add_patch(rect_fill)
        # Label
        ax.text(x + 0.5, -0.5, label, ha='center', va='top', fontsize=8, fontweight='bold')
        ax.text(x + 0.5, 3.2, status, ha='center', va='bottom', fontsize=9,
                color=PURPLE if pct >= 0.9 else 'gray', fontweight='bold')

    ax.set_xlim(-0.3, len(steps) * 1.3)
    ax.set_ylim(-1.5, 4.0)
    ax.set_title('Data Pipeline Progress', fontweight='bold', fontsize=14)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'data_roadmap.png', bbox_inches='tight')
    plt.close()
    print("Saved: data_roadmap.png")


# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("Generating Presentation Figures")
    print("=" * 60)

    plot_pipeline_summary()
    plot_tvl_coverage_heatmap()
    plot_tvl_by_chain()
    plot_eth_liquidation_timeseries()
    plot_liquidation_distribution()
    plot_utilization_timeseries()
    plot_liq_vs_utilization()
    plot_data_roadmap()

    print(f"\nAll figures saved to: {OUTPUT_DIR}/")
