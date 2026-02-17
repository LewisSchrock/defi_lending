# Feasibility Report: Block-Level Data Granularity

**Date**: February 16, 2026
**Author**: Data Pipeline Analysis
**Status**: Assessment only (no changes made)

---

## Executive Summary

This report assesses the difficulty of moving from **daily snapshots** to **block-level (or sub-daily)** granularity for three variables in the Panel SVAR analysis:

1. **Utilization (Leverage)** = Borrowed / Supplied
2. **TVL Components** = Total supply and borrow per CSU
3. **Collateral Asset Volatility** = Weighted basket return volatility

**Liquidations are already block-level** (event-based, each has a specific block number and timestamp).

### Difficulty Summary

| Variable | Current | Block-Level Difficulty | Recommended Upgrade |
|----------|---------|----------------------|---------------------|
| Liquidation | Block-level | Already done | N/A |
| Utilization | Daily | **Medium** | Hourly or 5-min |
| TVL (Supply/Borrow) | Daily | **Medium** | Hourly or 5-min |
| Collateral Volatility | Daily | **Medium-Hard** | Hourly |

**Overall verdict**: With **dRPC paid tier** (prepaid balance loaded, no rate limit ceiling), RPC capacity is not a constraint for any granularity up to per-block on Ethereum. Every-5-minute across all 42 CSUs costs ~$70/month in CU. True per-block on high-throughput L2s (Arbitrum: 345K blocks/day) requires event-driven reconstruction rather than polling. The binding constraints are **engineering effort and price oracle update frequency**, not RPC capacity or cost.

---

## 1. Current State: Daily Snapshots

### How It Works Now

Each day, we take **one snapshot** per CSU by calling smart contract view functions at the midnight UTC block:

| Component | On-Chain Source | Calls per Snapshot | Current Frequency |
|-----------|----------------|-------------------|-------------------|
| TVL (Aave V3) | `getReservesList()` + per-reserve `totalSupply()` | ~105-175 | 1x/day |
| TVL (Compound V3) | `totalsBasic()` + per-collateral `totalsCollateral()` | ~40 | 1x/day |
| TVL (Compound V2-style) | per-market `getCash()`, `totalBorrows()`, `totalSupply()` | ~90-270 | 1x/day |
| TVL (Fluid) | per-fToken `totalAssets()` + `getOverallTokenData()` | ~130-165 | 1x/day |
| TVL (Others) | Protocol-specific | ~10-50 | 1x/day |
| **Total (42 CSUs)** | | **~7,560 calls** | **1x/day** |

### Current Daily Cost

- **RPC calls**: ~7,560 `eth_call` requests per full collection
- **Storage**: ~0.03 GB/year
- **Time**: ~5-10 minutes with 2 parallel workers
- **Cost**: Effectively free (well within free tier limits)

---

## 2. Variable-by-Variable Analysis

### 2.1 Utilization (Leverage Ratio)

**Formula**: `utilization = total_borrow_usd / total_supply_usd`

**What changes at block level**:
- Utilization changes every time someone supplies, borrows, repays, or withdraws
- On active protocols (Aave V3 Ethereum), this happens **hundreds of times per day**
- Interest accrual also changes these values continuously (every block)

**Difficulty: MEDIUM**

The core challenge is that utilization requires the same contract calls as TVL. There is no separate, cheaper way to get utilization without reading supply and borrow totals. So this is effectively the same problem as TVL below.

**One optimization**: For Aave V3 and Compound V3, you can monitor `Supply`, `Borrow`, `Repay`, `Withdraw` events and reconstruct running totals from a known starting point, rather than polling contract state. This is an **event-driven** approach:

```
Approach A (polling):  Read contract state every N blocks → ~180 calls/snapshot
Approach B (events):   Subscribe to events, reconstruct state → ~4 event topics to monitor
```

Approach B is dramatically cheaper but requires more complex bookkeeping code and introduces drift risk from missed events.

---

### 2.2 TVL Components (Supply & Borrow)

