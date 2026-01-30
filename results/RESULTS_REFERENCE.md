# Panel VAR Results Reference

> Generated from `notebooks/pvar_3var_analysis.ipynb`
> Data source: `data/gold/panel_base_eth/gold_panel_base_eth.parquet`
> Last updated: 2025-01-29

---

## 1. Data Structure

### Gold Panel
- **File:** `data/gold/panel_base_eth/gold_panel_base_eth.parquet` (also `.xlsx`)
- **Dimensions:** 12 CSUs × 364 days = 4,368 observations
- **Date range:** 2024-01-03 to 2024-12-31
- **After dropping missing util/vol:** 3,274 observations (75% coverage — remaining gaps are markets not yet deployed)

### Variables
| Variable | Column | Definition | Transform |
|----------|--------|-----------|-----------|
| Utilization | `utilization` | `total_borrow_usd / total_supply_usd` | Bounded [0, 1] |
| Volatility | `volatility` | 14-day rolling std of collateral basket log returns | Computed from bronze TVL + price cache |
| Liquidation | `liquidation` | `log1p(total_collateral_usd)` | Log(1+x) to handle zeros and skewness |

### CSUs (Cross-Sectional Units)
| CSU | Chain | Architecture | Mechanism |
|-----|-------|-------------|-----------|
| aave_v3_ethereum | Ethereum | Pooled | Aave-Style (Instant) |
| aave_v3_base | Base | Pooled | Aave-Style (Instant) |
| sparklend_ethereum | Ethereum | Pooled | Aave-Style (Instant) |
| moonwell_lending_base | Base | Pooled | Aave-Style (Instant) |
| compound_v3_eth_usdc | Ethereum | Isolated | Compound V3 (Absorb) |
| compound_v3_eth_usdt | Ethereum | Isolated | Compound V3 (Absorb) |
| compound_v3_eth_usds | Ethereum | Isolated | Compound V3 (Absorb) |
| compound_v3_eth_weth | Ethereum | Isolated | Compound V3 (Absorb) |
| compound_v3_eth_wsteth | Ethereum | Isolated | Compound V3 (Absorb) |
| compound_v3_base_usdc | Base | Isolated | Compound V3 (Absorb) |
| compound_v3_base_weth | Base | Isolated | Compound V3 (Absorb) |
| compound_v3_base_aero | Base | Isolated | Compound V3 (Absorb) |

---

## 2. Methodology

### Panel VAR Specification
- **Fixed effects:** Within-transformation (demean each variable by CSU) to remove unit-specific means
- **Lag selection:** BIC with max 10 lags, capped at 5
- **IRF identification:** Cholesky decomposition (orthogonalized IRFs)
- **IRF horizon:** 20 periods (days)
- **Confidence intervals:** Residual bootstrap, 500 replications, 95% CIs (2.5th/97.5th percentile)
- **Granger causality:** F-test on excluded lags, all 6 pairwise directions in the 3-variable system

### Cholesky Orderings Used
| Analysis | Ordering | Rationale |
|----------|----------|-----------|
| Sections 6–16 (Baseline) | Util → Vol → Liq | Slow to fast: leverage decisions → market conditions → liquidation events |
| Section 17 (Robustness) | Util → Liq → Vol | Liquidations as mechanical events that feed into volatility |
| Sections 18, 20 (Mechanism & Chain) | Util → Liq → Vol | Same as robustness ordering |

---

## 3. Tests Run

### Test A: Baseline 3-Variable PVAR (Sections 6–16)
**Ordering:** Util → Vol → Liq
**Subsamples:** Full Sample (12), Base Chain (5), Ethereum (7), Pooled (4), Isolated (8)

