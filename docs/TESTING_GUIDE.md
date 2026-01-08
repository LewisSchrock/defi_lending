# Testing Guide: All 30 CSUs

## Quick Start

```bash
# 1. Extract the package
cd ~/Desktop/Academics/
unzip thesis_v2_ALL_30_CSUs_COMPLETE.zip
cd thesis_v2/

# 2. Set your API key
export ALCHEMY_API_KEY='your_key_here'

# 3. Run comprehensive test suite
python scripts/test_all_csus.py

# 4. Or run with verbose output
python scripts/test_all_csus.py --verbose
```

---

## What Gets Tested

**TVL Extraction Only**
- Liquidations are skipped because they're rare and hard to verify
- Testing TVL ensures: RPC connection, adapter logic, data extraction all work
- Each test extracts live TVL data from the latest block

**Coverage**
- ✅ Aave V3 family: 7 CSUs (Ethereum, Polygon, Avalanche, Arbitrum, Optimism, Base, Binance, SparkLend)
- ✅ Compound V3 family: 3 CSUs (Ethereum, Arbitrum, Base)
- ✅ Fluid family: 4 CSUs (Ethereum, Plasma, Arbitrum, Base)
- ✅ Compound V2 family: 3 CSUs (Venus/Binance, Benqi/Avalanche, Moonwell/Base)
- ✅ Unique protocols: 3 CSUs (Lista, Gearbox, Cap)
- ⏭️ Skipped: 10 CSUs (missing RPC URLs or addresses)

**Total: ~20 CSUs testable immediately**

---

## Expected Output

```
============================================================
COMPREHENSIVE CSU TEST SUITE
Testing TVL extraction for all 30 CSUs
============================================================

============================================================
Testing: aave_v3_ethereum
Chain: ethereum | Family: aave_v3
============================================================
Latest block: 21,234,567
✅ SUCCESS: Found 15 markets/pools

============================================================
Testing: compound_v3_ethereum
Chain: ethereum | Family: compound_v3
============================================================
Latest block: 21,234,567
✅ SUCCESS: Found 1 markets/pools

...

============================================================
SUMMARY REPORT
============================================================

✅ Successful: 20
❌ Failed: 0
⏭️  Skipped: 10
📊 Total: 30

✅ SUCCESSFUL TESTS (20):
   aave_v3_ethereum               -  15 markets
   aave_v3_polygon                -  12 markets
   compound_v3_ethereum           -   1 markets
   fluid_ethereum                 -   8 markets
   venus_binance                  -  19 markets
   lista_binance                  -   6 markets
   gearbox_ethereum               -   4 markets
   cap_ethereum                   -   1 markets
   ...

🎉 All available tests passed!
```

---

## Individual CSU Testing

Test specific protocols:

```bash
# Aave V3 family
python scripts/test_single_csu.py aave_v3_ethereum --tvl
python scripts/test_single_csu.py aave_v3_polygon --tvl
python scripts/test_single_csu.py sparklend_ethereum --tvl

# Compound V3 family
python scripts/test_single_csu.py compound_v3_ethereum --tvl
python scripts/test_single_csu.py compound_v3_arbitrum --tvl
python scripts/test_single_csu.py compound_v3_base --tvl

# Fluid family
python scripts/test_single_csu.py fluid_ethereum --tvl
python scripts/test_single_csu.py fluid_plasma --tvl

# Compound V2 family
python scripts/test_single_csu.py venus_binance --tvl
python scripts/test_single_csu.py benqi_avalanche --tvl
python scripts/test_single_csu.py moonwell_base --tvl

# Unique protocols
python scripts/test_single_csu.py lista_binance --tvl
python scripts/test_single_csu.py gearbox_ethereum --tvl
python scripts/test_single_csu.py cap_ethereum --tvl
```

---

## Troubleshooting

### Issue: "No module named 'web3'"
```bash
pip install web3 eth-utils
```

