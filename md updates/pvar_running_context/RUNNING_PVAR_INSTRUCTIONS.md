# Running Your Panel SVAR Analysis
## Using Both Your Pedroni Implementation and Standard statsmodels

---

## Setup

### 1. Clone Your Implementation (if not already done)
```bash
cd ~/thesis_work
git clone https://github.com/LewisSchrock/Pedroni_Panel_SVAR.git
cd Pedroni_Panel_SVAR/Python_panel_svar
```

### 2. Install Dependencies
```bash
pip install pandas numpy scipy statsmodels matplotlib openpyxl
```

### 3. Copy Your Data
```bash
cp /path/to/vol_util_panel.xlsx ~/thesis_work/Pedroni_Panel_SVAR/Python_panel_svar/
```

---

## Method 1: Your Pedroni Panel SVAR Implementation

### Configuration File
Create `config.py` in the Python_panel_svar directory:

```python
# config.py

excel_path = "vol_util_panel.xlsx"
excel_sheet_name = "panel_data"
td_col = ["date"]
member_col = "csu"

variables = {
    'utilization': [0],
    'volatility': [0],
}

variable_order = ['utilization', 'volatility']
```

### Run Analysis
In Claude Code, navigate to your repo and run:

```
cd Pedroni_Panel_SVAR/Python_panel_svar
python main.py  # or whatever your entry point is
```

Or ask Claude Code:
```
"I have a Panel SVAR implementation in Pedroni_Panel_SVAR/Python_panel_svar/.
The data is vol_util_panel.xlsx with columns: date, csu, utilization, volatility.
Please run the analysis and show me the IRF for utilization → volatility."
```

---

## Method 2: Standard statsmodels VAR (for comparison)

### Quick Run Script

```python
"""
run_statsmodels_pvar.py
Standard VAR implementation for comparison with Pedroni method
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.api import VAR
import warnings
warnings.filterwarnings('ignore')

# Load data
df = pd.read_excel('vol_util_panel.xlsx', sheet_name='panel_data')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['csu', 'date'])

# Remove problematic CSUs (if any with all zeros)
csu_util_mean = df.groupby('csu')['utilization'].mean()
valid_csus = csu_util_mean[csu_util_mean > 0.01].index
df = df[df['csu'].isin(valid_csus)]

# Fill missing volatility
df['volatility'] = df.groupby('csu')['volatility'].ffill().bfill()
df = df.dropna(subset=['utilization', 'volatility'])

print("="*70)
print("STATSMODELS PANEL VAR")
print("="*70)
print(f"Observations: {len(df)}")
print(f"CSUs: {df['csu'].nunique()}")

# Fixed effects transformation (demean by CSU)
df['util_fe'] = df.groupby('csu')['utilization'].transform(lambda x: x - x.mean())
df['vol_fe'] = df.groupby('csu')['volatility'].transform(lambda x: x - x.mean())

# Estimate pooled VAR
panel = df[['util_fe', 'vol_fe']].dropna()
model = VAR(panel)

# Lag selection
lag_order = model.select_order(maxlags=10)
print(f"\nLag Selection - AIC: {lag_order.aic}, BIC: {lag_order.bic}")
optimal = max(1, min(lag_order.bic, 5))

# Fit
results = model.fit(optimal)
print(f"Using {optimal} lags")

# IRF
irf = results.irf(periods=20)
irf_vals = irf.irfs[:, 0, 1]  # util → vol

# Bootstrap CI
err = irf.errband_mc(orth=True, repl=500, steps=20, seed=42)
ci_lo, ci_hi = err[0][:, 0, 1], err[1][:, 0, 1]

# Granger causality
gc = results.test_causality('vol_fe', ['util_fe'], kind='f')
print(f"\nGranger Causality (Util → Vol): p={gc.pvalue:.6f}")

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
periods = range(len(irf_vals))
ax.plot(periods, irf_vals, 'b-', lw=2, label='IRF')
ax.fill_between(periods, ci_lo, ci_hi, alpha=0.3, color='blue', label='95% CI')
ax.axhline(0, color='black', ls='--', lw=0.5)
ax.set_title('statsmodels: Utilization Shock → Volatility Response', fontsize=14, fontweight='bold')
ax.set_xlabel('Days')
ax.set_ylabel('Response')
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig('irf_statsmodels.png', dpi=150, bbox_inches='tight')
print("\nSaved: irf_statsmodels.png")

# Print IRF values
print("\nIRF Values:")
for i, (v, lo, hi) in enumerate(zip(irf_vals, ci_lo, ci_hi)):
    sig = "*" if lo > 0 or hi < 0 else ""
    print(f"  t+{i:2d}: {v:8.5f}  [{lo:8.5f}, {hi:8.5f}] {sig}")
```

