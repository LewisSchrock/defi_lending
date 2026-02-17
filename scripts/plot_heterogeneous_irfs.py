#!/usr/bin/env python3
"""
Plot Individual Heterogeneous IRFs from Pedroni Panel SVAR
Shows IRF for each CSU separately to display heterogeneity
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 8

def plot_individual_common_shock_irfs():
    """Plot individual IRFs to common shocks - one line per CSU."""

    # Load results
    df = pd.read_excel('output/ind-IRs-to-common-shocks.xlsx', index_col=0)

    # Remove CSUs with all NaN
    df_valid = df.dropna(how='all')
    csus = df_valid.index.tolist()

    print(f"Plotting individual IRFs for {len(csus)} CSUs")
    print(f"CSUs: {csus}")

    # Variable order: 1=utilization, 2=liquidation, 3=volatility
    variables = ['Utilization', 'Liquidation', 'Volatility']
    shocks = ['Utilization', 'Liquidation', 'Volatility']

    # Create figure with all CSU lines
    fig, axes = plt.subplots(3, 3, figsize=(16, 12))
    fig.suptitle('Heterogeneous IRFs to Common Shocks - Individual CSUs\n' +
                 'Panel SVAR - DeFi Liquidations\n' +
                 f'Causal Order: Utilization → Liquidation → Volatility ({len(csus)} CSUs)',
                 fontsize=14, fontweight='bold', y=0.995)

    # Color palette for CSUs
    colors = sns.color_palette("husl", len(csus))

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
                        ax.plot(steps, irf_data, linewidth=1.5, alpha=0.7,
                               color=color, label=csu if i==0 and j==2 else "")

                # Zero line
                ax.axhline(0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

                # Labels
                response_var = variables[i]
                shock_var = shocks[j]
                ax.set_title(f"{response_var} (σ) → {shock_var} Shock",
                            fontsize=10, fontweight='bold')
                if i == 2:
                    ax.set_xlabel('Steps (days)', fontsize=9)
                if j == 0:
                    ax.set_ylabel('Response (σ)', fontsize=9)
                ax.grid(True, alpha=0.3)

    # Add legend outside plot area
    handles, labels = axes[0, 2].get_legend_handles_labels()
    fig.legend(handles, labels, loc='center left', bbox_to_anchor=(1.0, 0.5),
              fontsize=7, title='CSU', title_fontsize=8)

    plt.tight_layout(rect=[0, 0, 0.88, 0.98])

    # Save
    output_path = Path('data/analysis/svar_figures')
    output_path.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path / 'individual_common_shock_irfs.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'individual_common_shock_irfs.pdf', bbox_inches='tight')

    print(f"\n✓ Saved: {output_path}/individual_common_shock_irfs.png")
    print(f"✓ Saved: {output_path}/individual_common_shock_irfs.pdf")

    return fig


def plot_individual_csu_panels():
    """Create separate IRF panel for each CSU (3x3 grid per CSU)."""

    df = pd.read_excel('output/ind-IRs-to-common-shocks.xlsx', index_col=0)
    df_valid = df.dropna(how='all')
    csus = df_valid.index.tolist()

    variables = ['Utilization', 'Liquidation', 'Volatility']
    shocks = ['Utilization', 'Liquidation', 'Volatility']

    output_path = Path('data/analysis/svar_figures/individual_csus')
    output_path.mkdir(parents=True, exist_ok=True)

    for csu in csus:
        fig, axes = plt.subplots(3, 3, figsize=(12, 10))
        fig.suptitle(f'IRFs to Common Shocks: {csu.upper()}\n' +
                     'Heterogeneous Panel SVAR\n' +
                     'Causal Order: Utilization → Liquidation → Volatility',
                     fontsize=12, fontweight='bold', y=0.995)

        for i in range(3):
            for j in range(3):
                ax = axes[i, j]

                col_prefix = f'IR{i+1}{j+1}_'
                cols = [col for col in df.columns if col.startswith(col_prefix)]

                if cols:
                    irf_data = df_valid.loc[csu, cols].values

                    if not np.isnan(irf_data).all():
                        steps = np.arange(len(irf_data))

                        # Plot IRF
                        ax.plot(steps, irf_data, 'b-', linewidth=2.5)
                        ax.fill_between(steps, 0, irf_data, alpha=0.2)
                        ax.axhline(0, color='black', linestyle='--', linewidth=0.5)

                        # Labels
                        response_var = variables[i]
                        shock_var = shocks[j]
                        ax.set_title(f"{response_var} → {shock_var} Shock",
                                    fontsize=10, fontweight='bold')
                        if i == 2:
                            ax.set_xlabel('Steps (days)')
                        if j == 0:
                            ax.set_ylabel('Response (σ)')
                        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save individual CSU plot
        csu_clean = csu.replace('/', '_')
        fig.savefig(output_path / f'{csu_clean}_irfs.png', dpi=200, bbox_inches='tight')
        plt.close(fig)

    print(f"\n✓ Saved {len(csus)} individual CSU IRF plots to: {output_path}/")


def plot_irf_heatmaps():
    """Create heatmaps showing IRF heterogeneity across CSUs."""

    df = pd.read_excel('output/ind-IRs-to-common-shocks.xlsx', index_col=0)
    df_valid = df.dropna(how='all')

    variables = ['Utilization', 'Liquidation', 'Volatility']
    shocks = ['Utilization', 'Liquidation', 'Volatility']

    fig, axes = plt.subplots(3, 3, figsize=(16, 12))
    fig.suptitle('Heterogeneous IRF Heatmaps - Common Shocks\n' +
                 'Panel SVAR - DeFi Liquidations\n' +
                 'Rows = CSUs, Columns = Time Steps',
                 fontsize=14, fontweight='bold', y=0.995)

    for i in range(3):
        for j in range(3):
            ax = axes[i, j]

            col_prefix = f'IR{i+1}{j+1}_'
            cols = [col for col in df.columns if col.startswith(col_prefix)]

            if cols:
                # Create matrix: rows = CSUs, cols = time steps
                irf_matrix = df_valid[cols].values

                # Plot heatmap
                im = ax.imshow(irf_matrix, aspect='auto', cmap='RdBu_r',
                              interpolation='nearest')

                # Color bar
                plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

                # Labels
                response_var = variables[i]
                shock_var = shocks[j]
                ax.set_title(f"{response_var} (σ) → {shock_var} Shock",
                            fontsize=10, fontweight='bold')
                ax.set_xlabel('Steps (days)')
                ax.set_ylabel('CSU Index')

                # Set y-tick labels to CSU names (show subset)
                if len(df_valid) <= 15:
                    ax.set_yticks(range(len(df_valid)))
                    ax.set_yticklabels(df_valid.index, fontsize=6)

    plt.tight_layout()

    output_path = Path('data/analysis/svar_figures')
    fig.savefig(output_path / 'irf_heatmaps.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'irf_heatmaps.pdf', bbox_inches='tight')

    print(f"\n✓ Saved: {output_path}/irf_heatmaps.png")
    print(f"✓ Saved: {output_path}/irf_heatmaps.pdf")

    return fig


def main():
    print("="*70)
    print("Plotting Individual Heterogeneous IRFs")
    print("="*70)
    print()

    # Plot 1: All CSUs on same plot (one line per CSU)
    try:
        plot_individual_common_shock_irfs()
    except Exception as e:
        print(f"Error plotting overlaid IRFs: {e}")
        import traceback
        traceback.print_exc()

    # Plot 2: Separate 3x3 panel for each CSU
    try:
        plot_individual_csu_panels()
    except Exception as e:
        print(f"Error plotting individual CSU panels: {e}")
        import traceback
        traceback.print_exc()

    # Plot 3: Heatmaps showing heterogeneity
    try:
        plot_irf_heatmaps()
    except Exception as e:
        print(f"Error plotting heatmaps: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("="*70)
    print("✓ Heterogeneous IRF plotting complete!")
    print("="*70)


if __name__ == '__main__':
    main()