**What's needed**: `totalSupply()` and `totalBorrow()` at higher frequency

**Difficulty by granularity**:

| Granularity | Snapshots/Day | RPC Calls/Day (42 CSUs) | vs. Current | Feasible? |
|-------------|---------------|------------------------|-------------|-----------|
| Daily (current) | 1 | 7,560 | 1x | Current |
| **Hourly** | 24 | **181,440** | 24x | **Yes** |
| Every 5 min | 288 | 2,177,280 | 288x | Marginal |
| Every 1 min | 1,440 | 10,886,400 | 1,440x | Difficult |
| Every block (ETH) | 7,200 | 54,432,000 | 7,200x | ETH only |
| Every block (Arb) | 345,600 | 2,612,736,000 | ~346Kx | No |

**RPC Provider Capacity — dRPC (Primary Provider)**:

Our primary RPC provider is **dRPC**. Based on documented and tested limits (see `context/dRPC_optimization_guide.md`):

**dRPC Paid Tier** (current plan — prepaid balance loaded):
- **Rate Limit**: Higher CU allocations than free tier (no hard 315K CU/min ceiling)
- **Priority Routing**: Requests routed to fastest available nodes
- **Better Latency**: No throttling during peak demand periods
- **Batch Support**: JSON-RPC batch calls supported (up to 100 per batch)
- **Cost per `eth_call`**: ~1 CU (deducted from prepaid balance)

For reference, the free tier alone supports ~250 req/sec (~21.6M/day). The paid tier removes this ceiling.

| Granularity | Calls/Day | Feasible on Paid Tier? | Binding Constraint |
|-------------|----------|----------------------|-------------------|
| Daily (current) | 7,560 | Trivially yes | None |
| **Hourly** | 181,440 | **Yes — negligible** | None |
| **Every 5 min** | 2,177,280 | **Yes — comfortable** | None |
| **Every 1 min** | 10,886,400 | **Yes** | Engineering effort |
| **Every block (ETH)** | 54,432,000 | **Yes** | CU cost (~$5-15/mo) |
| Every block (Arb) | 2,612,736,000 | No (polling) | L2 block rate; use event-driven |

With the paid tier, **every granularity up to and including per-block on Ethereum is feasible**. The only infeasible option via polling is per-block on high-throughput L2s (Arbitrum, Base) where event-driven reconstruction is the correct approach.

**Fallback providers** (already configured in pipeline):

| Provider | Rate Limit | Daily Capacity | Role |
|----------|-----------|---------------|------|
| dRPC (paid) | Uncapped (priority routing) | Unlimited (pay per CU) | **Primary** |
| Alchemy (free) | 300 CU/sec | ~1M CU/day | Fallback |
| BlockPi (free) | 400 RU/sec | ~1.6M/day | Fallback |

**Key constraint**: The 42 CSUs span **10 different chains**. Each chain requires its own RPC endpoint. dRPC supports all 10 chains natively, so the rate limit is shared across chains but routing is per-chain.

**Per-chain breakdown at hourly granularity**:

| Chain | CSUs | Calls/Hour | Calls/Day | % of dRPC Capacity |
|-------|------|-----------|-----------|-------------------|
| Ethereum | 12 | ~2,160 | 51,840 | 0.24% |
| Arbitrum | 8 | ~1,440 | 34,560 | 0.16% |
| Base | 5 | ~900 | 21,600 | 0.10% |
| Avalanche | 3 | ~540 | 12,960 | 0.06% |
| Polygon | 3 | ~540 | 12,960 | 0.06% |
| Optimism | 4 | ~720 | 17,280 | 0.08% |
| BSC | 3 | ~540 | 12,960 | 0.06% |
| Gnosis | 1 | ~180 | 4,320 | 0.02% |
| Linea | 1 | ~180 | 4,320 | 0.02% |
| Scroll | 2 | ~360 | 8,640 | 0.04% |
| **Total** | **42** | **7,560** | **181,440** | **0.84%** |