#### Granger Causality Results (Table 2)
| Direction | Full Sample | Base Chain | Ethereum | Pooled | Isolated |
|-----------|-------------|------------|----------|--------|----------|
| Util → Vol | p=0.1807 | p=0.6890 | p=0.9524 | p=0.4431 | p=0.4142 |
| Vol → Util | p=0.4794 | p=0.7902 | p=0.3649 | p=0.8186 | p=0.4305 |
| Util → Liq | p=0.7933 | p=0.5918 | p=0.7917 | p=0.3132 | p=0.6864 |
| Liq → Util | p=0.1579 | p=0.8326 | p=0.0724* | p=0.0033*** | p=0.5188 |
| Vol → Liq | p=0.0248** | p=0.1645 | p=0.0203** | p=0.0088*** | p=0.5193 |
| Liq → Vol | p=0.0000*** | p=0.0002*** | p=0.0000*** | p=0.0000*** | p=0.0089*** |

**Key finding:** Liq→Vol is significant across ALL subsamples. Vol→Liq is significant for Full Sample, Ethereum, and Pooled. Liq→Util is significant for Pooled architecture.

#### IRF Summary (Table 3 — selected paths)
| Sample | Path | Cumulative | Peak | Peak Period | Sig Horizons |
|--------|------|-----------|------|-------------|-------------|
| Full Sample | Liq → Vol | -0.56577 | 0.12611 | t+0 | 20/21 |
| Full Sample | Vol → Liq | 0.00743 | 0.00063 | t+3 | 0/21 |
| Full Sample | Liq → Util | 0.18915 | 0.01632 | t+3 | 0/21 |
| Pooled | Liq → Vol | -1.09479 | 0.22994 | t+0 | 20/21 |
| Pooled | Liq → Util | 0.39468 | -0.13486 | t+0 | 0/21 |
| Pooled | Vol → Liq | 0.01059 | 0.00087 | t+3 | 0/21 |
| Isolated | Liq → Vol | -0.13926 | 0.05091 | t+0 | 0/21 |
| Isolated | Util → Vol | -0.01173 | -0.00083 | t+13 | 19/21 |

#### FEVD (Full Sample, h=20)
| Variable explained by → | Util | Vol | Liq |
|-------------------------|------|-----|-----|
| Utilization | 99.9% | 0.0% | 0.1% |
| Volatility | 0.0% | 98.6% | 1.4% |
| Liquidation | 0.0% | 0.2% | 99.8% |

---

### Test B: Cholesky Ordering Robustness (Section 17)
**Comparison:** Util→Vol→Liq (baseline) vs Util→Liq→Vol (alternative)

#### Key Result (Table 5 — Full Sample)
| IRF Path | Baseline Cum | Alt Cum | Diff | Base Sig | Alt Sig |
|----------|-------------|---------|------|----------|---------|
| Util → Vol | -0.00377 | -0.00391 | -0.00014 | 2/21 | 6/21 |
| Vol → Liq | 0.00743 | 0.00910 | +0.00168 | 0/21 | 1/21 |
| Liq → Vol | -0.56577 | -0.74324 | -0.17747 | 20/21 | 19/21 |
| Liq → Util | 0.18915 | 0.18915 | 0.00000 | 0/21 | 0/21 |

**Key finding:** Results are robust to ordering. Same paths are significant. Liq→Util and Vol→Util are invariant (identical cumulative values). Liq→Vol is larger under the alternative (vol no longer absorbs contemporaneous liq shocks).

---

### Test C: Liquidation Mechanism Comparison (Section 18)
**Ordering:** Util → Liq → Vol
**Subsamples:**
- Aave-Style (Instant): 4 CSUs — aave_v3_ethereum, aave_v3_base, moonwell_lending_base, sparklend_ethereum
- Compound V3 (Absorb): 8 CSUs — all compound_v3_* markets

#### Granger Causality (Table 7)
| Direction | Aave-Style | Compound V3 |
|-----------|-----------|-------------|
| Util → Liq | p=0.3132 | p=0.6864 |
| Liq → Util | **p=0.0033***** | p=0.5188 |
| Util → Vol | p=0.4431 | p=0.4142 |
| Vol → Util | p=0.8186 | p=0.4305 |
| Liq → Vol | **p=0.0000***** | **p=0.0089***** |
| Vol → Liq | **p=0.0088***** | p=0.5193 |

