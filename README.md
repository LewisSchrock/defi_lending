# DeFi Liquidations — Heterogeneous Panel SVAR Analysis

Replication package for Lewis Schrock's senior thesis, Williams College, May 2026.

The compiled paper is at [paper/main.pdf](paper/Schrock_Thesis.pdf).

## Research question

Does leveraged borrowing in DeFi lending protocols create a feedback loop in
which cascading liquidations amplify the volatility of the collateral assets
that triggered them?

## Methodology

Pedroni (2013) heterogeneous panel SVAR. The first stage estimates a separate
bivariate VAR for each cross-sectional unit (CSU = protocol × chain × asset)
in collateral basket return and liquidation volume. Long-run (Blanchard–Quah)
restrictions decompose shocks into a "cascade" shock (permanent price effect)
and a "mechanical" shock (transitory). The Pedroni Lambda matrix then splits
each member's response into common, composite, and idiosyncratic components.
A second stage cross-sectional regression of member responses on protocol
characteristics (TVL depth, stablecoin debt share, systematic share) tests
which design parameters predict cascade amplification.

## Repository layout

```
defi_lending/
├── paper/main.pdf                Final compiled thesis
├── README.md                     This file
├── .env.example                  Required environment variables
├── requirements.txt              Python dependencies
│
├── adapters/                     Protocol-specific data adapters
│   ├── liquidations/             Aave V3, Compound V2/V3, Cap, Venus, Lista, Gearbox, Fluid
│   ├── tvl/                      Same set + Aave V2, Euler V2, Morpho, LayerBank
│   └── prices/                   DefiLlama, CoinGecko, Chainlink price service
│
├── config/
│   ├── rpc_pool_v2.py            Multi-provider RPC failover pool (used by collectors)
│   ├── rpc_config.py             Single-key RPC URL builder (used by adapters)
│   ├── prices/chainlink_feeds.yaml   Chainlink feed registry
│   └── units.csv                 Token-decimal table
│
├── code/
│   ├── config/
│   │   ├── csu_config.yaml       Single source of truth for the 45-CSU universe
│   │   └── deployment_dates.yaml Earliest scan dates per protocol-chain
│   └── pedroni_svar/
│       ├── SVAR.py               Per-member VAR + structural identification
│       ├── panelSVAR.py          Pedroni Lambda decomposition
│       ├── identification.py     Cholesky / Blanchard-Quah utilities
│       ├── plotting.py           IRF + FEVD plotting helpers
│       └── run_bivariate_bq.py   Standalone alternate bivariate BQ run (not used for paper figures)
│
├── notebooks/
│   ├── svar_nb.py                Shared Panel SVAR utilities (panelSVAR wrapper, plotting)
│   └── bivariate_return_liq.ipynb  Section 4 — canonical bivariate BQ panel SVAR notebook
│
├── scripts/                      Pipeline (see "Run order" below)
│   ├── collect_liquidations_unified.py
│   ├── collect_tvl_parallel.py
│   ├── build_block_cache.py
│   ├── parse_raw_liquidations.py
│   ├── build_silver_liquidations.py
│   ├── build_silver_tvl.py
│   ├── enrich_tvl_oracle_prices.py
│   ├── build_gold_panel_all_chains.py
│   ├── build_collateral_composition.py
│   ├── build_volatility_panel.py
│   ├── prepare_panel_svar_data.py
│   ├── extract_borrow_supply.py
│   ├── clean_tvl_outliers.py
│   ├── run_unit_root_{cum_liq,total_borrow,tvl,utilization}.py
│   ├── second_stage_inference.py
│   ├── second_stage_tvl.py
│   ├── second_stage_stablecoin_share.py
│   ├── second_stage_systematic_share.py
│   ├── plotting/plot_csu_timeseries.py
│   └── run_full_pipeline.sh      End-to-end driver
│
├── data/
│   ├── gold/
│   │   ├── liquidations/all_chains/
│   │   │   ├── daily_panel.parquet, daily_panel.csv
│   │   │   ├── daily_panel_by_denomination.parquet
│   │   │   └── denomination_classification_reference.csv
│   │   └── collateral_composition/   Per-CSU daily collateral baskets (76 files)
│   └── analysis/
│       ├── collateral_basket.parquet           Vol/util panel
│       ├── panel_svar_data_qualified.parquet   Final SVAR-ready panel
│       ├── tvl_borrow_supply_daily.parquet     Borrow/supply panel
│       └── tvl_borrow_supply_daily_clean.parquet
│
└── results/
    ├── pedroni/bivariate_return_liq/    Section 4 figures (IRFs, FEVD, Lambda)
    └── data_analysis/
        ├── csu_timeseries/              Per-CSU summary timeseries (42 PNGs)
        └── token_prices/token_classification.csv
```

## Setup

Python 3.12 recommended.

```bash
git clone https://github.com/LewisSchrock/defi_lending.git
cd defi_lending
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set DRPC_KEY (required to re-run any on-chain data step)
```

Only `DRPC_KEY` is strictly required. The optional keys in `.env.example`
enable a multi-provider fallback pool that increases throughput during
bulk collection.

## What this package can replicate

The repository ships **derived data** sufficient to reproduce all paper figures
and tables from the SVAR stage onward:

