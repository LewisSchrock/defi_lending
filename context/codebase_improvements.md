# Codebase Improvement Suggestions — Running Doc

**Purpose:** Track opportunities to make the codebase more concise, readable, and maintainable. These are NOT urgent fixes — they are improvements to implement later.

**Last Updated:** 2026-02-11

---

## 1. Eliminate Dual Adapter Architecture

**Current state:** Two complete adapter sets exist:
- `code/tvl/adapters/` + `code/liquid/adapters/` — 35+ files, OOP-based, legacy
- `adapters/tvl/` + `adapters/liquidations/` — 16+ files, function-based, production

**Recommendation:** Delete the entire `code/tvl/adapters/`, `code/liquid/adapters/`, and `code/tvl/aggregator.py` tree. All production scripts use root `adapters/`. The legacy code creates confusion about which is canonical and has known bugs (wrong Compound V2 event signature, broken Fluid normalize, etc.).

**Lines of code removed:** ~3,000+

---

## 2. Consolidate Config Key Naming

**Current state:** Different protocols use different config keys for the same concept:
- Aave: `registry` (= PoolAddressesProvider)
- Compound V3: `registry` (= Comet proxy)
- Venus: `registry` (= Comptroller)
- Gearbox: `registry` (= AddressProvider) + `contracts_register` (= ContractsRegister)
- Kinetic: `unitroller` (= Comptroller)
- Sumer: `comptroller` + `registry` (both = Comptroller, redundant)
- Tydro: `pool_addresses_provider` + `data_provider` + `pool`
- Cap: `registry` (unused by adapter)

**Recommendation:** Adopt a consistent naming convention:
```yaml
# For all protocols:
entry_point: "0x..."        # The main contract the adapter needs
entry_point_type: "comptroller" | "pool_addresses_provider" | "comet" | "resolver" | ...
# Optional additional addresses:
auxiliary:
  contracts_register: "0x..."
  data_provider: "0x..."
```

---

## 3. Unify Adapter Return Schema

**Current state:** Each adapter returns a different dict schema:
- Aave V3: `{supplied_raw, stable_debt_raw, variable_debt_raw, ...}`
- Compound V2-style: `{tvl_underlying_raw, get_cash_raw, total_borrows_raw, total_reserves_raw, ...}`
- Compound V3: `{supplied_raw, borrowed_raw, ...}`
- Fluid: `{total_assets, total_supply, ...}`
- Lista: `{total_supply_assets, total_borrow_assets, total_supply_shares, ...}`

The silver builder `build_silver_tvl.py` has separate extraction functions (`get_supply_raw()`, `get_borrow_raw()`) with protocol-specific branching.

**Recommendation:** Define a standard output dataclass:
```python
@dataclass
class MarketSnapshot:
    symbol: str
    token_address: str
    decimals: int
    supply_raw: int       # Total deposits in base units
    borrow_raw: int       # Total borrows in base units
    reserves_raw: int     # Protocol reserves in base units (0 if N/A)
    # Optional protocol-specific fields in an extras dict
    extras: dict = field(default_factory=dict)
```

Every adapter returns `list[MarketSnapshot]`. The silver builder becomes trivially simple.

---

## 4. Centralize Event Definitions

**Current state:** Liquidation event signatures and ABIs are defined in THREE places:
1. Root `adapters/liquidations/*.py` — correct definitions
2. `code/liquid/adapters/*.py` — some incorrect (compound.py, fluid.py)
3. `scripts/collect_liquidations_parallel.py` — re-defines events inline with bugs

**Recommendation:** Create `adapters/events.py` with a single source of truth:
```python
EVENTS = {
    "aave_v3_liquidation": {
        "signature": "LiquidationCall(address,address,address,uint256,uint256,address,bool)",
        "topic0": "0xe413a321...",
        "indexed": ["collateralAsset", "debtAsset", "user"],
        "data": ["debtToCover", "liquidatedCollateralAmount", "liquidator", "receiveAToken"],
    },
    "compound_v2_liquidation": { ... },
    "compound_v3_absorb_collateral": { ... },
    "compound_v3_absorb_debt": { ... },
    "fluid_liquidation": { ... },
    "lista_liquidation": { ... },
}
```

Both `collect_liquidations_parallel.py` and individual adapters import from this single source.

---

## 5. Extract Chain Constants