**Key finding:** Aave-style has significant bidirectional Liq↔Vol feedback AND Liq→Util. Compound V3 only has Liq→Vol. The absorb mechanism dampens the feedback loop.

#### IRF Summary (Table 8)
| Mechanism | Path | Cumulative | Sig Horizons |
|-----------|------|-----------|-------------|
| Aave-Style | Liq → Vol | **-1.39998** | **19/21** |
| Compound V3 | Liq → Vol | -0.21496 | 0/21 |
| Aave-Style | Vol → Liq | 0.01288 | 1/21 |
| Compound V3 | Vol → Liq | 0.00490 | 0/21 |
| Aave-Style | Liq → Util | 0.39468 | 0/21 |
| Compound V3 | Liq → Util | 0.09588 | 0/21 |
| Aave-Style | Util → Liq | 0.01559 | 0/21 |
| Compound V3 | Util → Liq | -0.00610 | 0/21 |
| Aave-Style | Util → Vol | 0.00226 | 0/21 |
| Compound V3 | Util → Vol | -0.01157 | 19/21 |
| Aave-Style | Vol → Util | -0.00016 | 16/21 |
| Compound V3 | Vol → Util | -0.00067 | 0/21 |

**Key finding:** Aave-style Liq→Vol cumulative is 6.5x larger than Compound V3 (-1.40 vs -0.21). Aave-style shows significant spillovers at 19/21 horizons; Compound V3 shows 0/21.

---

### Test D: Chain Comparison — Ethereum L1 vs Base L2 (Section 20)
**Ordering:** Util → Liq → Vol
**Subsamples:**
- Ethereum (L1): 7 CSUs — all *_ethereum and sparklend_ethereum
- Base (L2): 5 CSUs — all *_base and moonwell_lending_base

#### Summary Statistics (Table 9)
| Chain | N | Obs | Util Mean | Vol Mean | Liq/Day Mean | % Days w/ Liq | Avg Coll USD |
|-------|---|-----|-----------|----------|-------------|--------------|-------------|
| Ethereum (L1) | 7 | 1,815 | 0.3350 | 0.0214 | 3.5 | 25.1% | $1,606,790 |
| Base (L2) | 5 | 1,459 | 0.4218 | 0.0237 | 4.6 | 22.0% | $28,994 |

#### Granger Causality (Table 10)
| Direction | Ethereum (L1) | Base (L2) |
|-----------|--------------|-----------|
| Util → Liq | p=0.7917 | p=0.5918 |
| Liq → Util | **p=0.0724*** | p=0.8326 |
| Util → Vol | p=0.9524 | p=0.6890 |
| Vol → Util | p=0.3649 | p=0.7902 |
| Liq → Vol | **p=0.0000***** | **p=0.0002***** |
| Vol → Liq | **p=0.0203**** | p=0.1645 |

**Key finding:** Both chains show highly significant Liq→Vol. Ethereum additionally has Vol→Liq (p=0.02) and marginal Liq→Util (p=0.07). Base shows no significant reverse channels.

#### IRF Summary (Table 11)
| Chain | Path | Cumulative | Peak | Peak Period | Sig Horizons |
|-------|------|-----------|------|-------------|-------------|
| Ethereum (L1) | Liq → Vol | **-0.97353** | -0.08016 | t+2 | **20/21** |
| Base (L2) | Liq → Vol | -0.37670 | 0.04253 | t+1 | 0/21 |
| Ethereum (L1) | Vol → Liq | 0.00872 | 0.00072 | t+2 | 0/21 |
| Base (L2) | Vol → Liq | 0.00907 | 0.00074 | t+3 | 1/21 |
| Ethereum (L1) | Liq → Util | 0.13295 | 0.07200 | t+0 | 0/21 |
| Base (L2) | Liq → Util | 0.20007 | -0.04591 | t+0 | 0/21 |
| Ethereum (L1) | Util → Vol | -0.01065 | -0.00065 | t+10 | 0/21 |
| Base (L2) | Util → Vol | 0.00470 | 0.00044 | t+1 | 0/21 |

