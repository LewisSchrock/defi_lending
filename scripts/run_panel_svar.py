#!/usr/bin/env python3
"""
Run Pedroni Panel SVAR Analysis on DeFi Liquidations
Heterogeneous Panel SVAR with common structural identification
"""

import sys
from pathlib import Path

# Add pedroni_svar code to path
sys.path.insert(0, str(Path('code/pedroni_svar')))

from SVAR import *
from panelSVAR import *
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")

# Configuration
plot = True
savefig_path = "data/analysis/svar_figures/"
excel_path = "data/analysis/panel_svar_data_qualified.xlsx"
excel_sheet_name = "panel_data"

# Create required directories
Path("output").mkdir(parents=True, exist_ok=True)
Path(savefig_path).mkdir(parents=True, exist_ok=True)

# Variables: [input_form, output_form]
# 0 = stationary, 1 = unit root
variables = {
    'utilization': [0, 0],  # Stationary (most exogenous)
    'liquidation': [0, 0],  # Stationary (middle)
    'volatility': [0, 0],   # Stationary (most endogenous)
}

# IMPORTANT: Order reflects causal structure
# Utilization → Liquidation → Volatility
variable_order = ['utilization', 'liquidation', 'volatility']
shocks = ['Utilization Shock', 'Liquidation Shock', 'Volatility Shock']

# Panel structure
td_col = ["date"]
member_col = "csu"

# Long-run restrictions (Cholesky ordering)
# Causal chain: Utilization causes Liquidation causes Volatility
lr_constraint = np.array([
    ['.', '0', '0'],  # Utilization: only utilization shock has long-run effect
    ['.', '.', '0'],  # Liquidation: utilization & liquidation shocks have effects
    ['.', '.', '.']   # Volatility: all shocks have long-run effects
])

# This means:
# - Utilization shock → affects utilization, liquidation, volatility (most exogenous)
# - Liquidation shock → affects liquidation, volatility (not utilization)
# - Volatility shock → affects volatility only (most endogenous)

# Sign restrictions (required: one per column)
lr_sign = np.array([
    ['+', '.', '.'],  # Utilization shock → positive utilization
    ['.', '+', '.'],  # Liquidation shock → positive liquidation
    ['.', '.', '+']   # Volatility shock → positive volatility
])

sr_constraint = np.array([])  # No short-run constraints

# Analysis parameters
maxlags = 7       # Test up to 7 lags
nsteps = 20       # 20-step impulse responses
lagmethod = 'aic' # Use AIC for lag selection

# Bootstrap
bootstrap = True
ndraws = 1000
signif = 0.05

print("="*70)
print("PEDRONI PANEL SVAR ANALYSIS - DEFI LIQUIDATIONS")
print("="*70)
print(f"\nMethodology: Heterogeneous Panel SVAR (Pedroni 2013)")
print(f"  - Common structural identification (shared M matrix)")
print(f"  - Heterogeneous VAR coefficients per CSU")
print(f"  - Heterogeneous Lambda loadings per CSU")
print(f"\nCausal ordering: Utilization → Liquidation → Volatility")
print(f"Standardization: Per-CSU z-score (IRFs in std dev units)")
print(f"Variables: {variable_order}")
print(f"CSUs: 22 qualified protocols")
print(f"Max lags: {maxlags}, Steps: {nsteps}")
print(f"Bootstrap: {bootstrap} ({ndraws} draws, {signif*100}% significance)")
print("="*70)
print()

# Create input object
panel_input = VAR_input(
    variables=variables,
    variable_order=variable_order,
    shocks=shocks,
    td_col=td_col,
    member_col=member_col,
    M=None,
    sr_constraint=sr_constraint,
    lr_constraint=lr_constraint,
    lr_sign=lr_sign,
    maxlags=maxlags,
    nsteps=nsteps,
    lagmethod=lagmethod,
    bootstrap=bootstrap,
    ndraws=ndraws,
    signif=signif,
    excel_path=excel_path,
    excel_sheet_name=excel_sheet_name,
    df=pd.DataFrame(),
    plot=plot,
    savefig_path=savefig_path
)

print("Running Pedroni Panel SVAR...")
print("This may take 5-10 minutes (1000 bootstrap draws)...\n")

# Run analysis
output = panelSVAR(panel_input)

print("\n" + "="*70)
print("✓ ANALYSIS COMPLETE!")
print("="*70)
print(f"\nResults saved to:")
print(f"  - output/ind-IRs-to-common-shocks.xlsx")
print(f"  - output/ind-IRs-to-composite-shocks.xlsx")
print(f"  - output/ind-IRs-to-idiosyncratic-shocks.xlsx")
print(f"  - output/lambda-matrices.xlsx")
print(f"\nFigures saved to: {savefig_path}")
print("="*70)