**Current state:** Chain-specific constants are scattered:
- Native token symbols hardcoded per-adapter (ETH, BNB, AVAX, FLR, etc.)
- RPC URLs in `config/rpc_config.py`
- Block times assumed implicitly
- Chainlink feed addresses in `config/prices/chainlink_feeds.yaml`

**Recommendation:** Single `chains.py` or `chains.yaml`:
```yaml
chains:
  ethereum:
    native_symbol: ETH
    native_decimals: 18
    wrapped_native: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    block_time_sec: 12
    chainlink_eth_usd: "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
  binance:
    native_symbol: BNB
    native_decimals: 18
    wrapped_native: "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
    block_time_sec: 3
    chainlink_bnb_usd: "0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE"
  # ...
```

---

## 6. Replace Bare `except` Blocks — PARTIALLY DONE

**Current state:** Several scripts use bare `except: continue` or `except Exception:` that swallow errors silently.

**Status:** Fixed `build_gold_panel_base_eth.py` bare except (now catches `json.JSONDecodeError, KeyError, TypeError, ValueError`). Remaining broad exception handlers in adapter files and price lookup code should still be narrowed.

**Recommendation:** Continue narrowing exception types across remaining files.

---

## 7. Add Type Hints to Adapter Functions

**Current state:** Most adapter functions lack type hints. Input/output types are only discoverable by reading the code.

**Recommendation:** Add return types at minimum:
```python
def get_aave_v3_tvl(rpc_url: str, registry: str, block: int | None = None) -> list[dict]:
def scan_aave_liquidations(rpc_url: str, pool: str, from_block: int, to_block: int) -> list[dict]:
```

---

## 8. Consolidate Test Scripts

**Current state:** Multiple test scripts with overlapping functionality:
- `scripts/test_all_csus.py`
- `scripts/test_single_csu.py`
- `scripts/test_problematic_csus.py`
- `scripts/test_single_day.py`
- Various `scripts/verify_*.py` and `scripts/check_*.py`

**Recommendation:** Consolidate into `scripts/test_pipeline.py` with subcommands:
```bash
python scripts/test_pipeline.py csu aave_v3_ethereum --tvl --liquidations
python scripts/test_pipeline.py all --quick
python scripts/test_pipeline.py problematic --verbose
```

---

## 9. Move Documentation Status Files Out of Root

**Current state:** Root directory has 5 status/progress markdown files:
- `COLLECTION_READY_STATUS.md`
- `CSU_CONFIG_STATUS.md`
- `DEPLOYMENT_DATES_STATUS.md`
- `RUN_RESULTS.md`
- Plus 19 files in `docs/`

**Recommendation:** Move all status files to `docs/status/`. Keep root clean with just `README.md`.

---

## 10. Add Data Validation Assertions — DONE

**Status:** Implemented. Both silver builders now include validation steps:

- `build_silver_tvl.py`: Checks for negative values, extreme utilization (>150%), suspiciously large TVL (>$100B), zero-market inconsistencies, and net_tvl_usd consistency.
- `build_silver_liquidations.py`: Checks for duplicate events, missing critical fields, negative amounts, extreme USD values (>$1B single liquidation), and suspicious collateral/debt ratios.

---

## 11. Consider a Single Entry Point

**Current state:** 40+ scripts in `scripts/` with no clear execution order.

**Recommendation:** Create a `Makefile` or `pipeline.py` orchestrator:
```makefile
bronze-tvl:
    python scripts/collect_tvl_parallel.py --start-date $(START) --end-date $(END)

bronze-liquidations:
    python scripts/collect_liquidations_parallel.py --chain ethereum --start-date $(START) --end-date $(END)

silver: bronze-tvl bronze-liquidations
    python scripts/build_silver_tvl.py
    python scripts/build_silver_liquidations.py

gold: silver
    python scripts/build_gold_panel_base_eth.py

all: gold
```

---

## Priority Order for Implementation

1. **Eliminate dual adapter architecture** (#1) — Biggest single improvement for clarity
2. **Centralize event definitions** (#4) — Prevents the bugs found in the validity audit
3. **Unify adapter return schema** (#3) — Simplifies silver builder significantly
4. **Extract chain constants** (#5) — Fixes native token and chain-specific pricing bugs
5. **Add data validation assertions** (#10) — Catches errors early
6. Everything else in any order
