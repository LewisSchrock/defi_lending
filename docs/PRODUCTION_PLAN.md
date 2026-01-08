# Production Data Collection Plan - Dec 31 → Nov 30

## Overview

**Target:** Collect 31 days (Dec 1-31, 2024) for 43 working CSUs
**Test Protocol:** aave_v3_ethereum
**Workers:** 5 parallel
**Pricing:** On-chain oracles (Chainlink, protocol-specific)

---

## Critical Constraints Addressed

### 1. **10 Blocks Per Call Limitation**

**Problem:** eth_getLogs limited to 10 blocks per call
**Impact:** Liquidation scanning is expensive

**Math for Ethereum (12s blocks):**
- 1 day = 7,200 blocks
- 10 blocks/call = 720 RPC calls per CSU per day
- 43 CSUs × 31 days × 720 calls = **960,480 calls for liquidations alone**

**Solution:**
```python
# Chunk liquidation scanning into 10-block windows
def scan_liquidations_for_day(csu, date):
    start_block = date_to_block(date + " 00:00:00 UTC")
    end_block = date_to_block(date + " 23:59:59 UTC")
    
    chunks = []
    for block_start in range(start_block, end_block, 10):
        block_end = min(block_start + 9, end_block)
        chunks.append((block_start, block_end))
    
    # 720 chunks per day for Ethereum
    # Parallelize these chunks across workers
    return chunks
```

**Optimization:**
- TVL: Only 1 call per day per CSU (snapshot at midnight)
- Liquidations: Parallelize 10-block chunks across workers

---

### 2. **Multiple Alchemy Accounts Strategy**

**Setup:**
```python
# Create connection pool with multiple API keys
ALCHEMY_KEYS = [
    'key1_from_account1',
    'key2_from_account2', 
    'key3_from_account3',
    # Add more as needed
]

class AlchemyConnectionPool:
    def __init__(self, keys, chain):
        self.providers = [
            Web3(Web3.HTTPProvider(
                f'https://{chain}-mainnet.g.alchemy.com/v2/{key}'
            )) for key in keys
        ]
        self.current_idx = 0
        self.lock = threading.Lock()
    
    def get_connection(self):
        """Round-robin across API keys"""
        with self.lock:
            w3 = self.providers[self.current_idx]
            self.current_idx = (self.current_idx + 1) % len(self.providers)
            return w3
```

**Benefits:**
- Distributes load across accounts
- Avoids rate limits on single key
- ~3x capacity if you have 3 accounts

---

### 3. **Public RPC Fallbacks**

**Current public RPCs are unreliable.** Need better alternatives:

```python
# Fallback RPC providers (ordered by reliability)
FALLBACK_RPCS = {
    'ethereum': [
        'https://eth.llamarpc.com',
        'https://rpc.ankr.com/eth',
        'https://eth.drpc.org',
        'https://ethereum.publicnode.com',
    ],
    'arbitrum': [
        'https://arb1.arbitrum.io/rpc',
        'https://arbitrum.llamarpc.com',
    ],
    'optimism': [
        'https://mainnet.optimism.io',
        'https://optimism.llamarpc.com',
    ],
    'flare': [
        'https://flare-api.flare.network/ext/C/rpc',
        'https://flare.solidifi.app/ext/bc/C/rpc',
    ],
    # etc.
}

class ResilientWeb3:
    def __init__(self, chain, alchemy_keys):
        self.alchemy_pool = AlchemyConnectionPool(alchemy_keys, chain)
        self.fallbacks = [Web3(Web3.HTTPProvider(url)) 
                         for url in FALLBACK_RPCS.get(chain, [])]
    
    def call_with_fallback(self, func, *args, **kwargs):
        # Try Alchemy first
        try:
            w3 = self.alchemy_pool.get_connection()
            return func(w3, *args, **kwargs)
        except Exception as e:
            # Try fallbacks
            for w3 in self.fallbacks:
                try:
                    return func(w3, *args, **kwargs)
                except:
                    continue
            raise Exception(f"All RPCs failed: {e}")
```

---

### 4. **SSH Multi-Computer Distribution**

**Architecture:** Coordinator + Workers

```
┌─────────────────┐
│  Main Computer  │  ← Coordinator (you)
│  (Coordinator)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Worker1│ │Worker2│  ← College lab machines via SSH
│SSH    │ │SSH    │
└───────┘ └───────┘
```