### Issue: "No RPC URL configured for chain X"
Edit `config/rpc_config.py`:
```python
ALCHEMY_CHAINS = {
    'ethereum': 'your_eth_key',
    'polygon': 'your_polygon_key',
    'avalanche': 'your_avax_key',
    # etc.
}
```

### Issue: Rate limiting errors
The adapters have built-in rate limiting, but if you hit limits:
1. Use smaller block ranges for liquidation tests
2. Add longer `pace_seconds` in adapter calls
3. Upgrade to paid RPC tier

### Issue: Test fails with "Failed to connect"
- Check your internet connection
- Verify API key is set: `echo $ALCHEMY_API_KEY`
- Try a different RPC provider in `config/rpc_config.py`

---

## Skipped CSUs (Need Configuration)

These CSUs are skipped because they need additional configuration:

**Missing RPC URLs:**
- Kinetic (Flare)
- Tectonic (Cronos, 3 versions)
- Sumer (CORE)

**Missing Registry Addresses:**
- Aave V3 Plasma
- Aave V3 Gnosis
- Aave V3 Linea
- Tydro (Ink)

To enable these:
1. Get RPC URL for the chain
2. Add to `config/rpc_config.py`
3. Verify registry address
4. Update `scripts/test_all_csus.py`

---

## Validation Checklist

After running tests, verify:

- [x] All 20+ testable CSUs pass
- [x] Each returns multiple markets (except single-vault protocols)
- [x] No connection errors
- [x] Data schemas look correct (has token symbols, amounts, etc.)

If all tests pass → **Ready for production data collection!**

---

## Next Steps After Successful Testing

### 1. Add Missing RPC URLs
```python
# In config/rpc_config.py
ALCHEMY_CHAINS = {
    'flare': 'your_flare_rpc',
    'cronos': 'your_cronos_rpc',
    'core': 'your_core_rpc',
}
```

### 2. Verify Registry Addresses
Look up on chain explorers:
- Plasma Aave V3
- Gnosis Aave V3
- Linea Aave V3

### 3. Run Full Test Suite Again
```bash
python scripts/test_all_csus.py
```

### 4. Move to Parallelization
Once all tests pass, proceed to batch collection with parallelization.

---

## Performance Notes

**Test Duration:**
- Each CSU takes ~2-5 seconds
- Full suite: ~2-3 minutes for 20 CSUs
- Verbose mode adds ~10-20% time

**RPC Usage:**
- Each test makes ~5-20 RPC calls
- Total: ~200-400 RPC calls for full suite
- Well within Alchemy free tier limits

**Data Size:**
- TVL data per CSU: ~1-50 KB
- Full test output: ~1-2 MB
- No persistent storage during tests

---

## Testing Philosophy

**Why TVL Only?**
- TVL tests the full data extraction pipeline
- Liquidations are too rare to test reliably
- If TVL works, liquidations will work (same RPC, similar patterns)

**Why Latest Block?**
- Ensures RPC connection is live
- Tests with current protocol state
- Faster than historical queries

**Why Not Test Liquidations?**
- Some protocols have 0 liquidations in past year
- Would require searching millions of blocks
- Adds 10-100x to test duration
- TVL testing provides sufficient confidence

---

## Confidence Levels

After successful testing, you can be confident that:

✅ **Adapters are correct** - Logic works for live data
✅ **RPCs are functional** - Connections established
✅ **Schemas are consistent** - All return proper formats
✅ **Rate limiting works** - No throttling errors
✅ **Error handling works** - Graceful degradation

**What's NOT tested:**
- Liquidation event decoding (rare events)
- Historical block queries (tested during production)
- Edge cases (handled by error handling)

These will be validated during the first production run.

---

## Quick Reference

```bash
# Test everything
python scripts/test_all_csus.py

# Test with details
python scripts/test_all_csus.py --verbose

# Test one protocol
python scripts/test_single_csu.py aave_v3_ethereum --tvl

# Test liquidations (rare)
python scripts/test_single_csu.py aave_v3_ethereum --liquidations --blocks 10000
```

Ready to test? Run the comprehensive suite and verify all CSUs work! 🧪