**Verdict**: With dRPC paid tier, **RPC capacity is not a constraint at any granularity up to per-block on Ethereum**. The binding constraints are purely engineering effort, storage, and (for volatility) price oracle update frequency.

---

### 2.3 Collateral Asset Volatility

**Current formula**:
```
R_t = Σ w_{i,t-1} × r_{i,t}        (basket return)
r_{i,t} = log(p_t) - log(p_{t-1})   (log return per token)
σ_t = rolling_std(R, window=14)      (rolling volatility)
```

**What changes at block level**: This is the hardest variable because it requires:

1. **Collateral basket weights** at higher frequency (from TVL data above)
2. **Token prices** at higher frequency

**Difficulty: MEDIUM-HARD**

**Challenge 1: Price data at block level**

Currently, prices come from:
- Chainlink oracle reads (on-chain, `latestRoundData()`)
- Uniswap V3 TWAP (on-chain, `pool.observe()`)
- DefiLlama API (off-chain fallback, daily only)

At block level, you need prices at every observation point. Options:

| Source | Granularity Available | RPC Cost | Reliability |
|--------|----------------------|----------|-------------|
| Chainlink on-chain | Every heartbeat (~1hr for major pairs, 1% deviation trigger) | 1 call per token per observation | High |
| Uniswap V3 TWAP | Every block | 1 call per pool per observation | Medium (manipulation risk) |
| Chainlink off-chain (API) | Per-round (~minutes) | 0 RPC calls | High but off-chain |
| DefiLlama | Daily/Hourly | 0 RPC calls | Medium |

**Additional RPC cost for prices per snapshot**:

For 42 CSUs with average 10 unique collateral tokens each:
- ~420 unique (CSU, token) pairs
- But many tokens overlap (WETH, USDC, etc.)
- ~50-80 unique tokens across all CSUs

| Approach | Calls per Observation | Notes |
|----------|----------------------|-------|
| Chainlink read per token | 50-80 | One `latestRoundData()` per unique token |
| Uniswap TWAP per token | 50-80 | One `pool.observe()` per unique token |
| Combined | ~100-160 | Chainlink primary + Uniswap fallback |

This **adds ~100-160 calls** per observation point on top of TVL calls.

**Challenge 2: Basket weight stability**

At daily frequency, collateral composition is relatively stable (weights shift slowly). At block level, individual supply/withdraw transactions can cause temporary spikes in basket weights. This means:

- Need to decide: use **instantaneous** weights (noisy) or **smoothed** weights (lagged)?
- Instantaneous: More accurate but volatile, susceptible to single large deposits/withdrawals
- Smoothed (e.g., 24-hour rolling average): More stable, easier to interpret, but partially defeats the purpose of block-level data

**Challenge 3: Rolling window definition**

Currently uses 14-day rolling std. At block level:
- 14-day window on hourly data = 336 observations per window
- 14-day window on 5-min data = 4,032 observations per window
- Computational cost grows linearly with observations

**Verdict**: Hourly volatility is achievable. Chainlink oracles update frequently enough for major tokens (~hourly heartbeats). Long-tail tokens may need Uniswap TWAP. Below hourly, price data becomes the binding constraint.

---

## 3. Total Cost at Each Granularity

### RPC Calls per Day (All Variables, 42 CSUs)

| Granularity | TVL Calls | Price Calls | Total Calls/Day | Storage/Year |
|-------------|----------|-------------|----------------|--------------|
| **Daily (current)** | 7,560 | ~160 | **~7,720** | 0.03 GB |
| **Hourly** | 181,440 | 3,840 | **~185,280** | 0.7 GB |
| Every 5 min | 2,177,280 | 46,080 | **~2,223,360** | 8.2 GB |
| Every 1 min | 10,886,400 | 230,400 | **~11,116,800** | 41 GB |

### Infrastructure Requirements (dRPC Paid Tier)