**Coordinator Script:**
```python
# Main computer - distributes work
import paramiko

WORKERS = [
    {'host': 'lab1.college.edu', 'user': 'lewisschrock'},
    {'host': 'lab2.college.edu', 'user': 'lewisschrock'},
    {'host': 'lab3.college.edu', 'user': 'lewisschrock'},
    {'host': 'lab4.college.edu', 'user': 'lewisschrock'},
    {'host': 'lab5.college.edu', 'user': 'lewisschrock'},
]

def distribute_work(tasks):
    """Distribute CSU×date tasks across SSH workers"""
    chunks = np.array_split(tasks, len(WORKERS))
    
    for worker, chunk in zip(WORKERS, chunks):
        ssh = paramiko.SSHClient()
        ssh.connect(worker['host'], username=worker['user'])
        
        # Upload task list
        ssh.exec_command(f'python3 worker.py --tasks {chunk}')
```

**Worker Script** (runs on each lab machine):
```python
# worker.py - runs on remote machine
import sys
sys.path.append('/path/to/thesis_v2')

from collectors.tvl_collector import collect_tvl_day
from collectors.liq_collector import collect_liquidations_day

def process_task(task):
    csu, date = task['csu'], task['date']
    
    # Collect TVL (1 call)
    tvl_data = collect_tvl_day(csu, date)
    save_bronze(tvl_data, f'data/bronze/tvl/{csu}/{date}.json')
    
    # Collect liquidations (720 calls for Ethereum)
    liq_data = collect_liquidations_day(csu, date)
    save_bronze(liq_data, f'data/bronze/liquidations/{csu}/{date}.json')

if __name__ == '__main__':
    tasks = load_tasks(sys.argv[1])
    for task in tasks:
        process_task(task)
```

**Alternative: Simple Parallel (No SSH)**
If SSH is complex, just use local ThreadPoolExecutor:

```python
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(collect_day, csu, date) 
               for csu, date in tasks]
```

---

### 5. **On-Chain Oracle Pricing**

**Strategy:** Query protocol's own oracle at snapshot block

```python
# Chainlink oracle interface
CHAINLINK_ORACLE_ABI = [
    {
        "name": "latestAnswer",
        "outputs": [{"type": "int256"}],
        "stateMutability": "view",
        "type": "function",
    }
]

def get_onchain_price(w3, token_address, block_number):
    """Get price from protocol's oracle at specific block"""
    
    # 1. Try Chainlink feed (most common)
    chainlink_feeds = {
        '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': '0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6',  # USDC
        '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2': '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',  # WETH
        # Add more token → feed mappings
    }
    
    if token_address in chainlink_feeds:
        feed = w3.eth.contract(
            address=chainlink_feeds[token_address],
            abi=CHAINLINK_ORACLE_ABI
        )
        try:
            price = feed.functions.latestAnswer().call(block_identifier=block_number)
            return price / 1e8  # Chainlink uses 8 decimals
        except:
            pass
    
    # 2. Try protocol's oracle (Aave, Compound, etc.)
    # Each protocol has different oracle structure
    
    # 3. Fallback: mark as missing, fill later
    return None
```

**Oracle Mapping by Protocol:**

| Protocol | Oracle Type | Contract |
|----------|-------------|----------|
| Aave V3 | Aave Oracle | Query via PoolAddressProvider |
| Compound V3 | Comet Price Feed | `comet.getAssetInfo(i).priceFeed` |
| Fluid | Custom | Check docs |

**Pragmatic Approach:**
- Try on-chain oracle first
- Log missing prices
- Fill gaps later with DefiLlama historical API (has generous limits)

---

### 6. **Date to Block Conversion**

**Using your existing code:**

```python
# From config/utils/time.py and config/utils/block.py
from config.utils.time import ny_date_to_utc_window
from config.utils.block import block_for_ts

def get_snapshot_block(w3, date_str):
    """
    Get block for end-of-day snapshot (NY midnight)
    
    Example: '2024-12-31' → block ~21,500,000
    """
    ts_start_utc, ts_end_utc = ny_date_to_utc_window(date_str)
    
    # Snapshot at END of day (NY midnight next day)
    block_num = block_for_ts(w3, ts_end_utc)
    
    # Safety: subtract 1 to ensure block is from target day
    return max(1, block_num - 1)
```

**Optimization:** Cache date→block mappings

