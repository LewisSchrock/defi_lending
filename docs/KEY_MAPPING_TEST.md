# Key-Chain Mapping Test

## What This Does

Tests each of your 5 API keys individually against all 10 Alchemy chains to see which keys have which chains enabled. Creates a mapping file so we only use keys that actually work for each chain.

---

## Quick Run

```bash
cd ~/Desktop/Academics/thesis_v2/

# Make sure keys are loaded
source ../.env

# Run the test
python3 scripts/test_key_mapping.py
```

---

## What You'll See

```
ALCHEMY KEY-CHAIN MAPPING TEST
======================================================================

Testing 5 API keys across 10 chains
Total tests: 50

======================================================================
Testing key_1: f3xoB8jQS-...
======================================================================

  ✅ ethereum        - Block 21234567
  ✅ arbitrum        - Block 285678901
  ✅ optimism        - Block 134567890
  ✅ base            - Block 23456789
  ❌ polygon         - unauthorized
  ❌ avalanche       - unauthorized
  ...

======================================================================
Testing key_2: xh8NUxPyS5...
======================================================================
  ...

SUMMARY: Chain Availability
======================================================================

✅ ethereum        - 4 key(s): key_1, key_2, key_4, key_5
✅ arbitrum        - 4 key(s): key_1, key_2, key_4, key_5
✅ base            - 4 key(s): key_1, key_2, key_4, key_5
✅ polygon         - 2 key(s): key_2, key_5
❌ linea           - NO KEYS AVAILABLE

Statistics
======================================================================

Total chains tested: 10
Working chains: 8/10
Failed chains: 2

⚠️  WARNING: These chains have NO working keys:
   - linea
   - gnosis
```

---

## Output Files Created

### 1. `data/config/key_chain_mapping.json`

Complete mapping showing which keys work for which chains:

```json
{
  "chain_to_keys": {
    "ethereum": ["key_1", "key_2", "key_4", "key_5"],
    "arbitrum": ["key_1", "key_2", "key_4", "key_5"],
    "polygon": ["key_2", "key_5"],
    ...
  }
}
```

### 2. `data/config/optimized_pool_config.py`

Python config file for use in rpc_pool.py:

```python
CHAIN_KEY_MAPPING = {
    "ethereum": ["key_1", "key_2", "key_4", "key_5"],
    "arbitrum": ["key_1", "key_2", "key_4", "key_5"],
    ...
}
```

---

## What This Tells Us

### Good News ✅
- Which keys have which chains enabled
- How many keys per chain (load distribution)
- Which chains have redundancy

### Issues to Watch ⚠️
- Chains with only 1 key (rate limit risk)
- Chains with 0 keys (need to enable or use public RPC)
- Uneven distribution across keys

---

## Example Scenarios

### Scenario 1: All Keys Have All Chains
```
✅ ethereum - 5 key(s)
✅ arbitrum - 5 key(s)
✅ base     - 5 key(s)
```
**Perfect!** Maximum load distribution.

### Scenario 2: Mixed Configuration
```
✅ ethereum - 4 key(s): key_1, key_2, key_4, key_5
✅ arbitrum - 3 key(s): key_1, key_2, key_5
⚠️  polygon  - 1 key: key_3
❌ linea    - NO KEYS AVAILABLE
```
**Action needed:**
- Ethereum/Arbitrum: Good, 3-4 keys
- Polygon: Enable on more accounts (rate limit risk)
- Linea: Enable on at least one account OR use public RPC

---

## Next Steps After Test

### If All Chains Have Keys ✅
Continue with setup:
```bash
python3 scripts/build_block_cache.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31
```

### If Some Chains Missing ⚠️

**Option A: Enable Chains**
1. Go to Alchemy dashboard
2. Enable missing chains on accounts
3. Re-run test

**Option B: Use Public RPCs**
Missing chains will automatically fall back to public RPCs (slower, less reliable)

**Option C: Skip Those CSUs**
Focus on chains with working keys

---

## Updating RPC Pool

After test, rpc_pool.py can be updated to only use working keys:

```python
# Load mapping
with open('data/config/key_chain_mapping.json') as f:
    mapping = json.load(f)
    CHAIN_KEY_MAPPING = mapping['chain_to_keys']

# Use only working keys for each chain
def get_keys_for_chain(chain):
    return [ALCHEMY_KEYS[k] for k in CHAIN_KEY_MAPPING.get(chain, [])]
```

---

## Troubleshooting

### "No API keys found"
```bash
# Keys not loaded
source ../.env

# Test
echo $ALCHEMY_KEY_1
```

### "unauthorized" for all chains on one key
- Key may be invalid
- Account may be suspended
- Check Alchemy dashboard

### Timeout errors
- Temporary network issue
- Re-run test
- Keys are still valid even if test times out

---

## Expected Time

- **5 keys × 10 chains = 50 tests**
- **~1 second per test**
- **Total: ~1 minute**

---

## Ready?

Run the test and share the summary output so we can:
1. See which keys have which chains
2. Update rpc_pool.py to use optimal mapping
3. Continue with block cache building

```bash
python3 scripts/test_key_mapping.py
```
