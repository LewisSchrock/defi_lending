# Data Validity Report — Thesis v2.9 DeFi Lending Pipeline

**Date:** 2026-02-11
**Scope:** Full audit of on-chain data collection, transformation, and panel construction
**Verdict:** Multiple critical issues found and FIXED. See fix log below.

### Fixes Applied (2026-02-11)

**Round 1 — Critical event/adapter fixes:**

| File | Fix | Severity |
|------|-----|----------|
| `scripts/collect_liquidations_parallel.py` | Fixed 3 wrong event definitions: (1) Compound V2 `LiquidateBorrow` indexed params corrected (was treating `repay_amount_raw` as indexed), (2) Added missing `AbsorbDebt` event for Compound V3, (3) Fixed Fluid `Liquidation` signature from `Liquidate(address,uint256,uint256,address)` to `Liquidation(address,address,address,address,uint256,uint256)` | CRITICAL |
| `scripts/build_silver_tvl.py` | (1) Chain now auto-detected from bronze data instead of hardcoded `'ethereum'`, (2) Native token mapping now chain-aware (BNB for BSC, AVAX for Avalanche, etc.) via `CHAIN_NATIVE_TOKENS` dict | HIGH |
| `code/liquid/adapters/compound.py` | Fixed 5th param from `address cTokenBorrowed` to `uint256 seizeTokens`; fixed topic0 hash computation; fixed normalize() output | CRITICAL |
| `code/liquid/adapters/fluid.py` | Removed duplicate `normalize()` (second was overwriting first with wrong field names `debtAsset`/`collateralAsset`); removed dead code in `fetch_events` | HIGH |
| `code/config/chains.yaml` | Fixed 3 wrong Aave V3 addresses: Polygon (was V2 address), Optimism, Base; added all 11 chains | MEDIUM |
| `code/liquid/runner.py` | Registered all adapter classes (was only Aave V3); generalized DataFrame schema to be protocol-generic | HIGH |

**Round 2 — Silver/Gold layer fixes and validation:**

| File | Fix | Severity |
|------|-----|----------|
| `scripts/build_silver_liquidations.py` | (1) Chainlink price lookup now uses actual chain instead of hardcoded `'ethereum'`, (2) `join_compound_events` now checks both `event_name` and `event_type` field names (parallel collector uses `event_type`), (3) `normalize_event` now handles Fluid field names (`debt_token`/`collateral_token`) and Compound V2 field names (`ctoken_collateral`/`repay_amount_raw`/`seize_tokens_raw`), (4) Join function handles collector field names (`asset`/`collateral_raw` vs `collateral_asset`/`collateral_absorbed_raw`), (5) Added `validate_events` step with sanity checks for duplicates, missing fields, negative amounts, extreme USD values, and collateral/debt ratios | HIGH |
| `scripts/build_silver_tvl.py` | (1) Fixed `skipped_count` NameError when `--force` flag used, (2) Added data validation step with checks for negative values, extreme utilization, suspicious TVL sizes, and net_tvl consistency | MEDIUM |
| `scripts/build_gold_panel_base_eth.py` | (1) Replaced bare `except: continue` with specific exception types (`json.JSONDecodeError, KeyError, TypeError, ValueError`), (2) Added provenance metadata output (`panel_metadata.json`) for reproducibility | LOW |

---

## Executive Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Contract Addresses | 0 | 0 | 1 | 2 |
| Event Signatures / Liquidation Schema | 3 | 1 | 0 | 0 |
| TVL Definition & Aggregation | 1 | 2 | 1 | 2 |
| Price / USD Handling | 0 | 2 | 1 | 1 |
| Pipeline Architecture | 0 | 1 | 1 | 0 |
| **TOTAL** | **4** | **6** | **4** | **5** |

---

## Part 1: Contract Address Validation

### 1.1 Aave V3 PoolAddressesProvider — PASS (with config file inconsistency)

