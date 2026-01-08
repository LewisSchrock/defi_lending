# Setup Instructions - 5 Alchemy Accounts

## You Have: 5 Alchemy Accounts ✅

Perfect! This gives you ~5x the rate limits (500 calls/sec distributed).

---

## Step 1: Set Environment Variables

Create a file to store your API keys (don't commit to git!):

```bash
cd ~/Desktop/Academics/thesis_v2/

# Create .env file
cat > .env << 'EOF'
# Alchemy API Keys (5 accounts)
export ALCHEMY_KEY_1='alch_your_first_key_here'
export ALCHEMY_KEY_2='alch_your_second_key_here'
export ALCHEMY_KEY_3='alch_your_third_key_here'
export ALCHEMY_KEY_4='alch_your_fourth_key_here'
export ALCHEMY_KEY_5='alch_your_fifth_key_here'
EOF

# Load keys into current session
source .env
```

**Important:** Add `.env` to your `.gitignore`!

```bash
echo ".env" >> .gitignore
```

---

## Step 2: Test RPC Connections

Verify all chains work with your accounts:

```bash
python3 config/rpc_pool.py
```

**Expected output:**
```
Testing RPC Connections
============================================================

[RPC Pool] ethereum: 5 Alchemy connections
[RPC Pool] ethereum: Connection OK (block 21234567)
[RPC Pool] arbitrum: 5 Alchemy connections
[RPC Pool] arbitrum: Connection OK (block 285678901)
...

Summary
============================================================
✅ ethereum
✅ arbitrum
✅ optimism
✅ base
✅ polygon
✅ avalanche
✅ binance
✅ plasma
✅ linea
✅ gnosis
✅ ink
✅ cronos
✅ flare
✅ meter

Working: 14/14 chains
```

**If any fail:**
- Check that all 4 accounts have that chain enabled in Alchemy dashboard
- Verify API keys are correct
- Try Plasma fix if it fails: Change `polygonzkevm-mainnet` to `plasma-mainnet` in `config/rpc_pool.py`

---

## Step 3: Build Block Cache for December 2024

Pre-compute date→block mappings for Dec 1-31:

```bash
python3 scripts/build_block_cache.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --chains ethereum arbitrum base optimism
```

**What this does:**
- Computes snapshot block for each day (31 days × 4 chains = 124 mappings)
- Uses binary search to find exact block
- Saves to `data/cache/ethereum_blocks_2024-12-01_2024-12-31.json`
- Takes ~2-3 minutes

**Output files:**
```
data/cache/
├── ethereum_blocks_2024-12-01_2024-12-31.json
├── arbitrum_blocks_2024-12-01_2024-12-31.json
├── base_blocks_2024-12-01_2024-12-31.json
└── optimism_blocks_2024-12-01_2024-12-31.json
```

---

## Step 4: Test Single Day Collection

Collect TVL for Aave V3 Ethereum on Dec 31:

```bash
python3 scripts/test_single_day.py \
  --csu aave_v3_ethereum \
  --date 2024-12-31
```

**Expected output:**
```
============================================================
Collecting TVL: aave_v3_ethereum on 2024-12-31
============================================================

CSU: aave_v3_ethereum
Chain: ethereum
Registry: 0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e
Family: aave_v3
Date: 2024-12-31

Connecting to RPC...
✅ Connected: latest block = 21567890

Getting snapshot block...
   Using cached block: 21556789
✅ Snapshot block: 21556789

Collecting TVL data...
✅ Collected 42 markets/reserves

Sample data (first reserve/market):
{
  "reserve": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "symbol": "USDC",
  "decimals": 6,
  "aToken": "0x...",
  "total_supplied_raw": 5000000000000,
  "total_borrowed_raw": 3000000000000,
  ...
}

✅ Saved to: data/bronze/tvl/aave_v3_ethereum/2024-12-31.json
   File size: 12.3 KB

============================================================
✅ Collection successful!
============================================================
```

**Verify the file:**
```bash
cat data/bronze/tvl/aave_v3_ethereum/2024-12-31.json | jq
```

---

## Step 5: Check Data Quality

Look at the collected data:

```bash
cat data/bronze/tvl/aave_v3_ethereum/2024-12-31.json | jq '.data[0]'
```

**What to check:**
- ✅ `total_supplied_raw` is a large number (not 0)
- ✅ `total_borrowed_raw` is less than supplied
- ✅ `symbol` is correct (USDC, WETH, etc.)
- ✅ `decimals` matches token (6 for USDC, 18 for WETH)

---

## Step 6: Test Another CSU

Try a Compound V3 market:

```bash
python3 scripts/test_single_day.py \
  --csu compound_v3_eth_usdc \
  --date 2024-12-31
```

Should see similar output with Compound V3 data structure.

---

## Troubleshooting

### Issue: "No Alchemy API keys found"
**Fix:** Make sure you ran `source .env` to load the keys

```bash
# Check if keys are loaded
echo $ALCHEMY_KEY_1

# If empty, load them:
source .env
```

### Issue: "Chain not supported"
**Fix:** Check spelling of chain name in CSUS dict

### Issue: RPC timeout
**Fix:** 
- Reduce timeout pressure by testing at night
- Try different Alchemy account
- Check Alchemy dashboard for rate limit hits

### Issue: Block cache fails
**Fix:**
- Make sure RPC works first (`python3 config/rpc_pool.py`)
- Try smaller date range first (1 week)
- Binary search may take time on slow RPCs

---

## What's Next?

Once Steps 1-6 work:

### Option A: Manual Batch Collection
Collect all of Dec 2024 for critical CSUs:

```bash
# Ethereum protocols (highest priority)
for date in 2024-12-{01..31}; do
  python3 scripts/test_single_day.py --csu aave_v3_ethereum --date $date
  python3 scripts/test_single_day.py --csu compound_v3_eth_usdc --date $date
done
```

### Option B: I Build Parallel Collector
I create `scripts/collect_parallel.py` with:
- ThreadPoolExecutor (5 workers)
- Checkpoint/resume logic
- Progress monitoring
- Handles all 43 CSUs automatically

### Option C: Both
- You start manual collection for Ethereum protocols now
- I build parallel collector in parallel
- You can kill manual and switch to automated once ready

---

## Quick Start Commands

```bash
# 1. Load API keys
cd ~/Desktop/Academics/thesis_v2/
source .env

# 2. Test connections
python3 config/rpc_pool.py

# 3. Build block cache
python3 scripts/build_block_cache.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --chains ethereum arbitrum base optimism

# 4. Test single day
python3 scripts/test_single_day.py \
  --csu aave_v3_ethereum \
  --date 2024-12-31

# 5. Check output
cat data/bronze/tvl/aave_v3_ethereum/2024-12-31.json | jq
```

---

## Expected Timeline

| Step | Time |
|------|------|
| 1. Set env vars | 2 mins |
| 2. Test RPCs | 1 min |
| 3. Build block cache | 2-3 mins |
| 4. Test single day | 30 secs |
| 5-6. Verify data | 2 mins |
| **Total** | **~10 mins** |

---

## Ready?

Run through Steps 1-6 and let me know:
- ✅ All RPCs working?
- ✅ Block cache built?
- ✅ Single day test successful?

Then I'll build the parallel collector!
