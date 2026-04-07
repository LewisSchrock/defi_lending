# context/ — Working Documents Index

All project documentation and working notes live here. Data-level READMEs stay
with their data (in `data/`). This folder is for everything else.

---

## Root

| File | What it is |
|------|-----------|
| `stablecoin_denomination_finding.md` | **Core thesis finding.** Stablecoin denomination of DeFi loans is the mechanism that determines whether liquidation is systemic or idiosyncratic. Includes mechanism, empirical evidence (Lambda + LP + horse race), theoretical positioning, implications, literature gap, and proposed thesis architecture. |
| `codebase_improvements.md` | Running list of non-urgent code quality improvements (eliminate dual adapter architecture, etc.). |

---

## theory/

| File | What it is |
|------|-----------|
| `theory_explainer.tex` / `.pdf` | **Pedagogical guide.** Walks through Geanakoplos Leverage Cycle theory step-by-step, adapted for DeFi. Aimed at undergrad econ level with numerical examples. |
| `theory_chapter.tex` / `.pdf` | **Formal thesis chapter.** Concise presentation with definitions, propositions, and theorems. 6 pages. |
| `lambda-robustness.tex` / `.pdf` | Lambda robustness checks and analysis. |
| `lambda_implementation_discrepancy.md` | Documentation of np.cov vs np.corrcoef fix in Lambda computation. |

## identification/

| File | What it is |
|------|-----------|
| `identification_strategy_feb17.md` | Identification approach. Reversed Cholesky (vol -> liq -> util). Lambda is robust to ordering choice. |
| `identification_strategy_v2.md` | Extended identification discussion. Cascade vs mechanical partition under reversed Cholesky. |
| `identification_pedroni_response_feb22.md` | Analysis of Pedroni's "interesting subset" insight on zero restrictions. Cascade vs mechanical partition. |
| `identification_brainstorm_feb17.pdf` | Feb 17 identification brainstorm notes (PDF). |

## data_docs/

| File | What it is |
|------|-----------|
| `data_pipeline.md` | Full pipeline documentation. Liquidation path: Bronze -> Silver -> Gold -> Analysis. Utilization + volatility path: Bronze -> Analysis (direct). |
| `data_methodology_section.md` | **Academic rewrite** of the data pipeline doc as a formal methodology section (Sections 3.1–3.7) with LaTeX equations. For thesis chapter / paperbanna diagramming. |
| `data_validity_report.md` | Feb 11 audit of the entire data pipeline. Documents critical bugs found and fixed. |
| `tvl_adapter_success_criteria.md` | Technical spec for what a TVL adapter must produce to survive the full pipeline. |
| `drpc_optimization_guide.md` | RPC concurrency and rate limit optimization for on-chain data collection. |
| `dune_validation_guide.md` | Guide for validating data against Dune Analytics. |
| `feb16_empirical_positioning.md` | How our sample (30+ CSUs, 10 chains) compares to existing DeFi literature. |
| `panel_dimensions_feb22.md` | Unbalanced panel design, per-CSU effective range, degenerate liquidation series problem, min 200 obs threshold. |
| `block_level_feasibility.md` | Assessment of moving from daily to block-level or hourly data. Conclusion: daily is best fit for Pedroni framework. |

## progress/

| File | What it is |
|------|-----------|
| `progress_feb23.md` | **Feb 23 session progress.** Built LP framework, three-way denomination comparison, within-CSU horse race LP. |
| `pedroni_update_feb24.md` | **Draft email to Pedroni.** Identification wall, bivariate SVAR + LP strategy, stablecoin denomination finding. |
| `csu_expansion_feb25.md` | Feb 25 CSU expansion notes. |
| `2026-03-01_contract_address_filtering.md` | **Mar 1 fix.** Contract-address filtering to disambiguate protocols sharing identical LiquidationCall topic0 signatures. |
| `csu_coordination_mar01.md` | **Mar 1 CSU status tracker.** Categories: READY (~31), ACTIVELY COLLECTING, NEEDS RESTART, INCOMPLETE TVL, BROKEN. |
| `claude_analysis_feb16.md` | Working notes from Feb 16 analysis session. Initial trivariate SVAR results. |
| `organization_summary_feb16.md` | One-time log of the Feb 16 folder reorganization. Historical record only. |

