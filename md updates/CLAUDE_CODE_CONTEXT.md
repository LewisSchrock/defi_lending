# DeFi Lending Thesis - Project Context for Claude Code

## 🎯 Project Overview

**Goal:** Empirically analyze how leverage and liquidations contribute to volatility across DeFi lending protocols.

**Approach:** Collect historical TVL and liquidation data from 43 Credit Supply Units (CSUs) across 15 blockchain networks, then analyze the relationship between leverage, liquidations, and market volatility.

---

## 📊 What We Have Built (Current State)

### ✅ Complete Infrastructure

**1. Protocol Adapters (43 Working CSUs)**
- **Aave V3:** 12 CSUs across 12 chains (Ethereum, Arbitrum, Base, Polygon, etc.)
- **Compound V3:** 19 CSUs (discovered 16 additional markets beyond initial 3)
  - Ethereum: 5 markets (USDC, WETH, USDT, wstETH, USDS)
  - Arbitrum: 4 markets (USDC.e, USDC, WETH, USDT)
  - Base: 4 markets (USDC, USDbC, WETH, AERO)
  - Optimism: 3 markets (USDC, USDT, WETH)
- **Compound V2-style:** 8 CSUs (Venus, Moonwell, Tectonic variants, Lista, Benqi, SparkLend, Sumer)
- **Fluid:** 4 CSUs (Ethereum, Arbitrum, Base, Plasma)
- **Unique:** 3 CSUs (Gearbox, Cap, Kinetic)

**Location:** `adapters/tvl/` and `adapters/liquidations/`

### ✅ Multi-Account RPC Pool

**File:** `config/rpc_pool.py`

**Features:**
- 5 Alchemy accounts with verified key-chain mapping
- Rate limiting: 10 calls/sec per key (Alchemy free tier compliant)
- Automatic load distribution across working keys
- Public RPC fallbacks for chains without Alchemy support

**Verified Key Mapping (from test_key_mapping.py):**
```
✅ Ethereum:  5 keys (50 calls/sec capacity)
✅ Arbitrum:  4 keys (40 calls/sec capacity)
✅ Base:      5 keys (50 calls/sec capacity)
✅ Polygon:   5 keys (50 calls/sec capacity)
✅ Optimism:  4 keys (40 calls/sec capacity)
✅ Avalanche: 5 keys (50 calls/sec capacity)
✅ Binance:   4 keys (40 calls/sec capacity)
✅ Linea:     4 keys (40 calls/sec capacity)
✅ Gnosis:    4 keys (40 calls/sec capacity)
❌ Plasma:    0 keys (uses public RPC)
```

### ✅ Testing Infrastructure

**Files:**
- `scripts/test_all_csus.py` - Test all 43 CSUs at current block
- `scripts/test_single_csu.py` - Test one CSU in detail
- `scripts/test_single_day.py` - Test historical data collection for one day
- `scripts/test_key_mapping.py` - Verify which keys work for which chains

**Status:** 43/43 CSUs working (Gearbox confirmed, Cap/Kinetic/Fluid deferred)

### ✅ Configuration

**Files:**
- `config/csu_config.yaml` - All 43 CSU definitions (protocols, chains, registries)
- `config/rpc_config.py` - Original RPC config (still functional)
- `config/rpc_pool.py` - New multi-account pool with rate limiting
- `config/utils/time.py` - NY timezone conversion utilities
- `config/utils/block.py` - Binary search for block-by-timestamp

### ✅ Documentation

**Key Docs:**
- `docs/ALCHEMY_RATE_LIMITS.md` - Rate limiting strategy and monthly usage projections
- `docs/PRODUCTION_PLAN.md` - Full data collection strategy
- `docs/PIPELINE_DESIGN.md` - Bronze-silver-gold architecture
- `MAJOR_DISCOVERY_46_CSUs.md` - Compound V3 architecture discovery

---

## 🚧 What Needs to Be Built (Next Steps)

### 1. Block Cache Builder ⏰ Priority: HIGH

**File to create:** `scripts/build_block_cache.py` (already exists, needs testing)

**Purpose:** Pre-compute date→block mappings for December 2024

**Why:** Avoids repeated RPC calls during collection. Date-to-block conversion uses binary search which is expensive.

**Usage:**
```bash
python3 scripts/build_block_cache.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --chains ethereum arbitrum base optimism
```

**Output:** JSON files in `data/cache/` like:
```json
{
  "2024-12-01": {
    "block": 21400123,
    "timestamp": 1701388800,
    "ts_start_utc": 1701388800,
    "ts_end_utc": 1701475200
  }
}
```

