# Collateral Composition Data - Data Dictionary

## Overview

Daily collateral composition (% breakdown by token) for each CSU on Ethereum.
Used to construct collateral baskets for volatility analysis.

Research question: "Do liquidations drive collateral asset volatility?"

## Files

### Per-CSU Files
- `aave_v3_ethereum.parquet` - Aave V3 collateral composition
- `compound_v3_eth_usdc.parquet` - Compound V3 USDC market collateral
- `compound_v3_eth_usdt.parquet` - Compound V3 USDT market collateral
- `compound_v3_eth_usds.parquet` - Compound V3 USDS market collateral
- `compound_v3_eth_weth.parquet` - Compound V3 WETH market collateral
- `sparklend_ethereum.parquet` - SparkLend collateral composition

### Combined File
- `all_csus_composition.parquet` - All CSUs combined

## Column Definitions

| Column | Type | Description |
|--------|------|-------------|
| `date` | string | Date in YYYY-MM-DD format |
| `csu` | string | CSU identifier |
| `symbol` | string | Token symbol (e.g., WETH, wstETH, USDC) |
| `underlying` | string | Token contract address |
| `supplied_amount` | float | Human-readable amount of tokens supplied |
| `supplied_usd` | float | USD value of supplied amount (may be null if price unavailable) |
| `pct_of_total` | float | Percentage of total collateral (0-100), based on USD values |

## Notes

1. **Data Source**: Bronze TVL snapshots from on-chain data collection

2. **USD Pricing**:
   - Chainlink oracles at historical blocks
   - Stablecoins assumed $1.00
   - Some tokens may lack USD values (no Chainlink feed)

3. **Percentage Calculation**:
   - `pct_of_total` = (token_supplied_usd / total_csu_supplied_usd) * 100
   - Only calculated when USD value is available
   - Percentages may not sum to 100% if some tokens lack prices

4. **Compound V3 Markets**:
   - Each Compound V3 market is a separate CSU
   - Collateral composition shows which assets back the base token (USDC/USDT/etc.)

## Usage Example (Python)

```python
import pandas as pd

# Load all CSUs
df = pd.read_parquet('data/gold/collateral_composition/ethereum/all_csus_composition.parquet')

# Get Aave's top collateral types on a specific date
aave = df[(df['csu'] == 'aave_v3_ethereum') & (df['date'] == '2024-06-15')]
top_collateral = aave.nlargest(5, 'pct_of_total')[['symbol', 'supplied_usd', 'pct_of_total']]

# Calculate collateral basket weights over time for a CSU
pivot = df[df['csu'] == 'aave_v3_ethereum'].pivot(
    index='date', columns='symbol', values='pct_of_total'
).fillna(0)

# Construct weighted price index (requires external price data)
# basket_return = sum(weight_i * return_i)
```

## Related Files
- `data/gold/liquidations/ethereum/daily_panel.parquet` - Daily liquidation panel
- `data/bronze/tvl/{csu}/` - Source bronze TVL data
- `data/reference/price_cache_ethereum.json` - Historical price cache