| Granularity | Workers Needed | Collection Window | Est. CU Cost/Month |
|-------------|---------------|-------------------|---------------------|
| Daily | 2 | ~10 min/day | ~$0.25 |
| **Hourly** | **4** | **~5 min/hour** | **~$6** |
| **Every 5 min** | **8** | **~2 min/5min** | **~$70** |
| Every 1 min | 16 | ~30 sec/min | ~$350 |
| Every block (ETH) | 32+ | Continuous | ~$1,700 |

*CU cost estimates assume ~1 CU per `eth_call` at dRPC's pay-as-you-go rate. Actual costs depend on dRPC's per-CU pricing for your plan tier.*

**Note**: With the paid tier, rate limits are not a concern. Collection time is dominated by network latency, not throttling. With 50-100 concurrent workers (as already implemented in `collect_liquidations_parallel.py`), even 5-min snapshots complete well within the window.

**Existing concurrency patterns**: The liquidation enrichment pipeline (`enrich_liquidations_multi_oracle.py`) already uses ThreadPoolExecutor with 50-100 workers against dRPC, sustaining ~100-150 req/sec. This same pattern applies directly to higher-frequency TVL collection.

---

## 4. Implementation Difficulty Assessment

### Option A: Hourly Snapshots (Recommended)

**Difficulty: Medium** — 3-5 days of engineering work

**What needs to change**:

1. **Collection script** (`collect_tvl_parallel.py`):
   - Change from daily midnight block to hourly blocks (every 300 blocks on ETH, ~1800 on Arb)
   - Add scheduler/cron to run every hour instead of daily
   - Modify file naming: `{csu}/YYYY-MM-DD_HH.json` instead of `{csu}/YYYY-MM-DD.json`

2. **Price collection**:
   - Add hourly Chainlink oracle reads alongside TVL snapshots
   - One `latestRoundData()` per unique token per hour
   - ~80 additional calls per hour

3. **Silver transformation** (`build_silver_tvl.py`):
   - Aggregate to hourly CSU-level TVL instead of daily
   - Output schema gains `hour` column

4. **Volatility calculation** (`prepare_panel_svar_data.py`):
   - Basket returns calculated hourly instead of daily
   - Rolling window adjusts: 14-day × 24 hours = 336 observations
   - Or use shorter window (e.g., 7-day = 168 observations)

5. **Panel SVAR analysis**:
   - Dataset grows 24x (from 20K to ~480K observations)
   - Pedroni SVAR computation time grows accordingly
   - May need to subsample or use daily aggregates for SVAR, but have hourly available for robustness

**Risks**: Low. Existing adapters work at any block number. No new contract interfaces needed.

---

### Option B: Every-5-Minute Snapshots

**Difficulty: Medium** — 1-2 weeks of engineering work

**With dRPC paid tier, RPC capacity is not a constraint.** Remaining challenges are purely engineering:

- Storage grows to 8.2 GB/year (manageable but needs monitoring)
- Price data at 5-min: Chainlink heartbeats (~1hr for major pairs) are too slow. Options:
  - **Uniswap V3 TWAP** (on-chain, ~1 call per token per observation)
  - **Chainlink with interpolation** (use last known price between heartbeats)
  - Both approaches add ~80-160 extra calls per snapshot, well within dRPC capacity
- Collection must run continuously (daemon or cron every 5 min), not batch