## downloads/

| File | What it is |
|------|-----------|
| `geanakoplos-2010-leverage-cycle.pdf` | Geanakoplos (2010) "Solving the Present Crisis and Managing the Leverage Cycle" (NY Fed version). |
| `chiu-2023-fragility-defi-lending.pdf` | Chiu et al. (2023) "On the Fragility of DeFi Lending" (Bank of Canada). |
| `2009-not-all-oil-price-shocks-are-alike-...pdf` | Kilian (2009) oil price shocks paper. |
| `Thesis deadlines and contact info 2025_26-apr25.pdf` | Thesis deadlines reference. |

## 471_reference/

**Primary source material for Pedroni (2013) Heterogeneous Panel SVAR methodology.** These are the foundational papers and course materials from Peter Pedroni's Econ 471 at Williams College. Essential reading for understanding the methodology this thesis implements.

| File | What it is |
|------|-----------|
| `pedroni(2013).pdf` | **Foundational paper.** "Structural Panel VARs" (Econometrics, 2013). Defines the DGP with common factor decomposition (Eq 1: epsilon_it = Lambda_i * epsilon_bar_t + epsilon_tilde_it). Three identification schemes: A(0) short-run (Eq 5), B(0) timing/information (Eq 6), A(1) long-run Blanchard-Quah (Eq 7). 5-step estimation algorithm (p.188): compute time effects, estimate reduced-form VARs, apply identifying restrictions, compute Lambda_i as correlations, compute member-specific IRFs. Monte Carlo simulations show panel fitted values outperform individual time series even at T=12, N=10. Optimal comparative advantage at T=100, N=20. |
| `Econ471-FullVersion-LecturePacket.pdf` | **Pedroni's lecture notes** for Econ 471 (Feb 2020). Sections I–VI: panel concepts (micro vs macro panels), long-run analysis (panel unit root/cointegration), cross-sectional dependence, nonlinear analysis, structural panel VARs. Key content: Pesaran-Smith (1995) critique — pooled dynamic panels with heterogeneous dynamics yield rho_hat → 1, beta_hat → 0 regardless of true values; IV/GMM cannot fix this. Macro panels (moderate N, substantial T) require panel time series methods, not micro panel methods (FE, GMM). |
| `econ-471-hw1.pdf` | **HW1: Latent heterogeneity consequences.** Demonstrates why pooled OLS with heterogeneous dynamics is inconsistent. Derives the bias analytically. |
| `econ-471-hw2-spring2026.pdf` | **HW2: Understanding heterogeneous panel SVARs.** Implements Blanchard-Quah for a panel of countries. Covers cross-sectional averaging consistency and inference for countries without data. Directly relevant to our panel SVAR implementation. |
| `econ-471-hw3-spring2026.pdf` | **HW3: Empirical panel SVAR applications.** Uses exchange rate data with Pedroni & Hasanov (2025/2026) papers. Practical application of the full estimation algorithm. |

## homework/

| File | What it is |
|------|-----------|
| `econ-471-hw1.tex` / `.pdf` | Econ 471 homework 1. Not thesis-related. |

---

## Other READMEs (outside context/)

| Location | What it covers |
|----------|---------------|
| `README.md` (root) | Project overview, quick start, layout |
| `data/analysis/README.md` | Economic definitions of the three SVAR variables + coverage stats (43 CSUs vol/util, 31 qualified SVAR) |
| `data/analysis/svar_output/README.md` | Index of SVAR output files (panels, results, figures) |
| `data/gold/collateral_composition/ethereum/README.md` | Ethereum collateral composition data dictionary |
| `data/gold/liquidations/ethereum/README.md` | Ethereum liquidation panel data dictionary (stale — 6 CSUs, needs update) |
| `archive/README.md` | Why files in archive/ are archived |
| `presentation/winter_study/LITERATURE_REFERENCE_GUIDE.md` | Comprehensive literature reference guide (Kiyotaki & Moore through DeFi papers) |

---

## Convention

- All files in `context/` use `lowercase_with_underscores.md`
- Date-stamped files use `topic_monthday.md` format (e.g., `identification_strategy_feb17.md`)
- New working documents go here, not at project root
- Data dictionaries stay with their data in `data/`