```python
# Create lookup table once
DATE_TO_BLOCK_CACHE = {}

def build_block_cache(w3, dates):
    """Pre-compute all date→block mappings"""
    for date in dates:
        DATE_TO_BLOCK_CACHE[date] = get_snapshot_block(w3, date)
    
    # Save to file
    with open('data/block_cache.json', 'w') as f:
        json.dump(DATE_TO_BLOCK_CACHE, f)
```

---

### 7. **Liquidation Scanning Strategy**

**Challenge:** Need to scan every block (expensive)

**Chunking Strategy:**

```python
def get_liquidation_chunks(start_block, end_block, chunk_size=10):
    """Split day into 10-block chunks for parallel processing"""
    chunks = []
    for block in range(start_block, end_block + 1, chunk_size):
        chunk_end = min(block + chunk_size - 1, end_block)
        chunks.append((block, chunk_end))
    return chunks

# Example for Dec 31, 2024 on Ethereum
# start_block = 21,490,000
# end_block = 21,497,200
# chunks = [(21490000, 21490009), (21490010, 21490019), ..., (21497191, 21497200)]
# Total: 720 chunks
```

**Parallel Processing:**

```python
def collect_liquidations_parallel(csu, date, num_workers=5):
    w3 = get_web3(csu['chain'])
    
    start_block = DATE_TO_BLOCK_CACHE[date]
    end_block = DATE_TO_BLOCK_CACHE[date] + 7200  # ~1 day
    
    chunks = get_liquidation_chunks(start_block, end_block, chunk_size=10)
    
    # Parallelize across workers
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(scan_chunk, csu, chunk_start, chunk_end)
            for chunk_start, chunk_end in chunks
        ]
        
        results = [f.result() for f in futures]
    
    # Combine all liquidations from all chunks
    all_liquidations = []
    for result in results:
        all_liquidations.extend(result)
    
    return all_liquidations
```

---

## Phased Execution Plan

### Phase 1: Infrastructure Setup (1 hour)

**Goal:** Get multi-account RPC working

```bash
# 1. Set up multiple Alchemy keys
export ALCHEMY_KEY_1='key1'
export ALCHEMY_KEY_2='key2'
export ALCHEMY_KEY_3='key3'

# 2. Test connection pool
python scripts/test_rpc_pool.py

# 3. Build date→block cache for Dec 1-31
python scripts/build_block_cache.py --start-date 2024-12-01 --end-date 2024-12-31
```

**Deliverable:** 
- `config/rpc_pool.py` - Connection pool manager
- `data/block_cache_dec2024.json` - 31 date→block mappings

---

### Phase 2: Single CSU, Single Day Test (30 mins)

**Goal:** Validate TVL + liquidations work for aave_v3_ethereum on Dec 31

```bash
python scripts/collect_single_day.py \
  --csu aave_v3_ethereum \
  --date 2024-12-31 \
  --include-tvl \
  --include-liquidations
```

**Expected Output:**
```
data/bronze/tvl/aave_v3_ethereum/2024-12-31.json        (1 file, <1KB)
data/bronze/liquidations/aave_v3_ethereum/2024-12-31.json  (1 file, varies)
```

**Verify:**
- TVL data has all reserves
- Liquidations captured (if any occurred)
- On-chain prices present
- No RPC errors

---

### Phase 3: Single CSU, Full Month (2 hours)

**Goal:** Collect 31 days for aave_v3_ethereum

```bash
python scripts/collect_month.py \
  --csu aave_v3_ethereum \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --workers 5
```

**Expected:**
- 31 TVL files
- 31 liquidation files
- ~22,320 RPC calls for liquidations (720/day × 31 days)
- ~5 minutes with 5 workers

**Monitor:**
```bash
# Check progress
python scripts/monitor_progress.py --csu aave_v3_ethereum

# Output:
# Dec 1: ✅ TVL + Liquidations
# Dec 2: ✅ TVL + Liquidations
# ...
# Dec 31: ✅ TVL + Liquidations
```

---

### Phase 4: All CSUs, Full Month (8-12 hours)

**Goal:** Collect 43 CSUs × 31 days

```bash
python scripts/collect_all_csus.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --workers 5 \
  --resume  # Resume from checkpoint if interrupted
```

**Task Distribution:**
- 43 CSUs × 31 days = 1,333 tasks
- 5 workers = ~267 tasks per worker
- TVL: 1,333 calls (~2 minutes)
- Liquidations: ~960,000 calls (~8-10 hours)

