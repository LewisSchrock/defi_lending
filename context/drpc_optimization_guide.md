# dRPC Optimization Guide for Liquidation Enrichment

## Current Status
- **Script**: `enrich_liquidations_multi_oracle.py`
- **Total Events**: 438,438 liquidations across 11 chains
- **Current Speed**: Serial processing (~1-2 RPC calls per event, ~0.2-0.5s each) = **6-24 hours**
- **Problem**: No concurrency - processes one event at a time

## dRPC Capabilities

Based on dRPC documentation and testing:

### Free Tier Limits
- **Rate Limit**: ~315,000 computational units (CU) per minute
- **Practical Limit**: ~250 `eth_call` requests per second
- **Dynamic Throttling**: ~2,100 CU/second during peak demand
- **Batch Requests**: Supported via JSON-RPC batch calls

### Paid Tier Benefits
- Higher CU allocations
- Priority routing
- Better latency during peak times

**Sources:**
- [Understanding dRPC Rate Limiting](https://drpc.org/docs/howitworks/ratelimiting)
- [DRPC Rate Limiting Docs](https://docs.drpc.org/howitworks/ratelimiting)

## Current Bottlenecks

1. **Serial Processing**: Script processes one event at a time
2. **No Request Batching**: Each price lookup is a separate RPC call
3. **No Concurrency**: Single-threaded execution
4. **Cache Miss Penalty**: First run has 0% cache hit rate

## Optimization Strategy

### 1. Concurrent Request Processing
- Use `ThreadPoolExecutor` with 50-100 workers
- Process multiple events in parallel
- Target: ~100-150 requests/second (under dRPC's 250 req/s limit)

### 2. Request Batching
- Batch similar price requests by block number
- Use JSON-RPC batch calls (up to 100 calls per batch)
- Reduces network overhead

### 3. Smart Rate Limiting
- Implement token bucket algorithm
- Target: 100-150 requests/second sustained
- Burst capacity: up to 200 req/s for short periods
- Automatic backoff on rate limit errors

### 4. Cache Optimization
- **Persistent Cache**: Already implemented ✅
- **In-Memory Cache**: Keep frequently accessed prices in memory
- **Pre-warm Cache**: Load common stablecoin prices upfront

### 5. Retry Logic
- Exponential backoff for failed requests
- Maximum 3 retries per request
- Log persistent failures for manual review

## Expected Performance Improvements

| Optimization | Speedup | Estimated Time |
|-------------|---------|----------------|
| **Current (Serial)** | 1× | 12-24 hours |
| **+ Concurrency (50 workers)** | 25-40× | 20-45 minutes |
| **+ Request Batching** | 50-80× | 10-20 minutes |
| **+ Cache Hit (50%)** | 100-150× | 5-10 minutes |

**Target**: Reduce 12-24 hours → **10-30 minutes** with optimizations

## Implementation Plan

### Phase 1: Add Concurrency (Immediate)
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from collections import deque
```

- Process events in parallel batches of 50-100
- Implement simple rate limiter (100 req/s)
- **Expected time**: 30-60 minutes for 438k events

### Phase 2: Add Batching (Advanced)
- Group price requests by block range
- Use JSON-RPC batch calls
- **Expected time**: 15-30 minutes

### Phase 3: Optimize Cache Strategy
- Pre-load stablecoin prices (always $1.00)
- Implement LRU cache for hot prices
- **Expected time**: 10-20 minutes with 50% cache hits

## Rate Limiter Implementation

```python
class RateLimiter:
    def __init__(self, requests_per_second=100):
        self.rate = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()

    def acquire(self):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True

        sleep_time = (1 - self.tokens) / self.rate
        time.sleep(sleep_time)
        self.tokens = 0
        return True
```

## Monitoring & Safety

1. **Progress Tracking**: Log every 100 events processed
2. **Cache Stats**: Track hit rate, show in progress updates
3. **Error Tracking**: Log RPC failures, rate limit hits
4. **Checkpointing**: Save progress every 1,000 events (already implemented ✅)
5. **Price Cache**: Save cache every 1,000 events (already implemented ✅)

## Environment Setup

Ensure dRPC key is set:
```bash
export DRPC_KEY_1="your_drpc_key"
# Or chain-specific:
export DRPC_KEY_ETHEREUM="your_ethereum_key"
export DRPC_KEY_ARBITRUM="your_arbitrum_key"
```

## Next Steps

1. ✅ Add persistent price cache (DONE)
2. 🔄 Add concurrent processing with ThreadPoolExecutor
3. ⏳ Add rate limiter (100 req/s)
4. ⏳ Add retry logic with exponential backoff
5. ⏳ (Optional) Add request batching for advanced optimization

---

## References

- [dRPC Rate Limiting Documentation](https://drpc.org/docs/howitworks/ratelimiting)
- [API Rate Limiting Best Practices 2026](https://apistatuscheck.com/blog/how-to-handle-api-rate-limits)
- [dRPC Free Plan Changes](https://drpc.org/blog/upcoming-changes-to-drpcs-free-plan-effective-june-1-2025/)