**Key finding:** Ethereum Liq→Vol is 2.6x larger than Base (-0.97 vs -0.38) and significant at 20/21 horizons. Ethereum's deeper liquidity and larger collateral positions ($1.6M vs $29K avg) amplify liquidation spillovers.

---

## 4. Cross-Cutting Findings

### Consistently Significant Channels
1. **Liq → Vol** — Significant in every test, every subsample. Liquidations Granger-cause volatility universally.
2. **Vol → Liq** — Significant for Full Sample, Ethereum, Pooled, and Aave-Style. The reverse channel (volatility triggering liquidations) operates in deeper, pooled markets.
3. **Liq → Util** — Significant for Pooled and Aave-Style. Liquidation-driven deleveraging is concentrated in shared-pool protocols.

### Consistently Insignificant Channels
1. **Util → Liq** — Never significant. Utilization does not Granger-cause liquidations in any subsample.
2. **Util → Vol** — Mostly insignificant (one exception: Isolated subsample has 19/21 sig horizons in IRF but non-significant Granger test).
3. **Vol → Util** — Mostly insignificant (one exception: Pooled has 16/21 sig horizons).

### Architecture Effect
- Pooled (Aave-style) protocols amplify the feedback loop: Liq→Vol cumulative is 8x larger than Isolated (-1.10 vs -0.14)
- The absorb mechanism (Compound V3) dampens spillovers: Liq→Vol is 6.5x smaller than instant liquidation

### Chain Effect
- Ethereum (L1) has 2.6x larger Liq→Vol spillovers than Base (L2)
- Base has higher utilization (0.42 vs 0.34) but 55x smaller avg collateral per liquidation ($29K vs $1.6M)

---

## 5. File Index

### Tables (CSV)
| File | Description |
|------|-------------|
| `table1_panel_summary_stats.csv` | Summary stats by subsample (Full, Base, Eth, Pooled, Isolated) |
| `table2_granger_causality_baseline.csv` | Granger causality, baseline ordering (Util→Vol→Liq) |
| `table3_irf_summary_baseline.csv` | IRF cumulative/peak/sig, baseline ordering |
| `table4_architecture_comparison.csv` | Pooled vs Isolated: GC p-values + cumulative IRFs |
| `table5_robustness_ordering.csv` | Baseline vs alternative Cholesky ordering comparison |
| `table6_mechanism_summary_stats.csv` | Summary stats: Aave-Style vs Compound V3 |
| `table7_mechanism_granger_causality.csv` | Granger causality by mechanism |
| `table8_mechanism_irf_summary.csv` | IRF summary by mechanism |
| `table9_chain_summary_stats.csv` | Summary stats: Ethereum vs Base |
| `table10_chain_granger_causality.csv` | Granger causality by chain |
| `table11_chain_irf_summary.csv` | IRF summary by chain |
| `mechanism_irf_point_estimates.csv` | Full IRF paths (all horizons, CIs) by mechanism |
| `chain_irf_point_estimates.csv` | Full IRF paths (all horizons, CIs) by chain |
| `pvar_summary.csv` | Legacy 2-variable PVAR summary |

### Figures (PNG)
| File | Description |
|------|-------------|
| `irf_3var_full_grid.png` | 3×3 IRF grid, Full Sample |
| `irf_3var_cross_comparison.png` | 6 cross-variable IRFs across all 5 subsamples |
| `irf_3var_base_vs_eth.png` | Base vs Ethereum key IRFs (baseline ordering) |
| `irf_3var_pooled_vs_isolated.png` | Pooled vs Isolated architecture IRFs |
| `irf_3var_ordering_robustness.png` | Baseline vs alternative Cholesky ordering |
| `irf_3var_mechanism_comparison.png` | Aave-Style vs Compound V3 IRFs |
| `irf_3var_chain_comparison.png` | Ethereum (L1) vs Base (L2) IRFs |

### Notebook
| File | Description |
|------|-------------|
| `notebooks/pvar_3var_analysis.ipynb` | Source notebook (not executed) |
| `notebooks/pvar_3var_analysis_executed.ipynb` | Executed notebook with all outputs |
