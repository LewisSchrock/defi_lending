#!/usr/bin/env python3
"""
Plot Impulse Response Functions from Pedroni Panel SVAR Results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10

def plot_common_shock_irfs():
    """Plot impulse responses to common shocks (averaged across CSUs)."""

    # Load results
    df = pd.read_excel('output/ind-IRs-to-common-shocks.xlsx')

    print(f"Loaded common shock IRFs: {df.shape}")
    print(f"CSUs with data: {df.notna().any(axis=1).sum()}/22")

    # Variable order: 1=utilization, 2=liquidation, 3=volatility
    # IRij_k means: variable i response to shock j at step k
    variables = ['Utilization', 'Liquidation', 'Volatility']
    shocks = ['Utilization', 'Liquidation', 'Volatility']

    # Create figure
    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    fig.suptitle('Impulse Responses to Common Shocks\nHeterogeneous Panel SVAR - DeFi Liquidations (14 CSUs)\nCausal Order: Utilization → Liquidation → Volatility',
                 fontsize=14, fontweight='bold', y=0.995)

    for i in range(3):
        for j in range(3):
            ax = axes[i, j]

            # Get IRF column names: IR{i+1}{j+1}_0, IR{i+1}{j+1}_1, ..., IR{i+1}{j+1}_20
            col_prefix = f'IR{i+1}{j+1}_'
            cols = [col for col in df.columns if col.startswith(col_prefix)]

            if cols:
                # Average across CSUs (excluding NaN from failed estimations)
                irf_data = df[cols].mean(axis=0, skipna=True).values
                irf_std = df[cols].std(axis=0, skipna=True).values
                steps = np.arange(len(irf_data))

                # Plot mean IRF
                ax.plot(steps, irf_data, 'b-', linewidth=2.5, label='Mean')

                # Add confidence band (±1 std)
                ax.fill_between(steps, irf_data - irf_std, irf_data + irf_std,
                               alpha=0.2, color='blue', label='±1 SD')

                # Zero line
                ax.axhline(0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

                # Labels
                response_var = variables[i]
                shock_var = shocks[j]
                ax.set_title(f"{response_var} → {shock_var} Shock",
                            fontsize=11, fontweight='bold')
                if i == 2:
                    ax.set_xlabel('Steps (days)')
                if j == 0:
                    ax.set_ylabel('Response')
                ax.grid(True, alpha=0.3)

                # Add legend only to top-right plot
                if i == 0 and j == 2:
                    ax.legend(fontsize=8, loc='upper right')

    plt.tight_layout()

    # Save
    output_path = Path('data/analysis/svar_figures')
    output_path.mkdir(parents=True, exist_ok=True)

    fig.savefig(output_path / 'heterogeneous_common_shock_irfs.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'heterogeneous_common_shock_irfs.pdf', bbox_inches='tight')

    print(f"\n✓ Saved: {output_path}/heterogeneous_common_shock_irfs.png")
    print(f"✓ Saved: {output_path}/heterogeneous_common_shock_irfs.pdf")

    return fig


def plot_composite_shock_irfs():
    """Plot impulse responses to composite shocks (averaged across CSUs)."""

    df = pd.read_excel('output/ind-IRs-to-composite-shocks.xlsx')

    print(f"\nLoaded composite shock IRFs: {df.shape}")
    print(f"CSUs with data: {df.notna().any(axis=1).sum()}/22")

    variables = ['Utilization', 'Liquidation', 'Volatility']
    shocks = ['Utilization', 'Liquidation', 'Volatility']

    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    fig.suptitle('Impulse Responses to Composite Shocks\nHeterogeneous Panel SVAR - DeFi Liquidations (14 CSUs)\nCausal Order: Utilization → Liquidation → Volatility',
                 fontsize=14, fontweight='bold', y=0.995)

    for i in range(3):
        for j in range(3):
            ax = axes[i, j]

            col_prefix = f'IR{i+1}{j+1}_'
            cols = [col for col in df.columns if col.startswith(col_prefix)]

            if cols:
                irf_data = df[cols].mean(axis=0, skipna=True).values
                irf_std = df[cols].std(axis=0, skipna=True).values
                steps = np.arange(len(irf_data))

                ax.plot(steps, irf_data, 'r-', linewidth=2.5, label='Mean')
                ax.fill_between(steps, irf_data - irf_std, irf_data + irf_std,
                               alpha=0.2, color='red', label='±1 SD')
                ax.axhline(0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

                response_var = variables[i]
                shock_var = shocks[j]
                ax.set_title(f"{response_var} → {shock_var} Shock",
                            fontsize=11, fontweight='bold')
                if i == 2:
                    ax.set_xlabel('Steps (days)')
                if j == 0:
                    ax.set_ylabel('Response')
                ax.grid(True, alpha=0.3)

                if i == 0 and j == 2:
                    ax.legend(fontsize=8, loc='upper right')

    plt.tight_layout()

    output_path = Path('data/analysis/svar_figures')
    fig.savefig(output_path / 'heterogeneous_composite_shock_irfs.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'heterogeneous_composite_shock_irfs.pdf', bbox_inches='tight')

    print(f"\n✓ Saved: {output_path}/heterogeneous_composite_shock_irfs.png")
    print(f"✓ Saved: {output_path}/heterogeneous_composite_shock_irfs.pdf")

    return fig


def plot_lambda_matrices():
    """Plot the Lambda loading matrices for each CSU."""

    df = pd.read_excel('output/lambda-matrices.xlsx')

    print(f"\nLoaded Lambda matrices: {df.shape}")

    # Extract diagonal elements (Lambda11, Lambda22, Lambda33)
    lambda_diag = df[['Lambda11', 'Lambda22', 'Lambda33']].dropna()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle('Lambda Loadings on Common Shocks by CSU\nHeterogeneous Panel SVAR',
                 fontsize=14, fontweight='bold')

    variables = ['Utilization', 'Liquidation', 'Volatility']
    colors = ['blue', 'green', 'red']

    for i, (var, col) in enumerate(zip(variables, colors)):
        ax = axes[i]
        lambda_col = f'Lambda{i+1}{i+1}'
        data = lambda_diag[lambda_col]

        # Histogram
        ax.hist(data, bins=10, alpha=0.7, color=col, edgecolor='black')
        ax.axvline(data.mean(), color='darkred', linestyle='--', linewidth=2,
                  label=f'Mean: {data.mean():.3f}')
        ax.set_title(f'{var} Loading (λ_{i+1}{i+1})', fontweight='bold')
        ax.set_xlabel('Lambda value')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = Path('data/analysis/svar_figures')
    fig.savefig(output_path / 'lambda_loadings.png', dpi=300, bbox_inches='tight')
    fig.savefig(output_path / 'lambda_loadings.pdf', bbox_inches='tight')

    print(f"\n✓ Saved: {output_path}/lambda_loadings.png")
    print(f"✓ Saved: {output_path}/lambda_loadings.pdf")

    return fig


def main():
    print("="*70)
    print("Plotting Heterogeneous Panel SVAR Results")
    print("="*70)
    print()

    try:
        plot_common_shock_irfs()
    except Exception as e:
        print(f"Error plotting common shocks: {e}")
        import traceback
        traceback.print_exc()

    try:
        plot_composite_shock_irfs()
    except Exception as e:
        print(f"Error plotting composite shocks: {e}")
        import traceback
        traceback.print_exc()

    try:
        plot_lambda_matrices()
    except Exception as e:
        print(f"Error plotting lambda matrices: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("="*70)
    print("✓ Plotting complete!")
    print("="*70)


if __name__ == '__main__':
    main()
