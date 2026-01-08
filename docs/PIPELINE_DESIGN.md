# Data Pipeline Design: Bronze → Silver → Gold

## Overview

You have 43 working CSUs ready to collect historical data for your panel VAR thesis.

**Goal:** Collect TVL and liquidation data for all CSUs, transform to analysis-ready format.

**Architecture:** Medallion (Bronze → Silver → Gold)

---

## Major Design Decisions You Need to Make

### 1. TIME RANGE & GRANULARITY

**Decision: How far back to collect data?**

Options:
- **Option A: 1 year** (Simple, faster, recent data)
- **Option B: 2 years** (Better for econometrics, more cycles)
- **Option C: Since protocol launch** (Complete history, but varies by protocol)

**My Recommendation:** Start with **1 year** (365 days) for all protocols
- Most protocols have been active for 1+ years
- Enough data for panel VAR (365 observations × 43 CSUs = 15,695 data points)
- Can extend later if needed

**Decision: What granularity?**

Options:
- **Daily snapshots** (simpler, 365 data points per CSU)
- **Hourly snapshots** (more granular, 8,760 data points per CSU)
- **Per-block** (maximum detail, but huge data)

**My Recommendation:** **Daily snapshots** (one per day at midnight UTC)
- Sufficient for macro DeFi analysis
- Much faster to collect
- Easier to work with in regression

---

### 2. DATA STORAGE STRUCTURE

**Decision: Where to store data?**

Recommended directory structure:
```
thesis_v2/
├── data/
│   ├── bronze/          # Raw blockchain data
│   │   ├── tvl/
│   │   │   ├── aave_v3_ethereum/
│   │   │   │   ├── 2024-01-01.json
│   │   │   │   ├── 2024-01-02.json
│   │   │   │   └── ...
│   │   │   └── compound_v3_eth_usdc/
│   │   │       └── ...
│   │   └── liquidations/
│   │       ├── aave_v3_ethereum/
│   │       │   ├── 2024-01-01.json
│   │       │   └── ...
│   │       └── ...
│   │
│   ├── silver/          # Cleaned, normalized
│   │   ├── tvl/
│   │   │   ├── aave_v3_ethereum.parquet
│   │   │   └── compound_v3_eth_usdc.parquet
│   │   └── liquidations/
│   │       └── aave_v3_ethereum.parquet
│   │
│   └── gold/            # Analysis-ready panel data
│       ├── daily_panel.parquet     # All CSUs, all dates, TVL + liquidations
│       └── metadata.json           # CSU info, date ranges, etc.
```

**Decision: File format?**

| Layer | Format | Why |
|-------|--------|-----|
| Bronze | JSON | Easy to read, preserves raw structure |
| Silver | Parquet | Efficient, columnar, fast for pandas |
| Gold | Parquet | Panel data format, ready for R/Python |

---

### 3. PARALLELIZATION STRATEGY

**Decision: How to parallelize?**

**Approach: Parallelize by CSU × Date**

```python
# Example: 43 CSUs × 365 days = 15,695 tasks
tasks = [
    (csu='aave_v3_ethereum', date='2024-01-01'),
    (csu='aave_v3_ethereum', date='2024-01-02'),
    ...
    (csu='compound_v3_eth_usdc', date='2024-01-01'),
    ...
]
```

**Worker Strategy:**

Option A: **ProcessPoolExecutor** (Python multiprocessing)
```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(collect_csu_day, csu, date) 
               for csu, date in tasks]
```

Option B: **ThreadPoolExecutor** (I/O bound, simpler)
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(collect_csu_day, csu, date) 
               for csu, date in tasks]
```

**My Recommendation:** **ThreadPoolExecutor with 5-10 workers**
- RPC calls are I/O bound (waiting on network)
- Threads work well for I/O
- Easier to debug than processes

---

### 4. RATE LIMITING & RPC STRATEGY

**Alchemy Limits:**
- Free tier: 300 requests/second (shared across all apps)
- Growth tier: 660 requests/second
- You have API key, so probably Growth tier

**Rate Limiting Strategy:**

```python
import time
from threading import Lock

class RateLimiter:
    def __init__(self, calls_per_second=100):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
        self.lock = Lock()
    
    def wait(self):
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            self.last_call = time.time()
```

**My Recommendation:**
- **100 calls/second** to be safe
- One rate limiter per RPC endpoint
- Exponential backoff on errors

---

### 5. ERROR HANDLING & CHECKPOINTING

**Decision: How to handle failures?**

**Checkpointing Strategy:**
```
data/checkpoints/
├── tvl_progress.json
└── liquidations_progress.json
```

```json
{
  "aave_v3_ethereum": {
    "completed_dates": ["2024-01-01", "2024-01-02", ...],
    "failed_dates": ["2024-03-15"],
    "last_updated": "2025-01-07T12:00:00Z"
  }
}
```

**Retry Logic:**
```python
def collect_with_retry(csu, date, max_retries=3):
    for attempt in range(max_retries):
        try:
            return collect_csu_day(csu, date)
        except Exception as e:
            if attempt == max_retries - 1:
                log_failure(csu, date, e)
                return None
            time.sleep(2 ** attempt)  # Exponential backoff