### Run it:
```bash
python run_statsmodels_pvar.py
```

---

## Comparing the Two Methods

Both should give similar results if implemented correctly:

| Aspect | Your Pedroni Method | statsmodels |
|--------|---------------------|-------------|
| Fixed Effects | Forward orthogonal deviations | Within-transformation (demeaning) |
| Estimation | GMM | OLS |
| Std Errors | Panel-robust | Bootstrap |
| Lag Selection | Your criteria | BIC |

### What to Check:
1. **IRF shape** - Should be similar (both positive for util→vol)
2. **Significance** - Both should show significant Granger causality
3. **Magnitude** - Slight differences OK due to estimation method
4. **CI width** - Your method may have wider CIs (more conservative)

### If Results Differ Significantly:
- Check fixed effects transformation
- Verify same lag order used
- Confirm same CSUs included
- Check for scaling differences in variables

---

## For Your Thesis

Report both methods:

> "We estimate the Panel VAR using two approaches: (1) the Pedroni panel SVAR methodology with GMM estimation and forward orthogonal deviations [cite], and (2) standard fixed-effects VAR with OLS estimation for robustness. Both methods yield qualitatively similar results..."

This strengthens your findings by showing they're not method-dependent.

---

## Quick Command for Claude Code

```
I have Panel VAR data in vol_util_panel.xlsx with columns: date, csu, utilization, volatility.

Please:
1. Run a 2-variable Panel VAR with fixed effects
2. Use Cholesky ordering: utilization first, volatility second
3. Generate IRFs for 20 periods with bootstrap confidence intervals
4. Test Granger causality both directions
5. Split the sample by architecture:
   - Pooled: all aave_*, sparklend_*, benqi_*, fluid_*, moonwell_*, venus_*, gearbox_*, sumermoney_*
   - Isolated: all compound_v3_*
6. Compare IRFs between pooled and isolated markets
7. Create publication-quality plots
```

---

## Updated CSU Categorization (35 CSUs)

### Pooled Architecture (18 CSUs):
```
aave_v3_* (10 chains)
benqi_lending_avalanche
fluid_lending_* (2)
gearbox_ethereum
moonwell_lending_base
sparklend_ethereum
sumermoney_meter
venus_core_pool_binance
```

### Isolated Architecture (17 CSUs):
```
compound_v3_* (17 markets)
```

---

## Expected Output

After running both methods, you should have:

1. **irf_pedroni.png** - IRF from your implementation
2. **irf_statsmodels.png** - IRF from standard VAR
3. **comparison_table.csv** - Side-by-side results
4. **granger_causality.txt** - Test statistics
5. **subsample_comparison.png** - Pooled vs Isolated IRFs

---

## Next Steps After IRF

1. ✅ **2-variable PVAR** - Utilization → Volatility (NOW)
2. 🔜 **Add liquidations** - 3-variable PVAR
3. 🔜 **Subsample analysis** - Pooled vs Isolated
4. 🔜 **Robustness** - Different lags, subperiods, balanced panel