- `data/gold/` — daily liquidation panel + collateral composition (49M)
- `data/analysis/` — SVAR-ready panels (3.4M)
- `results/` — final paper figures (11M)

Raw blockchain data (`data/bronze/`, `data/silver/`, `data/cache/`) is **not**
shipped — these total ~1.7 GB and can be re-collected from RPC using the
collection scripts. A full re-collection takes 1–2 days depending on RPC
provider throughput.

## Run order

### A. From shipped data (fast, minutes)

This is the typical replication path. It reproduces every figure and table
in the paper from the parquets in `data/gold/` and `data/analysis/`.

```bash
# Section 4 — bivariate Blanchard-Quah panel SVAR
jupyter notebook notebooks/bivariate_return_liq.ipynb
# Run all cells. Writes results/pedroni/bivariate_return_liq/{irfs,fevd,lambda}.{png,csv}

# Section 5 — second-stage cross-sectional regressions
python scripts/second_stage_inference.py
python scripts/second_stage_tvl.py                  # depth test (Table 4)
python scripts/second_stage_stablecoin_share.py     # denomination test (Table 5, Figure 5)
python scripts/second_stage_systematic_share.py     # systematic share scatter

# Section 3 — panel unit-root tests (IPS + Maddala-Wu)
python scripts/run_unit_root_tvl.py
python scripts/run_unit_root_total_borrow.py
python scripts/run_unit_root_cum_liq.py
python scripts/run_unit_root_utilization.py

# Summary — per-CSU diagnostic timeseries
python scripts/plotting/plot_csu_timeseries.py
```

### B. From scratch (slow, days)

To regenerate everything from on-chain data:

```bash
# 1. Bronze: collect liquidation events + TVL snapshots from RPC
python scripts/collect_liquidations_unified.py --start-date 2024-07-01 --end-date 2025-12-31
python scripts/collect_tvl_parallel.py
python scripts/build_block_cache.py

# 2. Silver: decode events, enrich with on-chain oracle prices
python scripts/parse_raw_liquidations.py
python scripts/build_silver_liquidations.py
python scripts/build_silver_tvl.py
python scripts/enrich_tvl_oracle_prices.py

# 3. Gold: aggregate to daily panels
python scripts/build_gold_panel_all_chains.py
python scripts/build_collateral_composition.py

# 4. Analysis prep: vol/util panel + qualified SVAR panel
python scripts/build_volatility_panel.py
python scripts/prepare_panel_svar_data.py
python scripts/extract_borrow_supply.py
python scripts/clean_tvl_outliers.py

# 5. SVAR + second-stage as in path A
```

`scripts/run_full_pipeline.sh` runs steps 1–4 sequentially.

## Mapping paper output to source

| Paper element | Source | Output |
|---|---|---|
| §4 IRFs (common) | `notebooks/bivariate_return_liq.ipynb` | `results/pedroni/bivariate_return_liq/irfs_common.png` |
| §4 IRFs (idiosyncratic) | same | `irfs_idiosyncratic.png` |
| §4 FEVD | same | `fevd_common.png`, `fevd_idiosyncratic.png` |
| §4 Median λ table | same | `lambda.csv` |
| §5 Depth test | `scripts/second_stage_tvl.py` | `results/data_analysis/second_stage/second_stage_tvl.csv` |
| §5 Denomination test | `scripts/second_stage_stablecoin_share.py` | `paper/figures/denomination_stable_share.png` (regenerable) |
| §5 Systematic share | `scripts/second_stage_systematic_share.py` | `paper/figures/systematic_share_scatter.png` (regenerable) |
| §3 Stationarity (ADF/IPS) | `scripts/run_unit_root_*.py` | tables embedded in paper |
| Sample composition | manual from `data/analysis/panel_svar_data_qualified.parquet` | Table 1 |
| Per-CSU summary plots | `scripts/plotting/plot_csu_timeseries.py` | `results/data_analysis/csu_timeseries/*.png` |

## Key dataset variables

`data/analysis/panel_svar_data_qualified.parquet`:
- `csu` — cross-sectional unit (e.g. `aave_v3_ethereum`)
- `date` — daily timestamp (UTC)
- `basket_ret` — log return of the collateral basket (weighted by USD value, surviving-token renormalized)
- `vol_14d` — 14-day rolling standard deviation of `basket_ret`
- `log_liq` — log(1 + total collateral USD seized that day)
- `util` — utilization ratio (total borrow USD / total supply USD), clipped to [0, 1]

The qualification rule: a CSU enters the panel if it has ≥ 200 liquidation
events across the sample, clean TVL coverage, and the first-stage SVAR
converges. 28/31 qualified CSUs estimate successfully in the bivariate BQ run.

## Citation

```
@thesis{schrock2026defi,
  author = {Schrock, Lewis},
  title  = {Denomination, Not Depth: Cross-Sectional Cascade Exposure in DeFi Lending},
  school = {Williams College},
  year   = {2026},
}
```

## References

- Pedroni, P. (2013). "Structural Panel VARs." *Econometrics*, 1(2), 180–206.
- Blanchard, O. and D. Quah (1989). "The Dynamic Effects of Aggregate Demand
  and Supply Disturbances." *American Economic Review*, 79(4), 655–673.

## Contact

Lewis Schrock — `lewschrock@gmail.com`