All 11 Aave V3 entries in `code/config/csu_config.yaml` match canonical addresses from the [Aave Address Book](https://github.com/bgd-labs/aave-address-book):

| Chain | Config Address | Status |
|-------|---------------|--------|
| Ethereum | `0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e` | CORRECT |
| Polygon | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` | CORRECT |
| Arbitrum | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` | CORRECT |
| Optimism | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` | CORRECT |
| Base | `0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D` | CORRECT |
| Avalanche | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` | CORRECT |
| BNB Chain | `0xff75B6da14FfbbfD355Daf7a2731456b3562Ba6D` | CORRECT |
| Linea | `0x89502c3731F69DDC95B65753708A07F8Cd0373F4` | CORRECT |
| Scroll | `0x69850D0B276776781C063771b161bd8894BCdD04` | CORRECT |
| xDai/Gnosis | `0x36616cf17557639614c1cdDb356b1B83fc0B2132` | CORRECT |
| Plasma | `0x061D8e131F26512348ee5FA42e2DF1bA9d6505E9` | CORRECT (newer deployment) |

**However, `code/config/chains.yaml` has 3 WRONG addresses:**

| Chain | chains.yaml (WRONG) | Correct (from csu_config.yaml) | Problem |
|-------|---------------------|-------------------------------|---------|
| Polygon | `0xd05e3E715d945B59290df0ae8eF85c1BdB684744` | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` | **This is the Aave V2 address, not V3** |
| Optimism | `0x5343b5a6ec9d8b9b1b66b62a09a57f3bafca1c05` | `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` | Completely wrong address |
| Base | `0x252B36B38B47aFe6B06FfA34a7C37DbffCC9B8F4` | `0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D` | Completely wrong address |

**Impact:** LOW — the production scripts import from `csu_config.yaml`, not `chains.yaml`. But if any code path references `chains.yaml` as a fallback, it will query wrong contracts for Polygon, Optimism, and Base.

### 1.2 Compound V3 Comet Addresses — PASS

All 16 active Compound V3 entries match the official `roots.json` files in the [compound-finance/comet](https://github.com/compound-finance/comet) repository. Every address verified. Two entries correctly commented out as invalid (Polygon USDC.e and USDT — both pointing to an address with no code).

### 1.3 Other Protocols — PASS (with minor notes)

| Protocol | Address | Verified Against | Status |
|----------|---------|-----------------|--------|
| Venus (BSC) | `0xfd36e2c2a6789db23113685031d7f16329158384` | BscScan ("Venus: Distribution") | CORRECT |
| SparkLend | `0x02C3eA4e34C0cBd694D2adFa2c690EECbC1793eE` | Etherscan ("Spark: Pool Addresses Provider") | CORRECT |
| Fluid (Ethereum) | `0xC215485C572365AE87f908ad35233EC2572A3BEC` | Fluid docs (Lending Resolver) | CORRECT |
| Lista (BSC) | `0x8F73b65B4caAf64FBA2aF91cC5D4a2A1318E5D8C` | BscScan ("Lista DAO: Moolah") | CORRECT |
| Benqi (Avalanche) | `0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4` | SnowTrace ("Benqi Finance: Comptroller") | CORRECT |
| Moonwell (Base) | `0xfBb21d0380beE3312B33c4353c8936a0F13EF26C` | BaseScan ("Moonwell: Comptroller") | CORRECT |
| Gearbox | registry `0x9ea7b04d...` + contracts_register `0xa50d4e7d...` | Etherscan | CORRECT (but `registry` key is misleading — it is the AddressProvider, not the ContractsRegister) |

---

## Part 2: Liquidation Event Schema Validation

### 2.1 CRITICAL: `collect_liquidations_parallel.py` — Three Wrong Event Definitions

This is the production parallel collector (`scripts/collect_liquidations_parallel.py`). It has three event definition bugs:

#### Bug 1: Compound V2 `LiquidateBorrow` — Wrong indexed/data param split

**Location:** `scripts/collect_liquidations_parallel.py` ~line 204

The parallel collector treats `repay_amount_raw` as an **indexed** parameter (expecting it in `topics[3]`). But the canonical event:

```solidity
event LiquidateBorrow(address indexed liquidator, address indexed borrower,
    uint repayAmount, address cTokenCollateral, uint seizeTokens);
```

has only TWO indexed params (`liquidator`, `borrower`). `repayAmount` is in the **data** section.

**Impact:** All Compound V2-style liquidation events (Venus, Benqi, Moonwell, Tectonic, Kinetic, Sumer) decoded by the parallel collector will have garbled field values for `repay_amount_raw`, `ctoken_collateral`, and `seize_tokens_raw`.

#### Bug 2: Compound V3 `AbsorbDebt` — Missing entirely

**Location:** `scripts/collect_liquidations_parallel.py` ~line 195

The `LIQUIDATION_EVENTS` list only includes `AbsorbCollateral` for Compound V3. The `AbsorbDebt` event is missing. This means only half of the Compound V3 liquidation data is collected — the collateral side but not the debt side.

The downstream `build_silver_liquidations.py` has a `join_compound_events()` function that expects both event types to pair them by `(tx_hash, borrower)`. Without `AbsorbDebt` events, the join produces incomplete records.

#### Bug 3: Fluid `Liquidate` — Completely wrong signature

**Location:** `scripts/collect_liquidations_parallel.py` ~line 208

The parallel collector defines Fluid's event as:
```
Liquidate(address,uint256,uint256,address)
```

But the actual on-chain event is:
```
Liquidate(address,address,address,address,uint256,uint256)
```

The topic0 hash won't match any on-chain Fluid liquidation events. **Zero Fluid liquidations will be collected.**

### 2.2 CRITICAL: `code/liquid/adapters/compound.py` — Wrong event signature (legacy adapter)

**Location:** `code/liquid/adapters/compound.py` line 46-50

The 5th parameter of `LiquidateBorrow` is defined as `type: "address"` when it should be `type: "uint256"` (`seizeTokens`). The computed topic0 hash `0x086fb6...` will never match the canonical `0x298637...`. This adapter silently returns zero results.

**Impact:** LOW for production (this is the legacy `code/` adapter set, not the production `adapters/` set). But anyone testing with the `code/liquid/` path will get no data.

### 2.3 HIGH: `code/liquid/adapters/fluid.py` — Duplicate normalize method

Two `normalize()` methods defined in the same class. The second (line 76) silently overwrites the first (line 59). The second version:
- References `args.get("debtAsset")` and `args.get("collateralAsset")` but the ABI uses `debtToken` and `collateralToken` → these fields will always be `None`
- Passes a dict to `abi=` parameter instead of a list

### 2.4 Production Adapters — Event Signatures Verified

The root `adapters/liquidations/` files use correct event signatures:

| Adapter | Event | Topic0 | Status |
|---------|-------|--------|--------|
| `aave_v3.py` | `LiquidationCall(address,address,address,uint256,uint256,address,bool)` | `0xe413a321...` | CORRECT |
| `compound_v3.py` | `AbsorbCollateral(...)` + `AbsorbDebt(...)` | Both correct | CORRECT |
| `compound_v2_style.py` | `LiquidateBorrow(address,address,uint256,address,uint256)` | `0x298637f6...` | CORRECT |
| `venus.py` | `LiquidateBorrow(address,address,uint256,address,uint256)` | Correct | CORRECT |
| `fluid.py` | `Liquidate(address,address,address,address,uint256,uint256)` | Correct | CORRECT |
| `lista.py` | `Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)` | `0xa4946ede...` | CORRECT |

**The adapters themselves are correct. The bug is in the parallel collector script that re-defines the events differently.**

---

## Part 3: TVL Definition & Aggregation

### 3.1 CRITICAL: TVL Definition Inconsistency Across Adapters

The pipeline uses **multiple, incompatible TVL definitions** across different adapter families:

| Adapter Type | TVL Definition | Semantic Meaning |
|-------------|---------------|-----------------|
| Aave V3 (aggregator.py) | `aToken.totalSupply()` | Gross deposits (supply) |
| Compound V2-style | `getCash + totalBorrows - totalReserves` | Gross deposits minus reserves |
| Lista (Moolah) | `totalSupplyAssets - totalBorrowAssets` | **Net TVL (supply - borrows)** |
| Fluid | `fToken.totalAssets()` | Gross vault assets |
| Gearbox | `expectedLiquidity()` | Total available + borrowed |
| Cap | `vault.totalAssets()` | ERC-4626 total assets |

**For a panel VAR model, mixing gross supply with net supply creates a definitional inconsistency.** When Aave reports $10B gross supply and Lista reports $500M net TVL, these are not comparable measures.

**DefiLlama uses net TVL (supply - borrows) for lending protocols.** If you want to benchmark against DefiLlama, you need the net figure. Your silver TVL builder (`build_silver_tvl.py`) computes both `total_supply_usd` and `net_tvl_usd` — **use `net_tvl_usd` for consistency.**

### 3.2 HIGH: Legacy Compound Adapter + Central Aggregator = Wrong Values

The legacy `code/tvl/adapters/compound_adapter.py` maps `aToken = cToken address`. When `aggregator.py` calls `get_total_supply(cToken)`, it reads cToken `totalSupply()` (in cToken units, typically 8 decimals) and divides by `10^8`. This gives you the number of cTokens, NOT the underlying deposited value. The actual underlying = `cTokenSupply × exchangeRateStored / scale`. This could be off by orders of magnitude.

**Impact:** MEDIUM — This only affects the legacy `code/tvl/aggregator.py` path. The production `adapters/tvl/compound_v2_style.py` correctly reads `getCash`, `totalBorrows`, `totalReserves`.

### 3.3 HIGH: Two Parallel Pipeline Architectures

There are TWO complete adapter sets:
- **`code/tvl/adapters/` + `code/liquid/adapters/`** — Legacy, OOP-based, used by `code/tvl/aggregator.py`
- **`adapters/tvl/` + `adapters/liquidations/`** — Production, function-based, used by all `scripts/` build pipelines

The production scripts exclusively import from root `adapters/`. The `code/` set is dead code for production purposes but remains in the repo, creating confusion about which is canonical.

---

## Part 4: Price / USD Handling

### 4.1 HIGH: Silver TVL Builder Hardcodes `chain='ethereum'` for All Price Lookups

**Location:** `scripts/build_silver_tvl.py` ~line 377

All Chainlink oracle lookups pass `chain='ethereum'` regardless of the actual CSU chain. This means:
- BSC tokens (Venus, Lista) → searched on Ethereum Chainlink feeds → likely missing → falls through to DefiLlama
- Avalanche tokens (Benqi) → same problem
- Fallback to DefiLlama/CoinGecko should still work, but adds latency and may have timing mismatches

### 4.2 HIGH: Native Token Always Maps to 'ETH'

**Location:** `scripts/build_silver_tvl.py` ~line 66

When a market's underlying is the native token (symbol = `NATIVE`), it's always mapped to `ETH`. This is wrong for:
- Venus on BSC → native is BNB, not ETH
- Benqi on Avalanche → native is AVAX, not ETH
- Kinetic on Flare → native is FLR, not ETH

**Impact:** Native-token TVL for non-Ethereum chains will be priced at ETH's price instead of the correct native token price.

### 4.3 MEDIUM: Compound V3 USD Value Scaling May Be Wrong

**Location:** `scripts/build_silver_liquidations.py` ~line 534

The silver builder divides Compound V3 `usdValue` by `1e8`. But the Compound V3 Comet contract emits `usdValue` in base units scaled by the base token's decimals (typically 1e6 for USDC or 1e18 for WETH). The correct scaling depends on the specific market's base token. Using a flat `1e8` divisor may produce values that are off by 1e2 (for USDC base: 1e6 vs 1e8) or 1e10 (for WETH base: 1e18 vs 1e8).

### 4.4 LOW: 34-Hour Price Tolerance

The `asof_fill()` function in the price cache accepts prices up to 34 hours old. For volatile assets during market crashes (exactly when liquidation data matters most), stale prices could introduce significant measurement error.

---

## Part 5: Pipeline Architecture Issues

### 5.1 HIGH: `code/liquid/runner.py` Only Registers Aave V3

Only `("aave","v3")` is in the `ADAPTER_REGISTRY`. All other protocol liquidation adapters are implemented but not wired into the runner. The runner's output DataFrame schema is Aave-specific (`receive_a_token`, `usd_value` columns), which won't align with other protocols.

**Impact:** LOW for production (production uses `collect_liquidations_parallel.py`, not the runner). But the runner is non-functional for any protocol except Aave V3.

### 5.2 MEDIUM: No Block Number in TVL Output

The silver/gold TVL output records `date` but not `block_number`. Since different runs on the same day could hit different blocks, results are not perfectly reproducible. The bronze layer DOES record the block number — this should propagate through to silver and gold.

---

## Part 6: Cross-Reference with External Data Sources

### 6.1 DefiLlama TVL Comparison (February 2026 approximate values)

| Protocol | DefiLlama TVL (net) | Order of Magnitude |
|----------|--------------------|--------------------|
| Aave V3 | ~$34.3B | Tens of billions |
| SparkLend | ~$2.5B | Low billions |
| Compound V3 | ~$1.3B | Low billions |
| Fluid | ~$1.3B | Low billions |
| Venus | ~$1.2B | Low billions |
| Lista Lending | ~$725M | Hundreds of millions |
| Gearbox | ~$400M+ | Hundreds of millions |
| Benqi | ~$353M | Hundreds of millions |
| Moonwell | ~$234M+ | Hundreds of millions |

**Remember:** DefiLlama reports **net TVL (supply - borrows)**. Your pipeline's `total_tvl` in `aggregator.py` sums **gross supply**. Use `net_tvl_usd` from `build_silver_tvl.py` for comparable numbers.

### 6.2 Aave Liquidation Event Verification

The `LiquidationCall` event signature matches:
- Official Aave V3 Pool contract source code
- Aave Protocol Subgraphs on TheGraph
- Major Dune Analytics dashboards (dcooper, KARTOD, chaininsight)
- Academic literature (arXiv:2512.11363)

### 6.3 Compound V3 Liquidation Event Verification

The `AbsorbCollateral` + `AbsorbDebt` events match:
- Official `CometMainInterface.sol` on GitHub
- Compound V3 documentation on `docs.compound.finance/liquidation/`
- Note: V3 uses a two-step process (absorb → buyCollateral). The pipeline correctly captures `absorb` (the actual liquidation) and ignores `buyCollateral` (the subsequent market-making operation).

---

## Prioritized Fix List

### Must Fix Before Any Analysis

1. **Fix `collect_liquidations_parallel.py` event definitions** — Three wrong event schemas causing garbled or missing liquidation data for Compound V2-style, Compound V3, and Fluid protocols
2. **Fix native token mapping in `build_silver_tvl.py`** — Map to correct native token per chain (BNB for BSC, AVAX for Avalanche, etc.)
3. **Fix chain parameter in `build_silver_tvl.py`** — Pass actual chain to Chainlink lookups instead of hardcoding 'ethereum'
4. **Standardize TVL definition across panel** — Decide on gross vs net TVL and apply consistently. Recommend: use `net_tvl_usd` from silver layer to match DefiLlama methodology.

### Should Fix Before Publication

5. **Verify Compound V3 `usdValue` scaling** — Check actual on-chain values against expected magnitude
6. **Propagate block numbers through silver/gold layers** — For reproducibility
7. **Fix or remove `chains.yaml`** — Three wrong addresses (V2 Polygon, wrong Optimism, wrong Base)
8. **Clean up dead code** — Legacy `code/` adapter set is unused in production
9. **Verify Fluid resolver addresses** — Could not find these specific addresses in public documentation

### Nice to Have

10. **Reduce 34-hour price tolerance** — Or flag stale prices in output
11. **Add `n_priced_assets` to summary** — Current `n_assets` counts unpriced rows
12. **Standardize config key naming** — `registry` vs `unitroller` vs `comptroller` vs `pool_addresses_provider`
