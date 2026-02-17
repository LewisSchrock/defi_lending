# Pedroni Panel SVAR Analysis — February 16, 2026

## What Was Run

A **Pedroni (2013) Panel SVAR** was estimated on a balanced daily panel of 30 DeFi lending protocol cross-sectional units (CSUs) spanning January 1, 2024 through December 31, 2025 (20,012 observations). This is the core empirical test for the thesis, which studies shock transmission across decentralized lending markets.

### Methodology: Pedroni (2013) Panel Structural VAR

Unlike a standard pooled fixed-effects VAR (which assumes homogeneous dynamics across all panel members), the Pedroni Panel SVAR estimates **heterogeneous member-specific SVARs** for each CSU individually, then decomposes their structural shocks into **common** (shared across all members) and **idiosyncratic** (market-specific) components via a **Lambda (Λ) matrix**.

- **Reference:** Pedroni, P. (2013). "Structural Panel VARs." *Econometrics*, 1(2), 180–206.
- **Implementation:** Python package at `code/pedroni_svar/` (classes `VAR_input`, `SVAR`, `panelSVAR`, `Panel_output`), originally from [github.com/LewisSchrock/Pedroni_Panel_SVAR](https://github.com/LewisSchrock/Pedroni_Panel_SVAR).
- **Key output per member:** Composite IRFs (total response), Common IRFs (response to the shared component of the shock), Idiosyncratic IRFs (response to the market-specific component), and the diagonal Lambda matrix measuring the common-vs-idiosyncratic split.

### Identification

- **Cholesky ordering (lower-triangular):** utilization → liquidation → volatility
- **Interpretation:** Utilization (leverage) is the slowest-moving variable — borrowing decisions are sticky. Liquidation events are mechanical responses triggered within the day. Volatility is the fastest — it reflects market-wide information arrival.
- **SR constraints:** Lower-triangular M matrix with positive signs on the diagonal.
- **Lag selection:** BIC (max 10 lags). **IRF horizon:** 20 steps (days).

### Variables

| Variable | Definition | Construction |
|---|---|---|
| **utilization** | Borrowed USD / Supplied USD | Direct from protocol smart contracts via `silver/tvl/daily_tvl.csv`. Bounded [0, 1]. Proxy for aggregate leverage in the lending pool. |
| **liquidation** | log(1 + total_collateral_usd) | Log-transformed USD value of collateral seized. `total_collateral_usd` aggregated from on-chain liquidation events (gold layer), then log(1+x) transformed to handle zero-inflation (most CSU-days have zero liquidations). |
| **volatility** | 14-day rolling std of collateral basket log returns | Collateral basket is the TVL-weighted portfolio of all collateral assets in the lending pool. Daily log returns computed from Chainlink oracle prices, then 14-day rolling standard deviation. |

### Panel Composition

30 CSUs across 10+ EVM chains. Three CSUs were excluded from the original 33 due to data issues:
- `cap_ethereum` — no liquidation events in sample
- `sonne_lending_optimism` — no liquidation events in sample
- `fluid_lending_ethereum` — utilization exceeds 1.0 (LiquidityResolver reports protocol-wide borrows including DEX vaults)

**CSU list:**

| Protocol Type | CSUs |
|---|---|
| **Aave V3** (10) | aave_v3_ethereum, aave_v3_base, aave_v3_arbitrum, aave_v3_optimism, aave_v3_polygon, aave_v3_avalanche, aave_v3_binance, aave_v3_linea, aave_v3_scroll, aave_v3_xdai |
| **Compound V3** (12) | compound_v3_eth_usdc, compound_v3_eth_usdt, compound_v3_eth_usds, compound_v3_eth_weth, compound_v3_arb_usdc, compound_v3_arb_usdc_e, compound_v3_arb_usdt, compound_v3_arb_weth, compound_v3_base_usdc, compound_v3_base_usdbc, compound_v3_base_weth, compound_v3_base_aero |
| **Other pooled** (8) | compound_v2_ethereum, sparklend_ethereum, moonwell_lending_base, benqi_lending_avalanche, venus_core_pool_binance, fluid_lending_arbitrum, lodestar_lending_arbitrum, mendi_lending_linea |

### Subsample Comparisons

Seven subsamples were estimated to test three dimensions of heterogeneity:

**Architecture (pooled vs isolated risk):**
- **Pooled** (18 CSUs): Shared liquidity pool where all borrowers/collateral types coexist (Aave V3, Compound V2, SparkLend, etc.)
- **Isolated** (12 CSUs): Each Compound V3 market has its own isolated risk pool with a single base asset

**Liquidation Mechanism:**
- **Aave-Style / Instant** (18 CSUs): Any third-party liquidator can seize discounted collateral the moment health factor < 1. Creates a competitive, MEV-driven liquidation market.
- **Compound V3 / Absorb** (12 CSUs): The protocol itself absorbs the underwater position via `absorb()`, then sells collateral through its own mechanism. Centralizes liquidation execution.

**Chain Environment:**
- **Ethereum L1** (7 CSUs): High gas costs, deep liquidity, mature MEV infrastructure
- **Arbitrum L2** (7 CSUs): Low gas costs, growing liquidity, Arbitrum-native protocols
- **Base L2** (6 CSUs): Low gas costs, Coinbase-affiliated ecosystem, newer protocols

---

## Key Results

All subsamples achieved **100% member estimation** (every CSU successfully estimated), a major improvement over v2.9 where 5/12 members failed due to positive-definiteness issues. The expanded panel (30 CSUs, 730 dates) provides far more stable estimates.

### Finding 1: Volatility Shocks Are Overwhelmingly Common (Systemic)

The Lambda decomposition reveals a clean hierarchy in how shocks propagate:

| Variable | Median λ (Full Sample) | Interpretation |
|---|---|---|
| **Volatility** | **0.88** | ~88% of volatility shocks are common — nearly every market responds to the same global crypto volatility regime |
| **Liquidation** | **0.56** | ~56% common — liquidation shocks are moderately shared, with a substantial idiosyncratic component |
| **Utilization** | **0.18** | ~82% idiosyncratic — leverage decisions are overwhelmingly local/market-specific |

**Implication:** Volatility is systemic risk. When crypto markets move, all lending protocols feel it simultaneously. But *how much* a protocol lends (utilization) is determined by local factors — governance parameters, token incentives, user base composition. Liquidation activity sits in between: partially driven by the common volatility shock, partially by market-specific conditions (collateral composition, liquidator competition, protocol design).

### Finding 2: Pooled Architecture Massively Amplifies Liquidation Persistence

The architecture comparison produces the largest structural difference in the analysis:

| IRF Path | Pooled (h=10) | Isolated (h=10) | Ratio |
|---|---|---|---|
| **Liq → Liq (self-persistence)** | **2.40** | **0.45** | **5.4×** |
| Vol → Liq (volatility spillover) | 0.118 | -0.010 | sign flip |
| Util → Liq | -0.032 | +0.010 | sign flip |

- **5.4× amplification:** In shared liquidity pools, liquidation events are 5.4 times more persistent than in isolated markets. A liquidation cascade in a pooled protocol echoes for much longer.
- **Volatility → Liquidation channel activates only in pooled architecture:** In pooled protocols, a volatility shock generates cumulative liquidation activity of 0.118. In isolated markets, the same channel is essentially zero (-0.010). Shared liquidity pools transmit volatility shocks into liquidation cascades; isolated pools do not.
- **Sign flip on Utilization → Liquidation:** In pooled protocols, higher utilization is associated with *fewer* subsequent liquidations (-0.032), possibly reflecting deleveraging dynamics where rising utilization triggers risk-off behavior before liquidations occur. In isolated markets, the relationship is weakly positive.

### Finding 3: Volatility Is the Dominant Cross-Variable Transmission Channel

From the full sample median cumulative IRFs (h=10):

| Path | Cumulative IRF | Interpretation |
|---|---|---|
| Liq → Vol | +0.009 | Liquidation events persistently feed back into market volatility |
| Vol → Util | -0.002 | Volatility shocks cause slight deleveraging (markets reduce leverage) |
| Util → Liq | -0.004 | Higher leverage does *not* directly trigger liquidations in the median market |
| Vol → Liq | +0.011 | Volatility is the trigger — it drives liquidation activity |
| Liq → Util | +0.002 | Liquidations mildly increase utilization (mechanical: supply withdrawn > debt repaid) |

The key narrative: **Volatility shocks trigger liquidations, which feed back into more volatility.** Utilization is relatively inert — it doesn't cause liquidations directly, and it doesn't respond strongly to volatility. The action is in the volatility-liquidation feedback loop.

### Finding 4: L2 Chains Have Stronger Utilization Persistence, L1 Has More Common Liquidation Shocks

| Metric | Ethereum L1 | Arbitrum L2 | Base L2 |
|---|---|---|---|
| Util self-persistence (h=10) | 0.061 | 0.103 | 0.114 |
| Median λ_vol | 0.884 | 0.908 | 0.939 |
| Median λ_liq | 0.714 | 0.653 | 0.601 |
| Median λ_util | 0.260 | 0.192 | 0.368 |

- **L2 utilization is stickier:** Arbitrum and Base markets maintain leverage levels 1.7–1.9× longer than Ethereum L1. Lower gas costs may reduce the frequency of position adjustments.
- **Base has the highest λ_vol (0.94):** Base markets are the most tightly coupled to global crypto volatility — almost pure common shocks. Newer ecosystem with less idiosyncratic activity.
- **Ethereum L1 has the highest λ_liq (0.71):** Liquidation shocks on mainnet are more commonly shared, likely because MEV bots operate in a more interconnected, competitive environment there. L2 liquidation markets are more fragmented.

### Finding 5: Compound V2 Ethereum Is a Structural Outlier

While nearly every CSU has λ_vol > 0.70, **Compound V2 Ethereum has λ_vol = 0.15** — its volatility dynamics are 85% idiosyncratic. This likely reflects Compound V2's legacy architecture with fixed collateral factors and a distinct user base that has not migrated to V3. It operates in its own volatility regime.

Similarly, **compound_v3_base_aero** (λ_liq = 0.01) and **compound_v3_base_weth** (λ_liq = 0.04) have almost entirely idiosyncratic liquidation patterns. Their niche collateral types (AERO governance token, WETH on Base) create unique liquidation dynamics disconnected from the common factor.

---

## File Locations

| File | Path |
|---|---|
| **Notebook (source)** | `notebooks/pedroni_3var_analysis.ipynb` |
| **Notebook (executed)** | `notebooks/pedroni_3var_analysis_executed.ipynb` |
| **Input data** | `data/analysis/panel_svar_data.parquet` (also `.xlsx`) |
| **Pedroni SVAR package** | `code/pedroni_svar/` (`SVAR.py`, `panelSVAR.py`) |
| **1st-order results** | `results/pedroni/1st_order/` (full sample IRFs, lambda, cumulative tables) |
| **Architecture results** | `results/pedroni/2nd_order/architecture/` (pooled vs isolated) |
| **Mechanism results** | `results/pedroni/2nd_order/mechanism/` (Aave-style vs Compound V3) |
| **Chain results** | `results/pedroni/2nd_order/chain/` (Ethereum vs Arbitrum vs Base) |

## Reproducing

```bash
cd notebooks/
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=600 \
    pedroni_3var_analysis.ipynb --output pedroni_3var_analysis_executed.ipynb
```

Requires: numpy, pandas, matplotlib, seaborn, statsmodels, openpyxl. The Pedroni SVAR package at `code/pedroni_svar/` is added to `sys.path` at runtime.