```

**My Recommendation:**
- Save bronze data immediately after collection
- Log all failures to file
- Resume from checkpoint file
- Skip already-collected dates

---

### 6. PRICING STRATEGY

**Decision: When to get USD prices?**

Options:
- **Option A:** During bronze collection (save raw prices too)
- **Option B:** During silver processing (fetch once, use for all CSUs)
- **Option C:** During gold aggregation (daily prices only)

**My Recommendation:** **Option B - During silver processing**

Why:
- Bronze stays pure (blockchain data only)
- Silver fetches prices once per token per day
- Cache prices for reuse across CSUs
- Can update prices without re-collecting blockchain data

**Price Sources:**
1. CoinGecko API (free tier: 10-50 calls/min)
2. DefiLlama API (no auth, generous limits)
3. Your existing price cache from v1

---

### 7. SCHEMA DESIGN

**Bronze Schema (Raw JSON):**
```json
{
  "csu": "aave_v3_ethereum",
  "date": "2024-01-01",
  "block": 18840123,
  "timestamp": 1704067200,
  "tvl_raw": [
    {
      "asset": "0x...",
      "symbol": "USDC",
      "decimals": 6,
      "total_supplied_raw": 1000000000000,
      "total_borrowed_raw": 500000000000
    }
  ]
}
```

**Silver Schema (Parquet columns):**
```
date | block | csu | asset | symbol | supplied | borrowed | supplied_usd | borrowed_usd
```

**Gold Schema (Panel format):**
```
date | csu | total_tvl_usd | total_supplied_usd | total_borrowed_usd | utilization_rate | num_assets | liquidations_usd
```

---

## Recommended Phased Approach

### Phase 1: Single CSU, Single Day (Test)
- Pick one CSU (e.g., Aave V3 Ethereum)
- Collect one day of data
- Validate bronze → silver → gold works
- **Time estimate:** 1 hour to build + test

### Phase 2: Single CSU, Full History (Validate)
- Collect 365 days for one CSU
- Run sequentially (no parallelization yet)
- Check data quality, identify issues
- **Time estimate:** 2-4 hours (depends on RPC speed)

### Phase 3: All CSUs, Sequential (Baseline)
- Collect all 43 CSUs × 365 days sequentially
- Establish baseline timing
- **Time estimate:** 12-24 hours total

### Phase 4: Parallelize (Production)
- Add ThreadPoolExecutor
- Start with 5 workers, scale to 10
- Monitor RPC rate limits
- **Time estimate:** 2-4 hours total (6-10x speedup)

### Phase 5: Incremental Updates (Daily)
- Script to add new day's data
- Run daily via cron
- **Time estimate:** 5-10 minutes per day

---

## Key Questions for You

Before we start coding, please decide:

1. **Time range:** How many days back? (Recommend: 365)

2. **Granularity:** Daily or hourly? (Recommend: Daily)

3. **Start date:** Fixed date (2024-01-01) or dynamic (365 days from today)?

4. **Workers:** How many parallel workers? (Recommend: 5-10)

5. **Storage location:** Keep in thesis_v2/data/ or separate drive?

6. **Test protocol:** Which CSU to test with? (Recommend: aave_v3_ethereum)

---

## What I'll Build for You

Once you answer the questions above, I'll create:

1. **Bronze collector:** `scripts/collect_bronze.py`
   - Parallel collection with rate limiting
   - Checkpointing and retry logic
   - Progress bars

2. **Silver processor:** `scripts/process_silver.py`
   - Clean and normalize bronze data
   - Add USD prices
   - Save as Parquet

3. **Gold aggregator:** `scripts/aggregate_gold.py`
   - Daily panel data
   - Ready for econometric analysis

4. **Test script:** `scripts/test_pipeline.py`
   - Validate one CSU end-to-end

5. **Monitor script:** `scripts/monitor_progress.py`
   - Check collection status
   - Identify failures

---

## Expected Performance

**Sequential (no parallelization):**
- ~2 RPC calls per CSU per day
- 43 CSUs × 365 days × 2 calls = 31,390 calls
- At 10 calls/sec = 3,139 seconds = ~52 minutes
- Add processing time = **~2-3 hours total**

**Parallel (10 workers):**
- 10x speedup
- **~15-20 minutes total for 1 year of data**

**Storage:**
- Bronze: ~500 MB (JSON)
- Silver: ~100 MB (Parquet compressed)
- Gold: ~10 MB (aggregated)

---

## Next Step

Answer the 6 key questions above, and I'll start building the pipeline!
