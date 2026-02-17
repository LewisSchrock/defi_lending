# TVL Adapter Success Criteria

Empirically derived from the 13 CSUs that successfully pass through the full pipeline:
Bronze TVL → Silver (USD aggregation) → Gold (composition + volatility) → Qualified Panel → SVAR Estimation.

---

## Overview: What a TVL Adapter Must Produce

A TVL adapter is a Python function that, given a Web3 instance, a registry contract address, and a block number, returns a list of market dicts. This data flows through four downstream stages, each with its own requirements. An adapter "succeeds" only if its output survives all four.

```
Adapter Output (bronze JSON)
    ↓
[Stage 1] Silver: aggregate markets → total_supply_usd, total_borrow_usd → utilization
    ↓
[Stage 2] Gold: token weights → basket returns → rolling volatility
    ↓
[Stage 3] Qualification: ≥70% coverage on utilization AND volatility
    ↓
[Stage 4] SVAR: non-degenerate variance in all 3 variables → matrix decomposition
```

---

## 1. Bronze Output Schema (Adapter Return Value)

Each market dict in the returned list MUST contain these fields. The field names vary by protocol architecture, but the downstream parsers (`build_silver_tvl.py`, `build_volatility_panel.py`) use a priority chain to extract each value.

### 1.1 Required Fields

| Concept | Accepted Field Names (priority order) | Type | Notes |
|---------|--------------------------------------|------|-------|
| **Token address** | `underlying`, `underlying_token`, `token_address` | `str` (0x...) | Checksummed. Used for oracle price lookups. |
| **Token symbol** | `underlying_symbol`, `token_symbol`, `symbol`, `asset_symbol` | `str` | Must resolve to a priceable token. `NATIVE` → chain native. |
| **Token decimals** | `underlying_decimals`, `token_decimals`, `decimals` | `int` | Defaults to 18 if missing. Wrong decimals corrupt all USD values. |
| **Supply (raw)** | `supplied_raw`, `tvl_underlying_raw`, `total_assets_raw`, `get_cash_raw` + `total_borrows_raw` | `int` | In token's smallest unit (wei-equivalent). Must be > 0 for at least one market. |
| **Borrow (raw)** | `variable_debt_raw` + `stable_debt_raw`, `borrowed_raw`, `total_borrows_raw`, `total_borrow_raw` | `int` | 0 is valid for collateral-only assets (e.g., Compound V3 collateral). |

### 1.2 Empirical Validation Criteria (from 13 successful CSUs)

**V1.1 — Non-empty market list.** The adapter must return ≥1 market dict. Zero markets → the bronze file is useless.

**V1.2 — At least one market with supply > 0.** Across all 13 successful CSUs, every bronze file has at least 1 market with `supply_raw > 0`. This is the minimum signal that the protocol has capital.

**V1.3 — Symbol is resolvable to a price.** The symbol must either:
- Be in the stablecoin set (USDC, USDT, DAI, etc.) → assumed $1.00
- Map to a DefiLlama token ID via `get_defillama_id(symbol)`
- Have an entry in the protocol oracle cache (`chain:address:date`)

If no market in the snapshot can be priced, the file contributes nothing to silver.

**V1.4 — Decimals are correct.** A wrong `decimals` value silently corrupts all downstream USD values. Validate by checking:
```
human_amount = supply_raw / 10^decimals
```
For known stablecoins (USDC, USDT), human_amount should be in a plausible range (not 1e18 or 1e-18). For ETH/WETH, human_amount × ~$3000 should produce a plausible USD TVL.

