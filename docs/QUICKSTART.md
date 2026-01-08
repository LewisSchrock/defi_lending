# Quick Start: Test Generic Adapters Now

## Download & Setup (2 minutes)

### 1. Download the Zip
Download `thesis_v2_complete.zip` from this chat (it's in the outputs above)

### 2. Extract on Your Local Machine
```bash
cd ~/Desktop/Academics/
unzip thesis_v2_complete.zip
cd thesis_v2/
```

### 3. Verify Generic Adapters Exist
```bash
ls -l adapters/tvl/compound_v2_style.py
ls -l adapters/liquidations/compound_v2_style.py
```

You should see both files (created today at 18:22).

### 4. Set Your API Key
```bash
export ALCHEMY_API_KEY='your_actual_key_here'
```

---

## Test Commands (Copy & Paste)

### Test 1: Venus (uses generic Compound V2 adapter)
```bash
python scripts/test_single_csu.py venus_binance --tvl
```

**Expected output:**
```
Testing TVL for venus_binance
Chain: binance
...
✅ Found 19 markets
First 3 markets:
- vUSDC: ...
- vBNB: ...
```

### Test 2: Benqi (same adapter, different chain)
```bash
python scripts/test_single_csu.py benqi_avalanche --tvl
```

### Test 3: Moonwell (same adapter, Base chain)
```bash
python scripts/test_single_csu.py moonwell_base --tvl
```

### Test 4: Liquidations
```bash
python scripts/test_single_csu.py venus_binance --liquidations --blocks 100
```

---

## What's in the Generic Adapter?

Open `adapters/tvl/compound_v2_style.py` and you'll see:

```python
def get_compound_style_tvl(web3, comptroller_address, ...):
    """Generic TVL for ANY Compound V2-style protocol"""
    # Works for Venus, Benqi, Moonwell, Kinetic, Tectonic, Sumer
    
# Convenience wrappers
def get_venus_tvl(web3, comptroller, block=None):
    return get_compound_style_tvl(web3, comptroller, block, "vToken")

def get_benqi_tvl(web3, comptroller, block=None):
    return get_compound_style_tvl(web3, comptroller, block, "qToken")
```

**All 8 protocols** share this **one file**. Bug fixes benefit everyone!

---

## Debugging

### If imports fail:
```bash
# Make sure you're in thesis_v2/ directory
pwd  # Should show: .../thesis_v2

# Try manual import
python -c "from adapters.tvl.compound_v2_style import get_venus_tvl; print('✅ Works!')"
```

### If "No RPC URL" error:
Edit `config/rpc_config.py` and add your keys:
```python
ALCHEMY_CHAINS = {
    'binance': 'your_bnb_key',
    'avalanche': 'your_avax_key',
    'base': 'your_base_key',
}
```

### If file doesn't exist:
You downloaded an old version. Re-download `thesis_v2_complete.zip` from this chat.

---

## File Checklist

Before testing, verify these exist locally:

```bash
# Should all exist and show timestamps from today
ls -l adapters/tvl/compound_v2_style.py          # ← NEW GENERIC
ls -l adapters/liquidations/compound_v2_style.py  # ← NEW GENERIC
ls -l adapters/tvl/aave_v3.py                     # ← Aave generic
ls -l adapters/tvl/compound_v3.py                 # ← Compound V3
ls -l adapters/tvl/fluid.py                       # ← Fluid
ls -l scripts/test_single_csu.py                  # ← Updated test script
```

All files should have today's date (Jan 6).

---

## Success Metrics

After running tests, you should see:
- ✅ No import errors
- ✅ Successfully connects to RPC
- ✅ Finds markets (10-20 for most protocols)
- ✅ Returns TVL data with token symbols

---

## Two Filesystems Explained

```
┌──────────────────────────────────┐
│ CLAUDE's Computer                │  ← I edit files here
│ /Users/lewisschrock/.../thesis_v2│     You CAN'T access this
└──────────────────────────────────┘
            │
            │ 📦 Download zip
            ↓
┌──────────────────────────────────┐
│ YOUR Computer                    │  ← You test here
│ ~/Desktop/Academics/thesis_v2    │     After downloading zip
└──────────────────────────────────┘
```

**Key point:** Every time I make changes, you need to **download the new zip** to see them on your machine.

---

## Ready to Test!

```bash
# Quick test of all 4 architecture families
python scripts/test_single_csu.py aave_v3_ethereum --tvl       # Aave V3 generic
python scripts/test_single_csu.py compound_v3_ethereum --tvl  # Compound V3 generic
python scripts/test_single_csu.py fluid_ethereum --tvl        # Fluid generic
python scripts/test_single_csu.py venus_binance --tvl         # Compound V2 generic ⭐
```

All should work immediately!
