# Setup Package - Quick Reference

## 📦 What's in This Package

### New Files (Infrastructure)

1. **config/rpc_pool.py** - Multi-account RPC connection pool
   - Rotates across 5 Alchemy accounts
   - Supports all 14 chains
   - Thread-safe for parallel workers

2. **scripts/build_block_cache.py** - Date→block pre-computation
   - Builds cache for date range
   - Saves time during collection
   - Uses binary search

3. **scripts/test_single_day.py** - Single day test collector
   - Tests one CSU on one date
   - Validates entire pipeline
   - Shows sample output

4. **SETUP_INSTRUCTIONS.md** - Complete setup guide
   - Step-by-step instructions
   - All 6 steps with examples
   - Troubleshooting included

5. **docs/PRODUCTION_PLAN.md** - Full production plan
   - Addresses all your constraints
   - 10-block limitation strategy
   - SSH distribution option
   - On-chain oracle pricing
   - Timeline estimates

---

## 🚀 Quick Start (10 Minutes)

### Step 1: Extract & Navigate
```bash
cd ~/Desktop/Academics/
unzip thesis_v2_RPC_SETUP.zip
cd thesis_v2/
```

### Step 2: Set API Keys
```bash
# Create .env file with your 5 Alchemy keys
cat > .env << 'EOF'
export ALCHEMY_KEY_1='alch_your_key_1'
export ALCHEMY_KEY_2='alch_your_key_2'
export ALCHEMY_KEY_3='alch_your_key_3'
export ALCHEMY_KEY_4='alch_your_key_4'
export ALCHEMY_KEY_5='alch_your_key_5'
EOF

# Load keys
source .env

# Add to gitignore
echo ".env" >> .gitignore
```

### Step 3: Test Connections (1 min)
```bash
python3 config/rpc_pool.py
```

Expected: `Working: 14/14 chains`

### Step 4: Build Block Cache (3 mins)
```bash
python3 scripts/build_block_cache.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --chains ethereum arbitrum base optimism
```

Expected: 4 cache files in `data/cache/`

### Step 5: Test Collection (30 secs)
```bash
python3 scripts/test_single_day.py \
  --csu aave_v3_ethereum \
  --date 2024-12-31
```

Expected: `data/bronze/tvl/aave_v3_ethereum/2024-12-31.json`

### Step 6: Verify Data
```bash
cat data/bronze/tvl/aave_v3_ethereum/2024-12-31.json | jq '.data[0]'
```

Should show reserve data with large numbers for supply/borrow.

---

## ✅ Success Checklist

- [ ] All 5 API keys loaded (`echo $ALCHEMY_KEY_1` shows key)
- [ ] All 14 chains working (test_rpc output shows ✅)
- [ ] Block cache built (4 JSON files in data/cache/)
- [ ] Single day test works (JSON file created)
- [ ] Data looks reasonable (non-zero supplies/borrows)

---

## 📁 File Structure After Setup

```
thesis_v2/
├── .env                          # YOUR API KEYS (git ignored)
├── SETUP_INSTRUCTIONS.md         # Detailed setup guide
│
├── config/
│   ├── rpc_pool.py              # NEW: Multi-account RPC pool
│   ├── rpc_config.py            # Original RPC config
│   └── utils/                   # Your existing time/block utils
│       ├── time.py
│       └── block.py
│
├── scripts/
│   ├── build_block_cache.py     # NEW: Pre-compute date→block
│   ├── test_single_day.py       # NEW: Test one CSU/day
│   ├── test_all_csus.py         # Existing: Test all 43 CSUs
│   └── test_single_csu.py       # Existing: Test one CSU
│
├── data/
│   ├── cache/                    # Block cache (created by Step 4)
│   │   ├── ethereum_blocks_2024-12-01_2024-12-31.json
│   │   ├── arbitrum_blocks_2024-12-01_2024-12-31.json
│   │   ├── base_blocks_2024-12-01_2024-12-31.json
│   │   └── optimism_blocks_2024-12-01_2024-12-31.json
│   │
│   └── bronze/                   # Raw data (created by Step 5)
│       └── tvl/
│           └── aave_v3_ethereum/
│               └── 2024-12-31.json
│
├── adapters/
│   └── tvl/                      # All your existing adapters
│       ├── aave_v3.py
│       ├── compound_v3.py
│       └── ...
│
└── docs/
    ├── PRODUCTION_PLAN.md        # NEW: Full production strategy
    ├── PIPELINE_DESIGN.md        # Original design doc
    └── ...
```

---

## 🎯 What Happens Next

Once Steps 1-6 work, I will build:

### Parallel Collector (`scripts/collect_parallel.py`)
- Collects all 43 CSUs × 31 days
- Uses 5 workers (ThreadPoolExecutor)
- Checkpoint/resume on failures
- Progress monitoring
- Estimated time: ~8-10 hours for December

### Features:
```bash
python3 scripts/collect_parallel.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --workers 5 \
  --resume  # Resume from checkpoint
```

---

## 📊 Performance Expectations

### Single Day Test (Step 5)
- Time: ~30 seconds
- RPC calls: ~1 call (TVL only)
- Output: ~10-20 KB JSON

### Full Month Collection (All 43 CSUs)
- Time: ~8-10 hours
- RPC calls: ~960,000 (mostly liquidations)
- Output: ~135 MB total

### Per CSU Breakdown
- TVL: 31 days × 1 call = 31 calls (~5 seconds)
- Liquidations: 31 days × 720 calls = 22,320 calls (~45 mins)

---

## 🆘 Troubleshooting

### "No Alchemy API keys found"
```bash
source .env
echo $ALCHEMY_KEY_1  # Should show your key
```

### RPC connection fails
- Check keys are correct
- Verify chain enabled in Alchemy dashboard
- Try at different time (less congestion)

### Block cache fails
- Reduce date range (try 1 week first)
- Check RPC working: `python3 config/rpc_pool.py`

### Test collection returns no data
- Check block number is valid
- Verify registry address correct
- Try different CSU

---

## 📚 Key Documents

1. **SETUP_INSTRUCTIONS.md** - Step-by-step setup (read first)
2. **docs/PRODUCTION_PLAN.md** - Full production strategy
3. **docs/PIPELINE_DESIGN.md** - Original design decisions

---

## 🔔 Next Steps After Setup

1. ✅ Complete Steps 1-6
2. ✅ Verify data quality
3. 📞 Tell me it works
4. 🚀 I build parallel collector
5. 🎯 You collect December 2024

---

## ⏱️ Timeline

| Phase | Time |
|-------|------|
| Setup (Steps 1-6) | 10 mins |
| I build parallel collector | 1 hour |
| Collection runs | 8-10 hours |
| **Total to data** | **~11 hours** |

---

## 💾 Storage

December 2024 (43 CSUs × 31 days):
- Bronze: ~80 MB
- Silver: ~50 MB (after you process)
- Gold: ~5 MB (panel format)
- **Total: ~135 MB**

Easily fits in thesis_v2/data/

---

## ✉️ Contact

Once setup complete, message with:
- ✅ All 6 steps done
- 📊 Sample of your data
- 🚀 Ready for parallel collector

Then I'll build the automated collection system!
