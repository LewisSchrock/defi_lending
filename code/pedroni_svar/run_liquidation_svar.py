"""
Run Panel SVAR Analysis on DeFi Liquidation Data

Analyzes the relationship between:
- Liquidation (log-transformed USD value of collateral seized)
- Utilization (leverage ratio = borrowed/supplied)
- Volatility (rolling std of collateral basket returns)

Using Pedroni (2013) Panel SVAR methodology
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from SVAR import *
from panelSVAR import *
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore", category=UserWarning, module="statsmodels")

def run_liquidation_panel():
    """Run Panel SVAR on DeFi liquidation data."""

    # Configuration
    plot = True
    savefig_path = "../../data/analysis/svar_figures/"
    excel_path = "../../data/analysis/panel_svar_data_qualified.xlsx"
    excel_sheet_name = "panel_data"

    # Variables (all stationary, no unit root)
    variables = {
        'liquidation': [0],   # log(1 + total_collateral_usd)
        'utilization': [0],   # Leverage ratio (0-1)
        'volatility': [0],    # Collateral basket volatility
    }

    variable_order = ['liquidation', 'utilization', 'volatility']
    shocks = ['Liquidation Shock', 'Utilization Shock', 'Volatility Shock']

    # Panel structure
    td_col = ["date"]
    member_col = "csu"

    # Identification constraints
    # Long-run restrictions (Cholesky-style ordering)
    lr_constraint = np.array([
        ['.', '0', '0'],  # Liquidation affects all
        ['.', '.', '0'],  # Utilization affects util & vol
        ['.', '.', '.']   # Volatility affects only itself
    ])

    sr_constraint = np.array([])  # No short-run constraints
    sr_sign = np.array([
        ['.', '.', '.'],
        ['.', '.', '.'],
        ['.', '.', '.']
    ])

    # Analysis parameters
    maxlags = 7      # Test up to 7 lags (weekly patterns)
    nsteps = 20      # 20-step impulse responses
    lagmethod = 'aic'  # Use AIC for lag selection

    # Bootstrap
    bootstrap = True
    ndraws = 2000
    signif = 0.05

    print("=" * 80)
    print("Running Panel SVAR Analysis on DeFi Liquidation Data")
    print("=" * 80)
    print(f"\nData: {excel_path}")
    print(f"Panel structure: {member_col} (cross-section) x {td_col} (time)")
    print(f"Variables: {variable_order}")
    print(f"Max lags: {maxlags}, Steps: {nsteps}")
    print(f"Bootstrap: {bootstrap} ({ndraws} draws, {signif} significance)")
    print()

    # Create output directory
    Path(savefig_path).mkdir(parents=True, exist_ok=True)

    # Run Panel SVAR
    panel_input = VAR_input(
        variables=variables,
        variable_order=variable_order,
        shocks=shocks,
        td_col=td_col,
        member_col=member_col,
        M=None,
        sr_constraint=sr_constraint,
        lr_constraint=lr_constraint,
        sr_sign=sr_sign,
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

    print("\nRunning Pedroni Panel SVAR...")
    output = panelSVAR(panel_input)

    print("\n" + "=" * 80)
    print("Analysis Complete")
    print("=" * 80)
    print(f"Figures saved to: {savefig_path}")

    return output


if __name__ == "__main__":
    run_liquidation_panel()
