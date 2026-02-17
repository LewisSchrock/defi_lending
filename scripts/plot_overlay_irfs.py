#!/usr/bin/env python3
"""
Plot Heterogeneous IRFs - All CSUs overlaid on single 3x3 grid
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10

def plot_overlaid_irfs():
    """Plot all CSU IRFs overlaid on single 3x3 grid."""

    # Load results
    df = pd.read_excel('output/ind-IRs-to-common-shocks.xlsx', index_col=0)
    df_valid = df.dropna(how='all')
    csus = df_valid.index.tolist()

    print(f"Plotting {len(csus)} CSUs with overlaid IRFs")

    # Variable order: 1=utilization, 2=liquidation, 3=volatility
    variables = ['Utilization', 'Liquidation', 'Volatility']
    shocks = ['Utilization', 'Liquidation', 'Volatility']

    # Create figure
    fig, axes = plt.subplots(3, 3, figsize=(18, 14))
    fig.suptitle('Heterogeneous Panel SVAR - Individual CSU Impulse Response Functions\n' +
                 'DeFi Liquidations Analysis (14 CSUs)\n' +
                 'Causal Order: Utilization → Liquidation → Volatility',
                 fontsize=16, fontweight='bold', y=0.995)

    # Color palette - use distinctive colors for each CSU
    colors = sns.color_palette("tab20", len(csus))

    for i in range(3):
        for j in range(3):
            ax = axes[i, j]

            # Get IRF column names
            col_prefix = f'IR{i+1}{j+1}_'
            cols = [col for col in df.columns if col.startswith(col_prefix)]

            if cols:
                # Plot each CSU's IRF
                for idx, (csu, color) in enumerate(zip(csus, colors)):
                    irf_data = df_valid.loc[csu, cols].values
                    if not np.isnan(irf_data).all():
                        steps = np.arange(len(irf_data))
                        ax.plot(steps, irf_data, linewidth=2, alpha=0.8,
                               color=color, label=csu)

                # Zero line
                ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.7)

                # Labels
                response_var = variables[i]
                shock_var = shocks[j]
                ax.set_title(f"{response_var} (σ) Response to {shock_var} Shock",
                            fontsize=12, fontweight='bold')
                if i == 2:
                    ax.set_xlabel('Steps (days)', fontsize=11)
                if j == 0:
                    ax.set_ylabel('Response (σ)', fontsize=11)
                ax.grid(True, alpha=0.3, linewidth=0.5)
                ax.tick_params(labelsize=9)

    # Create single legend for all subplots
    handles, labels = axes[0, 0].get_legend_handles_labels()

    # Format CSU names for legend
    legend_labels = [csu.replace('_', ' ').title() for csu in labels]

    # Add legend below the plot
    fig.legend(handles, legend_labels,
              loc='lower center',
              bbox_to_anchor=(0.5, -0.02),
              ncol=7,
              fontsize=9,
              frameon=True,
              title='CSU',
              title_fontsize=10)

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])

    # Save
    output_path = Path('data/analysis/svar_figures')
    output_path.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path / 'heterogeneous_irfs_overlaid.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'heterogeneous_irfs_overlaid.pdf', bbox_inches='tight')

    print(f"\n✓ Saved: {output_path}/heterogeneous_irfs_overlaid.png")
    print(f"✓ Saved: {output_path}/heterogeneous_irfs_overlaid.pdf")

    return fig


def plot_overlaid_with_mean():
    """Plot all CSU IRFs overlaid + mean IRF highlighted."""

    df = pd.read_excel('output/ind-IRs-to-common-shocks.xlsx', index_col=0)
    df_valid = df.dropna(how='all')
    csus = df_valid.index.tolist()

    variables = ['Utilization', 'Liquidation', 'Volatility']
    shocks = ['Utilization', 'Liquidation', 'Volatility']

    fig, axes = plt.subplots(3, 3, figsize=(18, 14))
    fig.suptitle('Heterogeneous Panel SVAR - Individual IRFs with Mean\n' +
                 'DeFi Liquidations Analysis (14 CSUs)\n' +
                 'Causal Order: Utilization → Liquidation → Volatility',
                 fontsize=16, fontweight='bold', y=0.995)

    colors = sns.color_palette("tab20", len(csus))

    for i in range(3):
        for j in range(3):
            ax = axes[i, j]

            col_prefix = f'IR{i+1}{j+1}_'
            cols = [col for col in df.columns if col.startswith(col_prefix)]

            if cols:
                # Plot individual CSU IRFs (lighter)
                for idx, (csu, color) in enumerate(zip(csus, colors)):
                    irf_data = df_valid.loc[csu, cols].values
                    if not np.isnan(irf_data).all():
                        steps = np.arange(len(irf_data))
                        ax.plot(steps, irf_data, linewidth=1.5, alpha=0.4,
                               color=color)

                # Plot mean IRF (bold)
                mean_irf = df_valid[cols].mean(axis=0, skipna=True).values
                steps = np.arange(len(mean_irf))
                ax.plot(steps, mean_irf, 'black', linewidth=3.5,
                       label='Mean IRF', zorder=100)

                # Zero line
                ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.7)

                # Labels
                response_var = variables[i]
                shock_var = shocks[j]
                ax.set_title(f"{response_var} (σ) Response to {shock_var} Shock",
                            fontsize=12, fontweight='bold')
                if i == 2:
                    ax.set_xlabel('Steps (days)', fontsize=11)
                if j == 0:
                    ax.set_ylabel('Response (σ)', fontsize=11)
                ax.grid(True, alpha=0.3, linewidth=0.5)
                ax.tick_params(labelsize=9)

                # Legend only on first plot
                if i == 0 and j == 0:
                    ax.legend(fontsize=10, loc='best')

    plt.tight_layout(rect=[0, 0, 1, 0.98])

    output_path = Path('data/analysis/svar_figures')
    fig.savefig(output_path / 'heterogeneous_irfs_with_mean.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'heterogeneous_irfs_with_mean.pdf', bbox_inches='tight')

    print(f"✓ Saved: {output_path}/heterogeneous_irfs_with_mean.png")
    print(f"✓ Saved: {output_path}/heterogeneous_irfs_with_mean.pdf")

    return fig


if __name__ == '__main__':
    print("="*70)
    print("Creating Overlaid Heterogeneous IRF Plots")
    print("="*70)
    print()

    plot_overlaid_irfs()
    print()
    plot_overlaid_with_mean()

    print()
    print("="*70)
    print("✓ Complete!")
    print("="*70)
