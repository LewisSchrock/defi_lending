#!/usr/bin/env python3
"""
Panel Data Visualization Suite

Generates visualizations for Panel SVAR analysis data:
- Time series plots per CSU
- Ridge plots across CSUs
- Distribution histograms
- Summary dashboard

Usage:
    python scripts/visualize_panel_data.py
    python scripts/visualize_panel_data.py --output-dir figures/panel
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# Style settings
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = plt.cm.tab10.colors
CSU_COLORS = {}


def load_panel_data() -> pd.DataFrame:
    """Load Panel SVAR data."""
    path = Path('data/analysis/panel_svar_data.parquet')
    if not path.exists():
        # Try Excel
        path = Path('data/analysis/panel_svar_data.xlsx')
        if path.exists():
            return pd.read_excel(path)
        raise FileNotFoundError("Run prepare_panel_svar_data.py first")

    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def assign_colors(csus: list):
    """Assign consistent colors to CSUs."""
    global CSU_COLORS
    for i, csu in enumerate(sorted(csus)):
        CSU_COLORS[csu] = COLORS[i % len(COLORS)]


def plot_time_series_by_csu(df: pd.DataFrame, variable: str, output_dir: Path,
                            ylabel: str = None, title_prefix: str = None,
                            log_scale: bool = False):
    """Plot time series for each CSU separately."""

    csus = df['csu'].unique()
    n_csus = len(csus)

    fig, axes = plt.subplots(n_csus, 1, figsize=(12, 3 * n_csus), sharex=True)
    if n_csus == 1:
        axes = [axes]

    for ax, csu in zip(axes, sorted(csus)):
        csu_data = df[df['csu'] == csu].sort_values('date')

        ax.plot(csu_data['date'], csu_data[variable],
                color=CSU_COLORS[csu], linewidth=0.8, alpha=0.8)
        ax.fill_between(csu_data['date'], 0, csu_data[variable],
                       color=CSU_COLORS[csu], alpha=0.3)

        ax.set_ylabel(ylabel or variable)
        ax.set_title(csu.replace('_', ' ').title(), fontsize=10, fontweight='bold')

        if log_scale and variable != 'utilization':
            ax.set_yscale('symlog', linthresh=1)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))

    plt.xlabel('Date')
    fig.suptitle(f'{title_prefix or variable.title()} by CSU', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = output_dir / f'{variable}_time_series.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def plot_ridge_plot(df: pd.DataFrame, variable: str, output_dir: Path,
                   xlabel: str = None, title: str = None):
    """Create ridge plot showing distribution over time by CSU."""

    csus = sorted(df['csu'].unique())
    n_csus = len(csus)

    fig, axes = plt.subplots(n_csus, 1, figsize=(12, 1.5 * n_csus), sharex=True)
    if n_csus == 1:
        axes = [axes]

    # Resample to weekly for cleaner visualization
    for ax, csu in zip(axes, csus):
        csu_data = df[df['csu'] == csu].set_index('date')[variable].dropna()

        if csu_data.empty:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            ax.set_ylabel(csu.split('_')[-1], rotation=0, ha='right', fontsize=9)
            continue

        # Weekly resample
        weekly = csu_data.resample('W').mean()

        ax.fill_between(weekly.index, 0, weekly.values,
                       color=CSU_COLORS[csu], alpha=0.7)
        ax.plot(weekly.index, weekly.values, color=CSU_COLORS[csu],
                linewidth=0.5, alpha=0.9)

        # Clean up axes
        ax.set_ylabel(csu.replace('compound_v3_eth_', 'c3_').replace('_ethereum', ''),
                     rotation=0, ha='right', fontsize=9)
        ax.set_yticks([])
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xlabel(xlabel or variable)

    fig.suptitle(title or f'{variable.title()} Ridge Plot', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = output_dir / f'{variable}_ridge.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def plot_histograms_per_csu(df: pd.DataFrame, output_dir: Path):
    """Create histogram grid showing all three metrics per CSU."""

    csus = sorted(df['csu'].unique())
    variables = ['liquidation', 'utilization', 'volatility']
    var_labels = ['Liquidation (USD)', 'Utilization', 'Volatility']

    n_csus = len(csus)
    fig, axes = plt.subplots(n_csus, 3, figsize=(14, 3 * n_csus))

    if n_csus == 1:
        axes = axes.reshape(1, -1)

    for i, csu in enumerate(csus):
        csu_data = df[df['csu'] == csu]

        for j, (var, label) in enumerate(zip(variables, var_labels)):
            ax = axes[i, j]
            data = csu_data[var].dropna()

            if data.empty or data.sum() == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                       transform=ax.transAxes, fontsize=10)
            else:
                # Use log scale for liquidation
                if var == 'liquidation':
                    data_plot = data[data > 0]
                    if len(data_plot) > 0:
                        ax.hist(np.log10(data_plot + 1), bins=30,
                               color=CSU_COLORS[csu], alpha=0.7, edgecolor='white')
                        ax.set_xlabel(f'log10({label})')
                else:
                    ax.hist(data, bins=30, color=CSU_COLORS[csu],
                           alpha=0.7, edgecolor='white')
                    ax.set_xlabel(label)

            if j == 0:
                ax.set_ylabel(csu.replace('compound_v3_eth_', 'c3_').replace('_ethereum', ''),
                             fontsize=10, fontweight='bold')

            if i == 0:
                ax.set_title(label, fontsize=11, fontweight='bold')

    fig.suptitle('Distribution of Variables by CSU', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    output_path = output_dir / 'histograms_by_csu.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def plot_summary_dashboard(df: pd.DataFrame, output_dir: Path):
    """Create summary dashboard with key statistics."""

    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

    csus = sorted(df['csu'].unique())

    # 1. Total liquidation by CSU (bar chart)
    ax1 = fig.add_subplot(gs[0, 0])
    liq_totals = df.groupby('csu')['liquidation'].sum().sort_values(ascending=True)
    bars = ax1.barh(range(len(liq_totals)), liq_totals.values / 1e6,
                   color=[CSU_COLORS[c] for c in liq_totals.index])
    ax1.set_yticks(range(len(liq_totals)))
    ax1.set_yticklabels([c.replace('compound_v3_eth_', 'c3_').replace('_ethereum', '')
                        for c in liq_totals.index], fontsize=9)
    ax1.set_xlabel('Total Liquidation ($M)')
    ax1.set_title('Total Liquidation by CSU', fontweight='bold')

    # 2. Average utilization by CSU
    ax2 = fig.add_subplot(gs[0, 1])
    util_means = df.groupby('csu')['utilization'].mean().sort_values(ascending=True)
    ax2.barh(range(len(util_means)), util_means.values,
            color=[CSU_COLORS[c] for c in util_means.index])
    ax2.set_yticks(range(len(util_means)))
    ax2.set_yticklabels([c.replace('compound_v3_eth_', 'c3_').replace('_ethereum', '')
                        for c in util_means.index], fontsize=9)
    ax2.set_xlabel('Average Utilization')
    ax2.set_title('Avg Utilization by CSU', fontweight='bold')
    ax2.set_xlim(0, 1)

    # 3. Average volatility by CSU
    ax3 = fig.add_subplot(gs[0, 2])
    vol_means = df.groupby('csu')['volatility'].mean().dropna().sort_values(ascending=True)
    if not vol_means.empty:
        ax3.barh(range(len(vol_means)), vol_means.values,
                color=[CSU_COLORS[c] for c in vol_means.index])
        ax3.set_yticks(range(len(vol_means)))
        ax3.set_yticklabels([c.replace('compound_v3_eth_', 'c3_').replace('_ethereum', '')
                            for c in vol_means.index], fontsize=9)
    ax3.set_xlabel('Average Volatility')
    ax3.set_title('Avg Volatility by CSU', fontweight='bold')

    # 4. Liquidation time series (all CSUs)
    ax4 = fig.add_subplot(gs[1, :])
    for csu in csus:
        csu_data = df[df['csu'] == csu].set_index('date')['liquidation']
        weekly = csu_data.resample('W').sum()
        ax4.plot(weekly.index, weekly.values / 1e6, label=csu.replace('compound_v3_eth_', 'c3_').replace('_ethereum', ''),
                color=CSU_COLORS[csu], linewidth=1.2, alpha=0.8)
    ax4.set_ylabel('Weekly Liquidation ($M)')
    ax4.set_title('Liquidation Over Time', fontweight='bold')
    ax4.legend(loc='upper right', fontsize=8, ncol=3)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # 5. Utilization time series
    ax5 = fig.add_subplot(gs[2, :2])
    for csu in csus:
        csu_data = df[df['csu'] == csu].set_index('date')['utilization']
        weekly = csu_data.resample('W').mean()
        ax5.plot(weekly.index, weekly.values, label=csu.replace('compound_v3_eth_', 'c3_').replace('_ethereum', ''),
                color=CSU_COLORS[csu], linewidth=1.2, alpha=0.8)
    ax5.set_ylabel('Utilization')
    ax5.set_title('Utilization Over Time', fontweight='bold')
    ax5.set_ylim(0, 1)
    ax5.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    # 6. Correlation heatmap
    ax6 = fig.add_subplot(gs[2, 2])
    corr_vars = ['liquidation', 'utilization', 'volatility']
    corr_matrix = df[corr_vars].corr()
    im = ax6.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
    ax6.set_xticks(range(len(corr_vars)))
    ax6.set_yticks(range(len(corr_vars)))
    ax6.set_xticklabels(['Liq', 'Util', 'Vol'], fontsize=10)
    ax6.set_yticklabels(['Liq', 'Util', 'Vol'], fontsize=10)
    for i in range(len(corr_vars)):
        for j in range(len(corr_vars)):
            val = corr_matrix.iloc[i, j]
            ax6.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=11,
                    color='white' if abs(val) > 0.5 else 'black')
    ax6.set_title('Correlation Matrix', fontweight='bold')
    plt.colorbar(im, ax=ax6, fraction=0.046)

    fig.suptitle('Panel SVAR Data Summary Dashboard', fontsize=16, fontweight='bold', y=1.02)

    output_path = output_dir / 'summary_dashboard.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def plot_scatter_matrix(df: pd.DataFrame, output_dir: Path):
    """Create scatter plot matrix of variables."""

    variables = ['liquidation', 'utilization', 'volatility']
    csus = sorted(df['csu'].unique())

    fig, axes = plt.subplots(3, 3, figsize=(12, 12))

    for i, var1 in enumerate(variables):
        for j, var2 in enumerate(variables):
            ax = axes[i, j]

            if i == j:
                # Diagonal: histogram
                for csu in csus:
                    data = df[df['csu'] == csu][var1].dropna()
                    if var1 == 'liquidation':
                        data = np.log10(data + 1)
                    ax.hist(data, bins=20, alpha=0.5, color=CSU_COLORS[csu],
                           label=csu.split('_')[-1] if '_' in csu else csu[:8])
                ax.set_xlabel(var1 if var1 != 'liquidation' else 'log10(liq)')
            else:
                # Off-diagonal: scatter
                for csu in csus:
                    csu_data = df[df['csu'] == csu]
                    x = csu_data[var2]
                    y = csu_data[var1]
                    if var2 == 'liquidation':
                        x = np.log10(x + 1)
                    if var1 == 'liquidation':
                        y = np.log10(y + 1)
                    ax.scatter(x, y, alpha=0.3, s=10, color=CSU_COLORS[csu])

                if i == 2:
                    ax.set_xlabel(var2 if var2 != 'liquidation' else 'log10(liq)')
                if j == 0:
                    ax.set_ylabel(var1 if var1 != 'liquidation' else 'log10(liq)')

    # Add legend
    handles = [plt.Line2D([0], [0], marker='o', color='w',
                         markerfacecolor=CSU_COLORS[csu], markersize=8,
                         label=csu.replace('compound_v3_eth_', 'c3_').replace('_ethereum', ''))
              for csu in csus]
    fig.legend(handles=handles, loc='upper right', bbox_to_anchor=(0.99, 0.99), fontsize=9)

    fig.suptitle('Variable Relationships by CSU', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_path = output_dir / 'scatter_matrix.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate panel data visualizations')
    parser.add_argument('--output-dir', default='figures/panel',
                       help='Output directory for figures')
    args = parser.parse_args()

    print("=" * 70)
    print("Panel Data Visualization Suite")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    df = load_panel_data()
    print(f"  Loaded {len(df):,} observations")
    print(f"  CSUs: {df['csu'].nunique()}")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Assign colors
    assign_colors(df['csu'].unique())

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate visualizations
    print("\nGenerating time series plots...")
    plot_time_series_by_csu(df, 'liquidation', output_dir,
                           ylabel='Liquidation (USD)', title_prefix='Daily Liquidation')
    plot_time_series_by_csu(df, 'utilization', output_dir,
                           ylabel='Utilization Ratio', title_prefix='Utilization')
    plot_time_series_by_csu(df, 'volatility', output_dir,
                           ylabel='Volatility', title_prefix='Collateral Basket Volatility')

    print("\nGenerating ridge plots...")
    plot_ridge_plot(df, 'liquidation', output_dir,
                   xlabel='Liquidation (weekly avg)', title='Liquidation Ridge Plot')
    plot_ridge_plot(df, 'utilization', output_dir,
                   xlabel='Utilization (weekly avg)', title='Utilization Ridge Plot')
    plot_ridge_plot(df, 'volatility', output_dir,
                   xlabel='Volatility (weekly avg)', title='Volatility Ridge Plot')

    print("\nGenerating histograms...")
    plot_histograms_per_csu(df, output_dir)

    print("\nGenerating summary dashboard...")
    plot_summary_dashboard(df, output_dir)

    print("\nGenerating scatter matrix...")
    plot_scatter_matrix(df, output_dir)

    print("\n" + "=" * 70)
    print(f"All figures saved to: {output_dir}/")
    print("=" * 70)

    # List generated files
    print("\nGenerated files:")
    for f in sorted(output_dir.glob('*.png')):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}: {size_kb:.0f} KB")


if __name__ == '__main__':
    main()