**V1.5 — Consistent market count.** Across the time series, market count should be stable (protocols don't gain/lose 50% of their markets overnight). Empirically:
- Aave V3 Ethereum: 11–60 markets (gradual growth as assets are listed)
- Compound V3 ETH USDC: 6–13 markets
- Moonwell Base: 7–20 markets

A sudden drop to 0 or 1 market indicates an adapter bug (wrong ABI, wrong contract, revert not caught).

---

## 2. Silver Layer Requirements (Utilization)

`build_silver_tvl.py` aggregates bronze markets into a single row per CSU-date:

```
total_supply_usd = Σ (supply_raw / 10^decimals) × price
total_borrow_usd = Σ (borrow_raw / 10^decimals) × price
utilization = total_borrow_usd / total_supply_usd
```

### 2.1 Empirical Benchmarks

| Metric | Min (successful CSUs) | Median | Max |
|--------|----------------------|--------|-----|
| `total_supply_usd` | $11.6M (Lodestar) | $387.5M | $25.4B (Aave Eth) |
| Utilization (mean) | 0.133 (Compound V2) | 0.349 | 0.964 (Fluid) |
| Utilization std | 0.022 | 0.044 | 0.162 |
| Days of data | 531 | 731 | 731 |

### 2.2 Validation Criteria

**V2.1 — total_supply_usd > 0.** If supply is zero on every day, utilization is undefined. The CSU cannot produce the first SVAR variable.

**V2.2 — total_supply_usd > total_borrow_usd (general case).** Utilization > 1.0 is clipped to 1.0. One CSU (Fluid) legitimately runs near 1.0 due to its architecture, but persistent utilization > 1.5 indicates a pricing or aggregation error.

**V2.3 — No negative values.** Supply < 0 or borrow < 0 is always a bug.

**V2.4 — No implausible magnitudes.** Supply > $100B for a single CSU is suspect. The largest successful CSU (Aave V3 Ethereum) averages $25B. If a new adapter reports $1T, the decimals are probably wrong.

**V2.5 — Day-over-day supply stability.** Empirically, >50% single-day supply change occurs on <1.1% of days. A new adapter should not show supply dropping by 90% and recovering the next day — that indicates intermittent contract call failures producing partial data.

**V2.6 — Utilization has non-degenerate variance.** `utilization.std() > 0.001`. The one SVAR failure from a utilization problem (Gearbox) had `util_std = 0.000000`. If the adapter always returns the same supply and borrow, there's no signal for the VAR to estimate.

---

## 3. Gold Layer Requirements (Volatility)

`build_volatility_panel.py` and `prepare_panel_svar_data.py` compute:

```
For each CSU-date:
  1. Token weights: w[token] = (supply_raw / 10^dec × price) / total_supply_usd
  2. Basket return: R_t = Σ w[token,t-1] × log(price[token,t] / price[token,t-1])
  3. Volatility: σ_t = rolling_std(R_t, window=14)
```

### 3.1 Empirical Benchmarks (Successful CSUs)

| Metric | Min | Median | Max |
|--------|-----|--------|-----|
| Volatility mean | 0.000005 (Aave Optimism) | 0.013493 | 0.032324 (Comp V3 WETH) |
| Volatility std | 0.000014 | 0.006641 | 0.016710 |
| Unique vol values | 221 | 696 | 724 |
| Non-zero vol days | 295/705 | 696/697 | 724/724 |

### 3.2 Why Volatility Goes to Zero (the Critical Failure Mode)

8 of 22 qualified CSUs fail SVAR because volatility = 0.0 on every observation. Root cause analysis:

| Pattern | CSUs Affected | Mechanism |
|---------|--------------|-----------|
| **100% stablecoin collateral** | compound_v3_arb_usdc, compound_v3_arb_usdc_e, compound_v3_base_usdc | Compound V3 markets backed only by USDC/USDT → basket return = 0 every day |
| **No price data for non-stablecoin tokens** | aave_v3_bsc, aave_v3_polygon, compound_v2_polygon | Have non-stablecoin tokens in collateral but price lookup fails → basket computed only from stablecoins → zero |
| **Single-asset market** | fluid_lending_arbitrum | Only one underlying token → no diversification to measure |

### 3.3 Validation Criteria

**V3.1 — At least 2 priceable non-stablecoin tokens in the collateral basket.** This is necessary (not sufficient) for non-zero volatility. The basket return is a weighted sum of log-returns. Stablecoins contribute ≈0. If the entire basket is stablecoins, volatility is mechanically zero regardless of adapter quality.

**V3.2 — Weight coverage ≥ 30% on non-stablecoin tokens.** The basket return calculation requires `total_weight > 0.3` (from `build_volatility_panel.py:393`). If 70%+ of collateral is stablecoins that get skipped from return calculation, the basket return may still be computed but will be dominated by noise.

**V3.3 — Volatility std > 0.00001.** Empirically, the weakest successful CSU (Aave V3 Optimism) has `vol_std = 0.000014`. Below this, the SVAR covariance matrix becomes singular.

**V3.4 — Token addresses must be present for oracle lookups.** The `underlying` address field is used as the primary key for protocol oracle price lookups (`chain:address:date`). Without it, the system falls back to symbol-based lookup, which has lower coverage for non-standard tokens.

**V3.5 — Volatility coverage ≥ 70%.** The qualification threshold applied by the panel preparation step. Coverage = (days with non-NaN volatility) / (total days). Missing days come from: missing prices, missing bronze files, insufficient rolling window history.

---

## 4. End-to-End Integration Validation

These checks verify that a new adapter's data successfully flows through all pipeline stages.

### 4.1 Bronze → Silver Round-Trip Test

```python
def validate_bronze_to_silver(csu_name: str, bronze_dir: Path) -> dict:
    """Test that bronze files produce valid silver output."""
    files = sorted(bronze_dir.glob('*.json'))
    results = {'total': len(files), 'valid_silver': 0, 'supply_zero': 0,
               'borrow_negative': 0, 'empty_markets': 0}

    supply_series = []
    for f in files:
        data = json.load(open(f))
        markets = data.get('data', [])

        if not markets:
            results['empty_markets'] += 1
            continue

        total_supply = sum(
            (get_supply_raw(m) / 10**get_decimals(m)) * get_price(m)
            for m in markets if get_price(m) is not None
        )
        total_borrow = sum(
            (get_borrow_raw(m) / 10**get_decimals(m)) * get_price(m)
            for m in markets if get_price(m) is not None
        )

        if total_supply > 0:
            results['valid_silver'] += 1
            supply_series.append(total_supply)
        else:
            results['supply_zero'] += 1
        if total_borrow < 0:
            results['borrow_negative'] += 1

    results['silver_coverage'] = results['valid_silver'] / results['total']
    results['supply_cv'] = np.std(supply_series) / np.mean(supply_series) if supply_series else None
    return results
```

**Pass criteria:**
- `silver_coverage >= 0.95` — At least 95% of bronze files produce valid silver rows
- `empty_markets == 0` — No files with zero markets
- `borrow_negative == 0` — No negative borrow values
- `supply_cv < 2.0` — Supply doesn't vary by more than 2x coefficient of variation (extreme instability)

### 4.2 Bronze → Volatility Round-Trip Test

```python
def validate_bronze_to_volatility(csu_name: str, bronze_dir: Path) -> dict:
    """Test that bronze files produce non-degenerate volatility."""
    # Run composition + basket return + rolling vol
    snapshots = load_bronze_snapshots(bronze_dir)
    vol_df = build_composition_and_volatility({csu_name: snapshots}, price_cache, window=14)

    results = {}
    if vol_df.empty:
        results['volatility_produced'] = False
        return results

    vol = vol_df['volatility'].dropna()
    results['volatility_produced'] = True
    results['vol_days'] = len(vol)
    results['vol_mean'] = vol.mean()
    results['vol_std'] = vol.std()
    results['vol_nonzero_pct'] = (vol > 0).mean()
    results['vol_unique'] = vol.nunique()

    return results
```

**Pass criteria:**
- `volatility_produced == True`
- `vol_std > 0.00001` — Non-degenerate (necessary for SVAR)
- `vol_nonzero_pct > 0.3` — At least 30% of days have non-zero volatility
- `vol_days >= 100` — Enough observations for 14-day rolling window + meaningful estimation

### 4.3 Qualification Gate

After silver and gold layers are built, apply the panel qualification check:

```python
def validate_qualification(csu_name: str, panel_df: pd.DataFrame) -> dict:
    csu_data = panel_df[panel_df['csu'] == csu_name]

    util_coverage = csu_data['utilization'].notna().mean()
    vol_coverage = csu_data['volatility'].notna().mean()
    vol_std = csu_data['volatility'].std()
    util_std = csu_data['utilization'].std()
    liq_std = csu_data['liquidation'].std()

    return {
        'util_coverage': util_coverage,
        'vol_coverage': vol_coverage,
        'qualifies_70': util_coverage >= 0.70 and vol_coverage >= 0.70,
        'qualifies_60': util_coverage >= 0.60 and vol_coverage >= 0.60,
        'svar_feasible': vol_std > 0.00001 and util_std > 0.0001 and liq_std > 0.0001,
    }
```

**Pass criteria for SVAR-ready CSU:**
- `qualifies_70 == True` (or `qualifies_60` if threshold is relaxed)
- `svar_feasible == True`

---

## 5. Adapter Code Requirements

### 5.1 Function Signature

Must match the dispatcher pattern in `collect_tvl_parallel.py`:

```python
def get_{protocol}_tvl(
    web3: Web3,
    registry: str,          # Primary contract address
    block: Optional[int] = None  # None = latest block
) -> List[Dict[str, Any]]:
```

For protocols needing extra parameters (Fluid's `liq_reg`, Lista's `vaults`), the adapter receives them through the CSU config and the collection script passes them.

### 5.2 Error Handling

Must follow the `_safe_call()` pattern:
- Individual market failures must not crash the entire snapshot
- Return sensible defaults for failed calls (0 for amounts, "UNKNOWN" for symbols, 18 for decimals)
- Log errors but continue with available data
- Return empty list `[]` only on total adapter failure (cannot reach contract at all)

### 5.3 CSU Config Entry

New CSU must be registered in `code/config/csu_config.yaml`:

```yaml
{csu_name}:
  protocol: {protocol_key}  # Must match ADAPTER_MAP key
  version: v1               # Or v2, v3
  chain: {chain_name}       # Must match RPC pool + block cache
  rpc: ""                   # Empty = use RPC pool
  registry: "0x..."         # Primary contract address (checksummed)
```

And the adapter must be registered in `ADAPTER_MAP` in `collect_tvl_parallel.py`.

### 5.4 Block Cache Dependency

The collection script requires block timestamps for each chain-date. Verify:
- `data/cache/{chain}_blocks_*.json` exists and covers the target date range
- Or the block resolution endpoint is available for the chain's RPC

---

## 6. Pre-Deployment Checklist

Before running a new adapter against historical data:

### Smoke Test (1 block)

```python
# In adapter file's __main__ block:
w3 = Web3(Web3.HTTPProvider(rpc_url))
result = get_{protocol}_tvl(w3, registry_address)

assert len(result) > 0, "Adapter returned empty"
for m in result:
    assert any(k in m for k in ['supplied_raw', 'tvl_underlying_raw', 'total_assets_raw']), \
        f"No supply field in market: {m.keys()}"
    symbol = m.get('underlying_symbol') or m.get('symbol')
    assert symbol and symbol != 'UNKNOWN', f"Unresolvable symbol: {symbol}"
    decimals = m.get('underlying_decimals') or m.get('decimals') or 18
    supply_raw = m.get('supplied_raw') or m.get('tvl_underlying_raw') or m.get('total_assets_raw') or 0
    human = supply_raw / 10**decimals
    print(f"  {symbol}: {human:,.2f} tokens (raw={supply_raw}, dec={decimals})")
```

### Historical Spot Check (3 dates)

Run adapter at 3 blocks separated by months. Verify:
1. Market count is consistent (±20%)
2. Supply amounts are in the same order of magnitude
3. No market has supply_raw = 0 when it should have capital
4. Token symbols and addresses are stable across dates

### Cross-Reference with DefiLlama

Compare adapter's `total_supply_usd` against DefiLlama's reported TVL for the same protocol-chain-date. Acceptable tolerance: ±30% (differences arise from price source, inclusion of rewards/incentive tokens, and the exact block queried).

### Full Pipeline Dry Run

```bash
# 1. Collect 30 days of bronze data
python scripts/collect_tvl_parallel.py --csus {csu_name} \
    --start-date 2024-06-01 --end-date 2024-06-30

# 2. Build silver
python scripts/build_silver_tvl.py --csu {csu_name} --verbose

# 3. Verify silver output
python -c "
import pandas as pd
tvl = pd.read_csv('data/silver/tvl/daily_tvl.csv')
csu = tvl[tvl['csu']=='{csu_name}']
print(f'Days: {len(csu)}')
print(f'Supply range: ${csu.total_supply_usd.min():,.0f} - ${csu.total_supply_usd.max():,.0f}')
print(f'Utilization: {(csu.total_borrow_usd/csu.total_supply_usd).describe()}')
"

# 4. Build volatility panel (check non-zero vol)
python scripts/build_volatility_panel.py --skip-fetch

# 5. Check volatility output
python -c "
import pandas as pd
panel = pd.read_parquet('data/analysis/vol_util_panel.parquet')
csu = panel[panel['csu']=='{csu_name}']
vol = csu['volatility'].dropna()
print(f'Vol days: {len(vol)}')
print(f'Vol std: {vol.std():.8f}')
print(f'Vol nonzero: {(vol>0).sum()}/{len(vol)}')
assert vol.std() > 0.00001, 'FAIL: volatility is degenerate'
print('PASS: volatility is non-degenerate')
"
```

---

## 7. Protocol-Specific Gotchas (Learned from Existing Adapters)

| Issue | Affected Protocols | Symptom | Fix |
|-------|-------------------|---------|-----|
| `underlying()` reverts on native token markets | Compound V2 forks (Venus, Benqi) | Missing market or crash | Catch revert, map to chain native symbol |
| Multiple fTokens share one underlying | Fluid | Double-counted borrow | Cache borrow per underlying address, don't sum |
| `totalSupply()` returns fToken supply, not underlying | Compound V2 forks | Wildly wrong TVL | Use `getCash() + totalBorrows()` instead |
| Inactive credit managers | Gearbox | Reverts on `pool()` call | Wrap in try/catch, skip silently |
| Collateral-only markets (no borrow) | Compound V3 | `borrowed_raw = 0` is correct | Don't flag as error; borrow = 0 is valid |
| Registry address changes with upgrades | Aave V3, SparkLend | Adapter returns 0 markets | Use PoolAddressesProvider (immutable) to resolve current Pool |
| Stale oracle prices for exotic tokens | All | Volatility = 0 even with diverse basket | Ensure token addresses are returned for oracle cache lookups |

---

## 8. Summary Decision Matrix

For a new CSU to be worth building an adapter for, it must clear all levels:

| Gate | Criterion | Observable Before Building |
|------|-----------|---------------------------|
| **G0: Has liquidations** | CSU already in silver liquidations | Check `data/silver/liquidations/` |
| **G1: Has contract to query** | Known registry/pool contract address | Etherscan / protocol docs |
| **G2: Has multi-asset collateral** | ≥2 non-stablecoin tokens in collateral basket | Check protocol UI or docs |
| **G3: Tokens are priceable** | DefiLlama or on-chain oracle covers the tokens | `get_defillama_id(symbol)` returns non-None |
| **G4: Sufficient history** | Protocol deployed ≥6 months ago | Check deployment block |
| **G5: Adapter produces valid TVL** | Smoke test returns markets with supply > 0 | Run adapter at latest block |
| **G6: Volatility is non-degenerate** | `vol_std > 0.00001` after full pipeline | Run 30-day dry run |

**Priority order for the 11 CSUs missing TVL adapters:**

CSUs that already have liquidation data and whose protocol architecture matches an existing adapter are highest priority — they can often use `compound_v2_style` or the existing Aave V3 adapter with a new registry address in `csu_config.yaml` rather than writing new code.

---

*Last Updated: February 17, 2026*
*Derived from: 13 successful SVAR CSUs, 42 bronze TVL directories, 24,254 silver TVL records*