**dRPC paid tier advantages at this granularity**:
- **No throttling**: Priority routing, no peak-demand slowdowns
- **Batch requests**: Group 42 CSUs × ~180 calls into JSON-RPC batches of 100, reducing network overhead by ~95%
- **Concurrent workers**: Reuse the ThreadPoolExecutor pattern from liquidation enrichment (already proven at 100-150 req/sec against dRPC)
- **CU cost**: ~2.2M calls/day × ~1 CU × 30 days ≈ ~$70/month (verify against your plan's per-CU rate)

**New infrastructure**:
- Cron job every 5 minutes (or systemd timer)
- Error recovery for missed intervals
- Data compaction (roll up to hourly/daily for long-term storage)

---

### Option C: True Block-Level (ETH Mainnet Only)

**Difficulty: Hard** — 2-4 weeks of engineering work

**Why only Ethereum mainnet (via polling)**:
- Ethereum: 7,200 blocks/day → 54M calls/day → **feasible on dRPC paid tier** (~$1,700/mo in CU cost)
- Other L2s (Base, Optimism): 28K-43K blocks/day → polling is expensive but technically possible
- Arbitrum: 345,600 blocks/day → 2.6B calls/day → **not feasible via polling** regardless of tier (network latency alone would exceed 24 hours)

**Polling approach for ETH**: With the paid tier, 54M calls/day at ~250 req/sec takes ~60 hours sequentially. With 50 concurrent workers, it completes in ~1.2 hours — tight but feasible. The event-driven approach below is more efficient:

**Approach**: Switch from polling to **event-driven state reconstruction**:
1. Index all `Supply`, `Borrow`, `Repay`, `Withdraw`, `Liquidation` events via `eth_getLogs`
2. Reconstruct running supply/borrow totals from a known starting state
3. Only need to poll contract state once (initial snapshot), then track deltas

**dRPC advantage**: `eth_getLogs` is already proven at scale in our liquidation collection pipeline — we fetched 438K events across 11 chains using dRPC with 13 parallel workers. The same infrastructure applies here.

**Advantages**: No rate limit issues (events fetched in bulk via `eth_getLogs`), exact block-level granularity
**Disadvantages**: Complex bookkeeping, protocol-specific event parsing, drift risk from missed events

**Price data**: Use Chainlink `AnswerUpdated` events (exact block of each price update) rather than polling. Fetch via `eth_getLogs` in bulk — same pattern as liquidation collection. This gives prices at their true update frequency with minimal RPC cost.

---

### Option D: Hybrid Approach

**Difficulty: Medium** — 1 week of engineering work

Combine block-level liquidations (already have) with hourly TVL/prices:
- **Liquidations**: Block-level (current)
- **TVL/Utilization**: Hourly snapshots
- **Prices/Volatility**: Hourly from Chainlink

Then for analysis:
- Aggregate all to hourly for Panel SVAR
- Use block-level liquidations for event studies and microstructure analysis
- Daily SVAR as robustness check

This gives you the **best cost/benefit ratio**.

---

## 5. What Doesn't Change

Regardless of granularity:

- **Adapters** (`adapters/tvl/*.py`): Work at any block number, no changes needed
- **Bronze format**: Same JSON structure, just more files
- **Silver schema**: Same columns, add time dimension
- **Gold aggregation**: Same logic, parameterized by time window
- **RPC providers**: Same endpoints, just more calls
- **On-chain reliability**: Contract reads are deterministic at any block

---

## 6. Recommendation

**Start with hourly (Option A)** or go straight to **5-min (Option B)**:

With dRPC paid tier, the decision between granularity levels is purely engineering effort vs. CU cost:

| Option | Engineering | CU Cost/Month | Granularity Gain |
|--------|-----------|---------------|-----------------|
| **Hourly** | 3-5 days | ~$6 | 24x |
| **Every 5 min** | 1-2 weeks | ~$70 | 288x |
| **Every 1 min** | 1-2 weeks | ~$350 | 1,440x |
| **Per-block (ETH only)** | 2-4 weeks | ~$1,700 | 7,200x |

The main reason to start with hourly is it's less engineering work upfront. But if you have the budget and time, 5-min gives you much finer resolution at a reasonable cost.

**Then evaluate**:
- If sub-daily data shows interesting intra-day patterns → move to 5-min if not already
- If you want microstructure analysis → implement event-driven for ETH only (Option C)
- If the thesis needs only daily Panel SVAR → use sub-daily for robustness checks

**For the current Panel SVAR thesis**: Hourly or 5-min data would allow robustness checks (does the daily aggregation mask important dynamics?) but the SVAR itself would likely still use daily frequency due to the econometric properties of the model. Having the higher-frequency data available strengthens the paper by demonstrating the daily aggregation choice is intentional, not a data limitation.

---

## 7. Quick Reference: What Each Variable Needs

### Utilization at Higher Frequency
```
Source:     Same TVL contract calls (totalSupply, totalBorrow)
Extra cost: Zero beyond TVL calls
Formula:    utilization_t = borrow_t / supply_t  (same, just more frequent)
Difficulty: Tied entirely to TVL collection frequency
```

### TVL at Higher Frequency
```
Source:     Same protocol adapters (no code changes)
Extra cost: Linear scaling (24x for hourly, 288x for 5-min)
Formula:    Same aggregation (sum across markets per CSU)
Difficulty: Scheduling and storage management
```

### Volatility at Higher Frequency
```
Source:     Composition (from TVL) + Prices (Chainlink/Uniswap)
Extra cost: TVL calls + ~80-160 price calls per observation
Formula:    Same basket return + rolling std, more observations in window
Difficulty: Price data availability is the binding constraint
            - Hourly: Chainlink heartbeats sufficient for major tokens
            - 5-min: Need Uniswap TWAP for real-time prices
            - Per-block: Need event-driven price reconstruction
```

---

## Appendix: dRPC-Specific Context

**Reference**: `context/dRPC_optimization_guide.md`

dRPC is our primary RPC provider. We are on the **paid tier with prepaid balance loaded**.

```
dRPC Paid Tier:
├── Rate Limit:        No hard ceiling (priority routing)
├── Practical Limit:   ~250+ eth_call req/sec sustained (no throttling)
├── Peak Throttling:   None (priority routing bypasses demand contention)
├── Daily Capacity:    Unlimited (pay per CU)
├── Batch Support:     Up to 100 calls per JSON-RPC batch
└── Cost per eth_call: ~1 CU (deducted from prepaid balance)

For reference, the free tier supports:
├── Rate Limit:        ~315,000 CU/minute (~5,250 CU/sec)
├── Practical Limit:   ~250 eth_call req/sec sustained
├── Peak Throttling:   ~2,100 CU/sec during high demand
└── Daily Capacity:    ~21.6M requests/day
```

**What we've already proven against dRPC**:
- Liquidation collection: 438K events across 11 chains using ThreadPoolExecutor (13 workers)
- Liquidation enrichment: 100-150 req/sec sustained with 50-100 workers
- Price caching with persistent cache + checkpointing
- Automatic exponential backoff on rate limit errors
- Key blacklisting on 401 errors

**How paid tier changes the feasibility picture**:

| Granularity | Without dRPC Paid | With dRPC Paid |
|-------------|------------------|---------------|
| Hourly | Comfortable (free tier) | **Trivial** (~$6/mo) |
| Every 5 min | Marginal on generic providers | **Comfortable** (~$70/mo) |
| Every 1 min | Difficult | **Feasible** (~$350/mo) |
| Every block (ETH) | Hard, needs paid provider | **Feasible via polling** (~$1,700/mo) or **cheap via events** |
| Every block (L2s) | Infeasible via polling | **Feasible via event-driven** (bulk `eth_getLogs`) |

The binding constraint is no longer RPC rate limits or cost for any realistic granularity. Instead, the binding constraints are:
1. **Engineering effort** (scheduling, error recovery, storage management)
2. **Price data availability** (Chainlink heartbeats limit sub-hourly price accuracy for volatility)
3. **L2 block production rates** (Arbitrum's 0.25s blocks make per-block polling infeasible; use event-driven reconstruction)

---

**Conclusion**: With dRPC paid tier, the RPC infrastructure supports **any granularity** for all 42 CSUs across 10 chains. The existing concurrency patterns from the liquidation pipeline transfer directly. The only questions are: (1) how much engineering effort to invest, (2) what CU budget is acceptable, and (3) whether price oracle update frequency supports the target granularity for the volatility variable.
