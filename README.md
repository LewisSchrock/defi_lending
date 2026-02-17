# DeFi Liquidations — Heterogeneous Panel SVAR Analysis

Senior Thesis, Williams College, May 2026

**Last Updated**: February 17, 2026

---

## Research Question

Does leveraged borrowing in DeFi lending protocols create a feedback loop through
cascading liquidations that amplifies collateral asset volatility?

## Methodology

Pedroni (2013) Heterogeneous Panel SVAR — estimates separate VARs per
protocol-chain unit (CSU), then decomposes shocks into common vs. idiosyncratic
components via Lambda matrix.

## Current State

- **Sample**: 31 qualified CSUs across 10 chains, 3 protocol families (Aave, Compound, others)
- **Period**: T=592 days (2024-07-01 to 2026-02-12)
- **Variables**: Volatility, Liquidation, Utilization
- **Identification**: Cholesky ordering vol -> liq -> util (see `context/identification_strategy_feb17.md`)
- **Status**: Identification strategy under revision; re-estimation pending

## Quick Start

```bash
# Rebuild vol/util panel from bronze data
python scripts/build_volatility_panel.py --skip-fetch

# Prepare trivariate SVAR panel
python scripts/prepare_panel_svar_data.py --start-date 2024-07-01

# Run Panel SVAR (via notebook)
jupyter notebook notebooks/pedroni_panel_svar_analysis.ipynb
```

## Project Layout

```
thesis_v2.10/
├── data/
│   ├── bronze/          Raw blockchain data (TVL snapshots, liquidation events, prices)
│   ├── silver/          Cleaned & aggregated (daily TVL, parsed liquidations)
│   ├── gold/            Analysis-ready (daily panels, collateral composition)
│   ├── analysis/        Final datasets + SVAR output
│   │   └── svar_output/ Organized results (panels, IRFs, figures)
│   ├── cache/           Price caches (symbol + oracle)
│   └── reference/       Pool configs, token registries
│
├── scripts/             Data pipeline scripts
│   ├── collect_*.py               Bronze data collection
│   ├── build_silver_tvl.py        Bronze -> Silver TVL
│   ├── build_volatility_panel.py  Bronze -> Vol/Util panel
│   └── prepare_panel_svar_data.py Panel assembly + qualification
│
├── code/pedroni_svar/   Pedroni (2013) implementation (SVAR.py, panelSVAR.py)
├── adapters/            Protocol-specific data adapters (TVL, liquidations, prices)
├── notebooks/           Analysis notebooks
├── context/             Working documents, strategy notes, references (see INDEX.md)
├── presentation/        Slides and presentation materials
└── archive/             Superseded analyses
```

## Documentation

All working documents live in `context/`. See [context/INDEX.md](context/INDEX.md) for what each file covers.

Key docs:
- [context/identification_strategy_feb17.md](context/identification_strategy_feb17.md) — Current identification approach
- [context/data_pipeline.md](context/data_pipeline.md) — Full data pipeline documentation
- [context/data_validity_report.md](context/data_validity_report.md) — Data audit and fixes
- [data/analysis/README.md](data/analysis/README.md) — Variable definitions
- [data/analysis/svar_output/README.md](data/analysis/svar_output/README.md) — Output file index
