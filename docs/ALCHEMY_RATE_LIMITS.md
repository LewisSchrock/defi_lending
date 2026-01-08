# Alchemy Free Tier Compliance

## Rate Limits (Per Account)

Based on Alchemy's free tier documentation:

### Compute Units (CUs)
- **300 CUs/second** per account
- **3 million CUs/month** per account (soft limit)

### Common Operation Costs
| Operation | CUs | Max/sec @ 300 CUs |
|-----------|-----|-------------------|
| eth_call | 26 | ~11 calls |
| eth_getLogs | 75 | ~4 calls |
| eth_getBlockByNumber | 16 | ~18 calls |
| eth_blockNumber | 10 | ~30 calls |

---

## Our Configuration

### Verified Key Mapping (From Test)
```
✅ ethereum  - 5 keys (key_1, key_2, key_3, key_4, key_5)
✅ arbitrum  - 4 keys (key_1, key_2, key_3, key_5)
✅ base      - 5 keys (all)
✅ polygon   - 5 keys (all)
✅ optimism  - 4 keys (key_1, key_2, key_3, key_5)
✅ binance   - 4 keys (key_1, key_2, key_3, key_5)
✅ avalanche - 5 keys (all)
✅ linea     - 4 keys (key_1, key_2, key_3, key_5)
✅ gnosis    - 4 keys (key_1, key_2, key_3, key_5)
❌ plasma    - 0 keys (PUBLIC RPC ONLY)
```

### Total Capacity
- **5 accounts × 300 CUs/sec = 1,500 CUs/sec**
- **~57 eth_call/sec** (for TVL)
- **~20 eth_getLogs/sec** (for liquidations)

---

## Rate Limiting Strategy

### Conservative Approach
**10 calls/second per key** regardless of operation type

Why conservative?
- Allows mixing of different operation types
- Provides safety margin for burst traffic
- Prevents accidental bans
- Better to be slow than banned

### Effective Capacity
- Ethereum: 5 keys × 10 calls/sec = **50 calls/sec**
- Arbitrum: 4 keys × 10 calls/sec = **40 calls/sec**
- Most chains: 4-5 keys = **40-50 calls/sec**

### Load Distribution
Round-robin across working keys:
```python
# Example: Ethereum with 5 keys
Request 1 → key_1 (wait 0.1s before next call on key_1)
Request 2 → key_2 (wait 0.1s before next call on key_2)
Request 3 → key_3
Request 4 → key_4
Request 5 → key_5
Request 6 → key_1 (0.1s has passed, safe to use again)
```

---

## Impact on Collection Speed

### TVL Collection (Fast)
- 1 CSU, 1 day: 1 eth_call
- 43 CSUs, 31 days: 1,333 calls
- **Time: ~27 seconds** (50 calls/sec on Ethereum)

### Liquidation Collection (Slower)
- 1 CSU, 1 day (Ethereum): 720 eth_getLogs (7,200 blocks ÷ 10)
- 43 CSUs, 31 days: ~960,000 calls
- **Time with rate limits: ~12-15 hours** (distributed across 5 workers)

---

## Monthly Usage Estimates

### December 2024 Collection (43 CSUs × 31 days)

**TVL:**
- 1,333 calls
- Avg 26 CUs/call
- **Total: ~35,000 CUs** (0.001% of monthly limit)

**Liquidations:**
- 960,000 calls
- Avg 75 CUs/call
- **Total: ~72 million CUs**
- Distributed across 5 accounts: **~14.4 million CUs per account**
- **Monthly limit: 3 million CUs per account ⚠️**

**Issue:** Liquidation collection exceeds free tier monthly limits!

---

## Solutions for Monthly Limit

### Option 1: Spread Collection Over Time ⏰
Collect 1 month of history per week:
- Week 1: Dec 2024
- Week 2: Nov 2024
- Week 3: Oct 2024
- Week 4: Sep 2024

**Pros:** Stays within free tier
**Cons:** Takes 4 weeks for 4 months of data

### Option 2: Upgrade Key Accounts 💰
Upgrade 2-3 accounts to Growth tier ($49/month):
- Growth tier: **Unlimited CUs** (within reason)
- Keep 2-3 accounts on free tier for redundancy

**Pros:** Fast collection, no waiting
**Cons:** $49-147/month during collection period

### Option 3: Focus on High-Priority CSUs First 🎯
Collect only most important protocols initially:
- Aave V3 (12 CSUs) - largest TVL
- Compound V3 (19 CSUs) - your thesis focus
- Skip smaller protocols for now

**Pros:** Fits within free tier
**Cons:** Incomplete dataset

### Option 4: Optimize Liquidation Scanning 🔍
Smart chunking strategies:
- Skip blocks with no liquidation events (pre-scan)
- Only scan blocks during high volatility periods
- Use event filters more aggressively

**Pros:** Could reduce calls by 50-70%
**Cons:** More complex, may miss some liquidations

---

## Recommended Approach

### Phase 1: TVL Collection (Fast & Free)
✅ Collect TVL for all 43 CSUs × 31 days
- **Time:** ~1 hour
- **Cost:** Free (minimal CUs)

### Phase 2: Critical Liquidations (Selective)
✅ Collect liquidations for Aave V3 + Compound V3 only
- 31 CSUs instead of 43
- **~700,000 calls instead of 960,000**
- Stays within free tier monthly limits

### Phase 3: Complete Later (Optional)
- Upgrade 1-2 accounts to Growth tier
- Collect remaining liquidations
- Or spread over multiple weeks

---

## Rate Limiter Configuration

Current settings in `config/rpc_pool.py`:

```python
class RateLimiter:
    def __init__(self, calls_per_second: float = 10):
        # Conservative: 10 calls/sec per key
        # Well under 300 CUs/sec limit
        ...
```

### Adjustable Parameters
If we need faster collection and upgrade accounts:

```python
# Growth tier (unlimited)
rate_limiter = RateLimiter(calls_per_second=50)  # Much faster

# Free tier (current)
rate_limiter = RateLimiter(calls_per_second=10)  # Conservative
```

---

## Monitoring Usage

### Check Usage in Alchemy Dashboard
1. Go to https://dashboard.alchemy.com
2. Select each app
3. View "Compute Units" graph
4. Monitor daily/monthly usage

### Warning Signs
- ⚠️ Approaching 3M CUs/month
- ⚠️ Consistent 429 errors (rate limiting)
- ⚠️ 403 errors (blocked/unauthorized)

### Safe Practice
- Start slow with test collections
- Monitor usage after first few hours
- Adjust rate limits if needed
- Upgrade accounts if consistently hitting limits

---

## Updated Collection Plan

### Immediate (Free Tier Safe)
```bash
# 1. Build block cache (minimal CUs)
python3 scripts/build_block_cache.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31

# 2. Collect TVL for all CSUs (fast, cheap)
python3 scripts/collect_tvl_parallel.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31

# 3. Collect liquidations for critical CSUs only
python3 scripts/collect_liquidations_parallel.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --protocols aave_v3,compound_v3  # 31 CSUs instead of 43
```

### Later (If Needed)
- Upgrade 2 accounts to Growth tier
- Collect remaining liquidations
- Or collect older historical data

---

## Summary

✅ **RPC pool updated** with verified key mapping
✅ **Rate limiting added** (10 calls/sec per key)
✅ **Within free tier** for TVL collection
⚠️ **Need strategy** for liquidations (exceeds monthly limits)

**Recommended:** Start with TVL + critical liquidations, evaluate usage, then decide on upgrades.
