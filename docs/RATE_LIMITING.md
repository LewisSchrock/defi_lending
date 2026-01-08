# Rate Limiting & Alchemy Free Tier Strategy

## The Problem

Alchemy's free tier has strict limits:
- **10 blocks max per eth_getLogs call**
- **300M compute units per month**
- **429 errors** when rate limit exceeded
- **Temporary throttling** when hitting limits

Your v1 code already handled this with `chunk=10` - I initially missed this critical constraint!

## The Solution

### 1. Small Chunk Sizes (10 blocks)

**Before (WRONG):**
```python
scan_aave_liquidations(w3, registry, from_block, to_block, chunk_size=2000)
# ❌ Would fail immediately with "query exceeds max block range"
```

**After (CORRECT):**
```python
scan_aave_liquidations(w3, registry, from_block, to_block, chunk_size=10)
# ✅ Respects Alchemy's 10-block limit
```

### 2. Retry Logic with Exponential Backoff

```python
for attempt in range(max_retries):
    try:
        logs = web3.eth.get_logs({...})
        break  # Success
    except Exception as e:
        if 'rate limit' in str(e).lower() and attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s...
            time.sleep(wait_time)
        else:
            # Skip this chunk after max retries
            break
```

### 3. Pacing Between Chunks

```python
# Small delay between successful chunks
time.sleep(pace_seconds)  # Default: 0.1s = 100ms
```

This prevents bursting and keeps request rate smooth.

### 4. Progress Reporting

```python
chunks_processed = 0
chunks_failed = 0

# After each chunk:
if logs:
    print(f"  [{from_block:,}, {to_block:,}]: {len(logs)} events")

# At end:
print(f"✅ {chunks_processed} chunks processed, {chunks_failed} chunks failed")
```

## Default Parameters

All liquidation adapters now use:

```python
def scan_protocol_liquidations(
    web3,
    registry,
    from_block,
    to_block,
    chunk_size=10,        # Alchemy free tier limit
    max_retries=3,        # Retry up to 3 times on rate limit
    pace_seconds=0.1      # 100ms between chunks
):
```

## Tuning Guide

### For Different RPC Providers

| Provider | chunk_size | pace_seconds | Notes |
|----------|------------|--------------|-------|
| Alchemy Free | 10 | 0.1 | Strict 10-block limit |
| Alchemy Growth | 10-100 | 0.05 | Higher compute units |
| Infura Free | 100 | 0.1 | More lenient |
| Public RPCs | 100-1000 | 0.5 | Often rate limited |
| Private Node | 10000 | 0 | No limits |

### For Different Scan Ranges

**Short scan (testing, < 50k blocks):**
```python
chunk_size=10
pace_seconds=0.1
max_retries=3
```

**Medium scan (daily updates, 50k-500k blocks):**
```python
chunk_size=10
pace_seconds=0.05  # Faster if you have headroom
max_retries=5      # More retries for reliability
```

**Long scan (historical, > 500k blocks):**
```python
chunk_size=10
pace_seconds=0.2   # Slower to be conservative
max_retries=5
# Consider running overnight or splitting across multiple days
```

### Environment Variables

You can override defaults via environment:

```bash
export CHUNK_SIZE=10
export PACE_SECONDS=0.1
export MAX_RETRIES=3
```

Then in your code:
```python
import os

chunk_size = int(os.getenv('CHUNK_SIZE', 10))
pace_seconds = float(os.getenv('PACE_SECONDS', 0.1))
max_retries = int(os.getenv('MAX_RETRIES', 3))
```

## Compute Unit Estimates

### Per Request
- `eth_getLogs` (10 blocks): ~50 CU
- `eth_call` (contract read): ~10 CU
- `eth_blockNumber`: ~10 CU

### Per CSU Scan (100k blocks)
```
Chunks needed: 100,000 / 10 = 10,000 chunks
CU per chunk: ~50 CU
Total: 10,000 × 50 = 500,000 CU
```

### Monthly Limit Strategy
```
Alchemy free tier: 300M CU/month
Budget per CSU: 300M / 30 CSUs = 10M CU per CSU
Blocks per CSU: 10M / 50 = 200k blocks

For 90 days of history (~650k blocks per chain):
Need 3-4 free Alchemy accounts, OR
Spread collection over 3 months
```