### 2. Parallel TVL Collector ⏰ Priority: HIGH

**File to create:** `scripts/collect_tvl_parallel.py`

**Purpose:** Collect TVL snapshots for all 43 CSUs across December 2024

**Requirements:**
- Use ThreadPoolExecutor with 5 workers
- Load block cache (don't recompute blocks)
- Save to bronze format: `data/bronze/tvl/{csu_name}/{date}.json`
- Checkpoint/resume on failures
- Progress monitoring

**Collection Strategy:**
- 43 CSUs × 31 days = 1,333 tasks
- 1 RPC call per task (snapshot at end-of-day block)
- Total time: ~30 seconds with rate limiting

**Bronze Output Format:**
```json
{
  "csu": "aave_v3_ethereum",
  "chain": "ethereum",
  "family": "aave_v3",
  "date": "2024-12-31",
  "block": 21556789,
  "timestamp": "2025-01-08T12:00:00Z",
  "num_markets": 42,
  "data": [
    {
      "reserve": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "symbol": "USDC",
      "decimals": 6,
      "aToken": "0x...",
      "total_supplied_raw": 5000000000000,
      "total_borrowed_raw": 3000000000000
    }
  ]
}
```

### 3. Parallel Liquidation Collector ⏰ Priority: MEDIUM

**File to create:** `scripts/collect_liquidations_parallel.py`

**Purpose:** Collect liquidation events for CSUs across December 2024

**Requirements:**
- Chunk scanning into 10-block windows (eth_getLogs limited to 10 blocks)
- 1 day = ~7,200 blocks = 720 chunks per CSU
- Use ThreadPoolExecutor to parallelize chunks
- Save to bronze format: `data/bronze/liquidations/{csu_name}/{date}.json`
- Checkpoint/resume critical (long-running)

**Challenge:** This is the expensive operation
- 43 CSUs × 31 days × 720 calls = **960,480 RPC calls**
- At 10 calls/sec per key = **~12-15 hours** with 5 workers

**IMPORTANT:** Start with Aave V3 + Compound V3 only (31 CSUs) to stay closer to free tier monthly limits.

**Bronze Output Format:**
```json
{
  "csu": "aave_v3_ethereum",
  "date": "2024-12-31",
  "block_range": [21550000, 21557200],
  "num_events": 15,
  "events": [
    {
      "tx_hash": "0x...",
      "block_number": 21556789,
      "log_index": 42,
      "liquidator": "0x...",
      "borrower": "0x...",
      "collateral_asset": "0x...",
      "debt_asset": "0x...",
      "collateral_amount_raw": 1000000000000000000,
      "debt_repaid_raw": 500000000000000000
    }
  ]
}
```

### 4. Progress Monitor ⏰ Priority: LOW (Nice to have)

**File to create:** `scripts/monitor_progress.py`

**Purpose:** Show collection status in real-time

**Features:**
- Check checkpoint file
- Show completed vs remaining tasks
- Estimate time remaining
- Identify failures

**Usage:**
```bash
python3 scripts/monitor_progress.py
```

**Output:**
```
Collection Progress: December 2024
============================================================
TVL Collection:
  Completed: 1,200/1,333 (90%)
  Failed: 5
  Remaining: 128
  Est. time: 15 seconds

Liquidation Collection:
  Completed: 500/1,333 (37.5%)
  Failed: 12
  Remaining: 821
  Est. time: 8 hours 15 minutes
```

---

## 📐 Architecture & File Structure

### Current Structure
```
thesis_v2/
├── config/
│   ├── csu_config.yaml          # All 43 CSU definitions
│   ├── rpc_pool.py              # Multi-account RPC with rate limiting
│   ├── rpc_config.py            # Original config (still works)
│   └── utils/
│       ├── time.py              # NY timezone utilities
│       └── block.py             # Block-by-timestamp binary search
│
├── adapters/
│   ├── tvl/                     # TVL adapters (43 CSUs)
│   │   ├── aave_v3.py
│   │   ├── compound_v3.py
│   │   ├── compound_v2_style.py
│   │   ├── fluid.py
│   │   ├── venus.py
│   │   ├── gearbox.py
│   │   ├── lista.py
│   │   └── cap.py
│   │
│   └── liquidations/            # Liquidation adapters (matching structure)
│       ├── aave_v3.py
│       ├── compound_v3.py
│       └── ...
│
├── scripts/
│   ├── test_all_csus.py         # ✅ Test all CSUs
│   ├── test_single_csu.py       # ✅ Test one CSU
│   ├── test_single_day.py       # ✅ Test historical collection
│   ├── test_key_mapping.py      # ✅ Verify key-chain mapping
│   ├── build_block_cache.py     # ✅ EXISTS - needs testing
│   ├── collect_tvl_parallel.py      # 🚧 TO BUILD
│   ├── collect_liquidations_parallel.py  # 🚧 TO BUILD
│   └── monitor_progress.py      # 🚧 TO BUILD (optional)
│
├── data/
│   ├── cache/                   # Date→block mappings (create via build_block_cache.py)
│   │   ├── ethereum_blocks_2024-12-01_2024-12-31.json
│   │   └── ...
│   │
│   ├── bronze/                  # Raw blockchain data (create via collectors)
│   │   ├── tvl/
│   │   │   └── {csu_name}/
│   │   │       └── {date}.json
│   │   └── liquidations/
│   │       └── {csu_name}/
│   │           └── {date}.json
│   │
│   ├── silver/                  # Cleaned/normalized (future)
│   │   ├── tvl/
│   │   └── liquidations/
│   │
│   └── gold/                    # Analysis-ready panel (future)
│       └── daily_panel.parquet
│
└── docs/
    ├── ALCHEMY_RATE_LIMITS.md   # Rate limiting constraints
    ├── PRODUCTION_PLAN.md        # Full collection strategy
    └── PIPELINE_DESIGN.md        # Architecture decisions
```

---

## ⚠️ Critical Constraints

### Alchemy Free Tier Limits

**Per Account:**
- 300 compute units/second (CUs)
- 3 million CUs/month

**Our Usage:**
- eth_call: ~26 CUs (TVL collection)
- eth_getLogs: ~75 CUs (liquidation collection)

**Monthly Projections:**
- **TVL collection:** ~35,000 CUs total (0.001% of monthly limit) ✅
- **Liquidation collection:** ~72 million CUs total (exceeds limit by 5x) ⚠️

**Solution:** Start with TVL + priority liquidations (Aave V3 + Compound V3 only = 31 CSUs instead of 43)

### Rate Limiting Strategy

**Current Config:** 10 calls/sec per key
- Conservative to avoid bans
- Provides headroom for burst traffic
- Can be increased if accounts upgraded to Growth tier

### Collection Timeline

**Phase 1: TVL (Fast & Safe)**
- All 43 CSUs × 31 days
- ~1,333 calls total
- Time: ~1 hour
- Cost: ~35K CUs (well within free tier)

**Phase 2: Liquidations (Slower & Expensive)**
- Option A: All 43 CSUs = exceeds monthly limits
- Option B: Aave V3 + Compound V3 only (31 CSUs) = closer to limits
- Time: ~8-12 hours (with rate limiting)
- Cost: ~52-72M CUs (may exceed free tier)

---

## 🔄 Intended Workflow with Claude Code

### High-Level Workflow

**You:** Define what to build + constraints
**Claude Code:** Writes code, runs tests, iterates
**You:** Review results, provide feedback, guide direction

### Development Cycle

1. **Specification Phase** (You)
   - Describe what needs to be built
   - Provide constraints (rate limits, output format)
   - Share relevant context (this document, existing code)

2. **Implementation Phase** (Claude Code)
   - Writes the code
   - Runs it to test
   - Fixes errors automatically
   - Iterates until working

3. **Review Phase** (You)
   - Test the output
   - Check data quality
   - Provide feedback if adjustments needed

4. **Refinement Phase** (Claude Code)
   - Makes adjustments based on feedback
   - Adds error handling, logging
   - Optimizes performance

### Best Practices for Claude Code

**✅ DO:**
- Give clear, specific tasks: "Build a parallel TVL collector that..."
- Share this context document at start of session
- Let Claude Code run and test code autonomously
- Provide feedback on outputs, not implementation details
- Ask for explanation of design decisions

**❌ DON'T:**
- Micromanage implementation details
- Interrupt mid-iteration
- Provide partial context (share full context each session)
- Assume Claude Code remembers previous sessions

### Example Interactions

**Good:**
```
You: "Build a parallel TVL collector for December 2024. Requirements:
- Use ThreadPoolExecutor with 5 workers
- Load block cache from data/cache/
- Save bronze data to data/bronze/tvl/{csu}/{date}.json
- Add checkpoint/resume for failures
- Respect rate limiting from rpc_pool.py
Here's the context: [share this document]"

Claude Code: [writes code, tests, shows results]
```

**Also Good:**
```
You: "The TVL collector is working but it's not loading the block cache 
correctly. It's recomputing blocks every time which is slow."

Claude Code: [analyzes code, fixes the caching logic, tests]
```

**Not Ideal:**
```
You: "Change line 42 to use json.load instead of json.loads"

Better: "The block cache loading is failing with a JSON error. Can you debug?"
```

### Session Structure

**Start of Session:**
```
1. Share this context document
2. Point to relevant existing code
3. Describe the goal
4. Let Claude Code work
```

**During Session:**
```
- Let Claude Code run tests autonomously
- Provide feedback on results
- Answer clarifying questions
- Guide overall direction
```

**End of Session:**
```
- Review what was built
- Test outputs manually
- Document any issues for next session
- Commit working code to GitHub
```

---

## 🎯 Immediate Next Task for Claude Code

### Task: Build Block Cache

**Goal:** Create date→block mappings for December 2024 to avoid repeated RPC calls during collection.

**File:** `scripts/build_block_cache.py` (already exists, needs testing)

**Test Command:**
```bash
python3 scripts/build_block_cache.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --chains ethereum arbitrum base optimism
```

**Expected Output:**
- 4 JSON files in `data/cache/`
- Each file has 31 date→block mappings
- Takes ~3-5 minutes to complete
- No errors

**Success Criteria:**
- ✅ Files created in data/cache/
- ✅ Each date has correct block number
- ✅ Block timestamps verify correct day
- ✅ No RPC errors or timeouts

**If Successful, Next Task:**
Build the parallel TVL collector using the cached blocks.

---

## 📚 Key References

### Existing Code to Reference

**For RPC connections:**
- `config/rpc_pool.py` - Use `get_web3(chain)` function

**For adapters:**
- `adapters/tvl/aave_v3.py` - Example TVL adapter
- `scripts/test_single_day.py` - Shows how to call adapters

**For time/block utilities:**
- `config/utils/time.py` - Use `ny_date_to_utc_window()`
- `config/utils/block.py` - Use `block_for_ts()`

**For CSU configs:**
- `config/csu_config.yaml` - All 43 CSU definitions

### Critical Functions

```python
# Get Web3 connection (with rate limiting)
from config.rpc_pool import get_web3
w3 = get_web3('ethereum')

# Get date→block (from cache or compute)
from config.utils.time import ny_date_to_utc_window
from config.utils.block import block_for_ts
ts_start, ts_end = ny_date_to_utc_window('2024-12-31')
block = block_for_ts(w3, ts_end)

# Call TVL adapter
from adapters.tvl.aave_v3 import get_aave_v3_tvl
data = get_aave_v3_tvl(w3, registry_address, block_number)
```

---

## 🔐 Security Reminder

**NEVER commit to GitHub:**
- `.env` file (has API keys)
- `data/` directory (large, regenerable)
- Any file with actual API keys in code

**Always verify before pushing:**
```bash
git status  # Check what will be committed
# Make sure .env is NOT in the list
```

---

## 📊 Progress Tracking

**Current Status:** Infrastructure complete, ready for data collection

**Completed:**
- ✅ 43 CSU adapters (TVL + liquidations)
- ✅ Multi-account RPC pool with rate limiting
- ✅ Testing infrastructure
- ✅ Block cache builder script (exists, needs testing)

**In Progress:**
- 🚧 Testing block cache builder
- 🚧 Building parallel collectors

**Not Started:**
- ⏸️ Silver processing (clean/normalize data)
- ⏸️ Gold aggregation (daily panel)
- ⏸️ Analysis/modeling

**Estimated Timeline:**
- Block cache: ~1 hour to test and verify
- TVL collector: ~2-4 hours to build and test
- TVL collection: ~1 hour to run
- Liquidation collector: ~4-6 hours to build and test
- Liquidation collection: ~12-15 hours to run

**Total to complete bronze collection:** ~2-3 days

---

## 💡 Summary for Claude Code

**What we have:**
- 43 working protocol adapters
- Multi-account RPC with rate limiting
- Complete testing infrastructure
- Bronze-silver-gold pipeline design

**What we need:**
- Test/fix block cache builder
- Build parallel TVL collector
- Build parallel liquidation collector
- Collect December 2024 data

**Constraints:**
- Rate limiting: 10 calls/sec per key
- Monthly CU limits on free tier
- 10-block limit on eth_getLogs

**First task:**
Test the block cache builder and ensure it works correctly.

**After that:**
Build the parallel TVL collector using the cached blocks.

---

## 🚀 Let's Build!

This context should be sufficient for Claude Code to understand the project and start building. Share this document at the start of each Claude Code session for best results.

**Ready to start with block cache testing?**
