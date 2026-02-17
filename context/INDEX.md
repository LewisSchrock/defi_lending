# context/ — Working Documents Index

All project documentation and working notes live here. Data-level READMEs stay
with their data (in `data/`). This folder is for everything else.

---

## Active Strategy

| File | What it is |
|------|-----------|
| `identification_strategy_feb17.md` | **Current identification approach.** Reversed Cholesky (vol -> liq -> util) as primary, Blanchard-Quah with log price level as complementary. Includes defense of zero restrictions, I(1) transformation analysis, and implementation plan. |

## Research Context

| File | What it is |
|------|-----------|
| `feb16_empirical_positioning.md` | How our sample (30+ CSUs, 10 chains) compares to existing DeFi literature (Lehar & Parlour, Heimbach & Huang, etc.). Shows we have the largest cross-sectional panel in the literature. |
| `claude_analysis_feb16.md` | Working notes from Feb 16 analysis session. Includes initial trivariate SVAR results and protocol-level heterogeneity findings. |
| `block_level_feasibility.md` | Assessment of moving from daily to block-level or hourly data. Conclusion: daily is best fit for Pedroni framework; block-level infeasible; hourly possible as robustness. |

## Data & Pipeline

| File | What it is |
|------|-----------|
| `data_pipeline.md` | Full Bronze -> Silver -> Gold -> Analysis pipeline documentation. Traces all on-chain data from blockchain sources through each transformation. |
| `data_validity_report.md` | Feb 11 audit of the entire data pipeline. Documents critical bugs found and fixed (wrong event signatures, chain detection, etc.). |
| `tvl_adapter_success_criteria.md` | Technical spec for what a TVL adapter must produce to survive the full pipeline (bronze -> silver -> gold -> qualified panel -> SVAR). |
| `drpc_optimization_guide.md` | RPC concurrency and rate limit optimization for on-chain data collection. |

## Codebase

| File | What it is |
|------|-----------|
| `codebase_improvements.md` | Running list of non-urgent code quality improvements (eliminate dual adapter architecture, etc.). |

## Meta (can be deleted)

| File | What it is |
|------|-----------|
| `organization_summary_feb16.md` | One-time log of the Feb 16 folder reorganization. Historical record only. |

---

## Other READMEs (outside context/)

| Location | What it covers |
|----------|---------------|
| `README.md` (root) | Project overview, quick start, layout |
| `data/analysis/README.md` | Economic definitions of the three SVAR variables |
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