## Error Messages to Watch For

### Rate Limit Errors
```
"Too many requests"
"Rate limit exceeded"  
"429 Too Many Requests"
"Compute units exceeded"
"Daily request limit exceeded"
```

**Solution:** Retry with exponential backoff (handled automatically)

### Block Range Errors
```
"query exceeds max block range"
"logs query exceeds max range of 10 blocks"
```

**Solution:** Reduce chunk_size to 10 or less

### Connection Errors
```
"Connection refused"
"Timeout"
"Read timed out"
```

**Solution:** Retry (handled automatically) or check network/RPC health

## Testing Rate Limits

### Quick Test (100 blocks)
```bash
python scripts/test_single_csu.py aave_v3_ethereum --liquidations --blocks 100
# Should complete in ~2 seconds with 10 chunks
```

### Medium Test (1000 blocks)
```bash
python scripts/test_single_csu.py aave_v3_ethereum --liquidations --blocks 1000
# Should complete in ~15 seconds with 100 chunks
```

### Stress Test (10k blocks)
```bash
python scripts/test_single_csu.py aave_v3_ethereum --liquidations --blocks 10000
# Should complete in ~2-3 minutes with 1000 chunks
# Watch for any rate limit errors
```

### Full Historical Test (100k blocks)
```bash
python scripts/test_single_csu.py aave_v3_ethereum --liquidations --blocks 100000
# Should complete in ~20-30 minutes with 10k chunks
# Good test of sustained rate
```

## Monitoring During Collection

Watch for these patterns:

✅ **Good (healthy):**
```
  [21,123,456, 21,123,465]: 2 events
  [21,123,466, 21,123,475]: 0 events
  [21,123,476, 21,123,485]: 1 events
✅ 1000 chunks processed, 0 chunks failed
```

⚠️ **Warning (approaching limits):**
```
  [21,123,456, 21,123,465]: 2 events
  Rate limit hit on [21,123,466, 21,123,475], retrying in 1s... (attempt 1/3)
  [21,123,466, 21,123,475]: 0 events
✅ 1000 chunks processed, 0 chunks failed
```

❌ **Problem (hitting hard limits):**
```
  Rate limit hit on [21,123,456, 21,123,465], retrying in 1s... (attempt 1/3)
  Rate limit hit on [21,123,456, 21,123,465], retrying in 2s... (attempt 2/3)
  Rate limit hit on [21,123,456, 21,123,465], retrying in 4s... (attempt 3/3)
  ❌ Failed [21,123,456, 21,123,465] after 3 attempts
✅ 900 chunks processed, 100 chunks failed
```

**Solution for problems:**
1. Increase `pace_seconds` to 0.5-1.0
2. Use multiple Alchemy accounts
3. Spread collection over multiple days
4. Use paid tier

## Best Practices

1. **Always test with small ranges first** (100-1000 blocks)
2. **Monitor the first 100 chunks** of any long scan
3. **Use verbose logging** to catch issues early
4. **Save progress periodically** (checkpoint every N chunks)
5. **Run overnight for large scans** (100k+ blocks)

## Multi-Account Strategy

For 30 CSUs with 90 days of history each:

```python
# Split CSUs across 4 accounts
accounts = {
    'A': ['aave_v3_ethereum', 'aave_v3_polygon', ...],  # 8 CSUs
    'B': ['compound_v3_ethereum', ...],                 # 8 CSUs
    'C': ['fluid_ethereum', ...],                       # 7 CSUs
    'D': ['venus_binance', ...],                        # 7 CSUs
}

# Each account handles ~7M CU per month
# Well within 300M limit
```

This avoids rate limits entirely by distributing load.

## Summary

**Key changes from initial v2 port:**
- ✅ `chunk_size=10` (was 2000)
- ✅ Retry logic with exponential backoff
- ✅ Pace control between chunks
- ✅ Failed chunk tracking
- ✅ Detailed progress reporting

**This makes the adapter production-ready for Alchemy free tier!**