**Optimizations:**
1. Prioritize high-TVL protocols (Aave, Compound)
2. Skip days with no activity (check block range first)
3. Cache repeated queries (token decimals, symbols)

---

### Phase 5: Incremental Extension (ongoing)

Once Dec 2024 works, extend backwards:

```bash
# Nov 2024
python scripts/collect_all_csus.py --start-date 2024-11-01 --end-date 2024-11-30

# Oct 2024
python scripts/collect_all_csus.py --start-date 2024-10-01 --end-date 2024-10-31

# Continue until blocker
```

---

## Performance Estimates

### TVL Collection (Fast)
- **1 CSU, 1 day:** 1 RPC call, <1 second
- **1 CSU, 31 days:** 31 calls, ~5 seconds
- **43 CSUs, 31 days:** 1,333 calls, ~2 minutes

### Liquidation Collection (Slow)
- **1 CSU, 1 day (Ethereum):** 720 calls, ~2 minutes (with 5 workers)
- **1 CSU, 31 days:** 22,320 calls, ~45 minutes
- **43 CSUs, 31 days:** 960,480 calls, **~8-10 hours**

### Total Time (Dec 2024)
- **Sequential:** ~24 hours
- **Parallel (5 workers):** **~8-10 hours**
- **Parallel (10 workers + multi-account):** **~4-5 hours**

---

## Storage Requirements

### Bronze (Raw JSON)
- **TVL:** 1,333 files × 10KB = ~13 MB
- **Liquidations:** 1,333 files × 50KB = ~65 MB
- **Total Bronze:** ~80 MB

### Silver (Parquet)
- **TVL:** ~20 MB (compressed)
- **Liquidations:** ~30 MB (compressed)
- **Total Silver:** ~50 MB

### Gold (Panel)
- **Daily aggregated:** ~5 MB

**Total for Dec 2024:** ~135 MB (easily fits in thesis_v2/data/)

---

## Error Handling & Checkpointing

**Checkpoint File:**
```json
{
  "last_updated": "2025-01-07T18:00:00Z",
  "completed_tasks": [
    {"csu": "aave_v3_ethereum", "date": "2024-12-01", "tvl": true, "liquidations": true},
    {"csu": "aave_v3_ethereum", "date": "2024-12-02", "tvl": true, "liquidations": false},
  ],
  "failed_tasks": [
    {"csu": "kinetic_flare", "date": "2024-12-15", "error": "RPC timeout"}
  ]
}
```

**Resume Logic:**
```python
def load_checkpoint():
    if os.path.exists('data/checkpoint.json'):
        with open('data/checkpoint.json') as f:
            return json.load(f)
    return {'completed_tasks': [], 'failed_tasks': []}

def is_completed(csu, date, data_type):
    checkpoint = load_checkpoint()
    for task in checkpoint['completed_tasks']:
        if task['csu'] == csu and task['date'] == date:
            return task.get(data_type, False)
    return False

# Skip already completed tasks
if is_completed(csu, date, 'tvl'):
    print(f"Skipping {csu} {date} TVL (already done)")
```

---

## What I'll Build Next

Based on your existing code, I'll create:

### 1. **RPC Connection Pool** (`config/rpc_pool.py`)
- Multi-account Alchemy rotation
- Fallback RPC providers
- Rate limiting per provider

### 2. **Block Cache Builder** (`scripts/build_block_cache.py`)
- Pre-compute date→block for date range
- Save to JSON for fast lookups

### 3. **On-Chain Price Fetcher** (`utils/onchain_pricing.py`)
- Chainlink oracle queries
- Protocol-specific oracle support
- Missing price logging

### 4. **Parallel Collector** (`scripts/collect_all_csus.py`)
- ThreadPoolExecutor with 5 workers
- Checkpoint/resume logic
- Progress monitoring

### 5. **Monitor Dashboard** (`scripts/monitor_progress.py`)
- Show completion status
- Identify failures
- Estimate time remaining

---

## Immediate Next Steps

Tell me:

1. **How many Alchemy accounts** do you have? (Determines pool size)
2. **SSH access:** Do you want to use college lab machines, or keep it simple with local ThreadPoolExecutor?
3. **Start immediately with Phase 1** (infrastructure setup)?

I'll build the RPC pool and block cache first, then we test on aave_v3_ethereum for Dec 31!
