#!/usr/bin/env python3
"""
Plot Impulse Response Functions from Panel SVAR Results

Reads the Excel output files and creates publication-quality IRF plots.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 10

def plot_common_shock_irfs():
    """Plot impulse responses to common shocks."""

    # Load results
    df = pd.read_excel('output/ind-IRs-to-common-shocks.xlsx')

    print(f"Loaded common shock IRFs: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    # Variables and shocks
    variables = ['liquidation', 'utilization', 'volatility']
    shocks = ['Liquidation', 'Utilization', 'Volatility']

    # Create figure
    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    fig.suptitle('Impulse Responses to Common Shocks\nPanel SVAR - DeFi Liquidations (22 CSUs)',
                 fontsize=16, fontweight='bold')

    for i, var in enumerate(variables):
        for j, shock in enumerate(shocks):
            ax = axes[i, j]

            # Find the column for this var-shock combination
            # Column names might be like "liquidation_Liquidation_0", "liquidation_Liquidation_1", etc.
            cols = [col for col in df.columns if col.startswith(f"{var}_{shock}_")]

            if cols:
                # Get the IRF data
                irf_data = df[cols].values
                steps = len(irf_data)

                # Plot
                ax.plot(range(steps), irf_data, 'b-', linewidth=2, alpha=0.7)
                ax.axhline(0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
                ax.fill_between(range(steps), 0, irf_data.flatten(), alpha=0.2)

                # Labels
                ax.set_title(f"{var.capitalize()} → {shock}", fontsize=11, fontweight='bold')
                ax.set_xlabel('Steps' if i == 2 else '')
                ax.set_ylabel('Response' if j == 0 else '')
                ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save
    output_path = Path('data/analysis/svar_figures')
    output_path.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path / 'common_shock_irfs.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'common_shock_irfs.pdf', bbox_inches='tight')

    print(f"✓ Saved: {output_path}/common_shock_irfs.png")
    print(f"✓ Saved: {output_path}/common_shock_irfs.pdf")

    return fig


def plot_composite_shock_irfs():
    """Plot impulse responses to composite shocks."""

    df = pd.read_excel('output/ind-IRs-to-composite-shocks.xlsx')

    print(f"\nLoaded composite shock IRFs: {df.shape}")

    variables = ['liquidation', 'utilization', 'volatility']
    shocks = ['Liquidation', 'Utilization', 'Volatility']

    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    fig.suptitle('Impulse Responses to Composite Shocks\nPanel SVAR - DeFi Liquidations (22 CSUs)',
                 fontsize=16, fontweight='bold')

    for i, var in enumerate(variables):
        for j, shock in enumerate(shocks):
            ax = axes[i, j]

            cols = [col for col in df.columns if col.startswith(f"{var}_{shock}_")]

            if cols:
                irf_data = df[cols].values
                steps = len(irf_data)

                ax.plot(range(steps), irf_data, 'r-', linewidth=2, alpha=0.7)
                ax.axhline(0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
                ax.fill_between(range(steps), 0, irf_data.flatten(), alpha=0.2, color='red')

                ax.set_title(f"{var.capitalize()} → {shock}", fontsize=11, fontweight='bold')
                ax.set_xlabel('Steps' if i == 2 else '')
                ax.set_ylabel('Response' if j == 0 else '')
                ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = Path('data/analysis/svar_figures')
    fig.savefig(output_path / 'composite_shock_irfs.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'composite_shock_irfs.pdf', bbox_inches='tight')

    print(f"✓ Saved: {output_path}/composite_shock_irfs.png")
    print(f"✓ Saved: {output_path}/composite_shock_irfs.pdf")

    return fig


def main():
    print("="*70)
    print("Plotting Panel SVAR Results")
    print("="*70)
    print()

    # Plot common shocks
    try:
        fig1 = plot_common_shock_irfs()
    except Exception as e:
        print(f"Error plotting common shocks: {e}")
        import traceback
        traceback.print_exc()

    # Plot composite shocks
    try:
        fig2 = plot_composite_shock_irfs()
    except Exception as e:
        print(f"Error plotting composite shocks: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("="*70)
    print("✓ Plotting complete!")
    print("="*70)


if __name__ == '__main__':
    main()
