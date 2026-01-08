# Troubleshooting: Local Testing Setup

## Issue: Updated Code Not Visible Locally

### Problem
Files edited in Claude's computer use environment exist at:
```
/Users/lewisschrock/Desktop/Academics/thesis_v2/
```

But you need to **download** them to your actual local machine to test.

---

## Solution: Download Latest Code

### Step 1: Download the Zip File
I've created `thesis_v2_final.zip` in the outputs. Download it from the chat interface.

### Step 2: Extract to Your Local Machine
```bash
# On your actual machine (not in Claude)
cd ~/Desktop/Academics/  # Or wherever you want it
unzip thesis_v2_final.zip
cd thesis_v2/
```

### Step 3: Verify Files Exist Locally
```bash
# Check that generic adapters are present
ls -la adapters/tvl/
# Should show: compound_v2_style.py, aave_v3.py, compound_v3.py, fluid.py, venus.py

ls -la adapters/liquidations/
# Should show: compound_v2_style.py, aave_v3.py, compound_v3.py, fluid.py, venus.py
```

### Step 4: Test
```bash
export ALCHEMY_API_KEY='your_key_here'
python scripts/test_single_csu.py venus_binance --tvl
```

---

## Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'adapters'"
**Cause:** Running from wrong directory
**Fix:**
```bash
cd /path/to/thesis_v2/  # Must be in root directory
python scripts/test_single_csu.py venus_binance --tvl
```

### Issue 2: "ImportError: cannot import name 'get_compound_style_tvl'"
**Cause:** Old version of code
**Fix:** Re-download and extract the latest zip file

### Issue 3: File exists in Claude but not locally
**Cause:** You're looking at two different filesystems
- Claude's filesystem: `/Users/lewisschrock/Desktop/Academics/thesis_v2/`
- Your filesystem: `~/Desktop/Academics/thesis_v2/` (must download)

**Fix:** Always download the latest zip file after Claude makes updates

### Issue 4: "No RPC URL configured for chain X"
**Cause:** Missing RPC config
**Fix:** Edit `config/rpc_config.py`:
```python
ALCHEMY_CHAINS = {
    'ethereum': 'your_eth_key',
    'binance': 'your_bnb_key',
    'avalanche': 'your_avax_key',
    'base': 'your_base_key',
    # etc.
}
```

### Issue 5: Changes made but not working
**Cause:** Python cached bytecode (.pyc files)
**Fix:**
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
rm -f adapters/**/*.pyc
```

---

## File Manifest (What Should Be There)

### Core Adapters
```
adapters/
├── tvl/
│   ├── __init__.py
│   ├── aave_v3.py              ← Generic (12 CSUs)
│   ├── compound_v2_style.py    ← Generic (8 CSUs) ⭐
│   ├── compound_v3.py          ← Generic (3 CSUs)
│   ├── fluid.py                ← Generic (4 CSUs)
│   └── venus.py                ← Legacy (kept for reference)
└── liquidations/
    ├── __init__.py
    ├── aave_v3.py              ← Generic (12 CSUs)
    ├── compound_v2_style.py    ← Generic (8 CSUs) ⭐
    ├── compound_v3.py          ← Generic (3 CSUs)
    ├── fluid.py                ← Generic (4 CSUs)
    └── venus.py                ← Legacy (kept for reference)
```

### Test Script
```
scripts/
└── test_single_csu.py          ← Updated to use generics
```

### Config
```
config/
├── __init__.py
├── rpc_config.py               ← RPC URLs (YOU MUST EDIT)
└── units.csv
```

---

## Testing Checklist

### Before Testing
- [ ] Downloaded latest `thesis_v2_final.zip`
- [ ] Extracted to local machine
- [ ] Verified `compound_v2_style.py` exists in both adapters/ folders
- [ ] Edited `config/rpc_config.py` with your API keys
- [ ] Set environment variable: `export ALCHEMY_API_KEY=...`

### Quick Smoke Test
```bash
# Test 1: Aave V3 (proven to work)
python scripts/test_single_csu.py aave_v3_ethereum --tvl

# Test 2: Compound V3 (proven to work)
python scripts/test_single_csu.py compound_v3_ethereum --tvl

# Test 3: Fluid (proven to work)
python scripts/test_single_csu.py fluid_ethereum --tvl

# Test 4: Venus (uses generic adapter)
python scripts/test_single_csu.py venus_binance --tvl

# Test 5: Benqi (uses same generic adapter as Venus)
python scripts/test_single_csu.py benqi_avalanche --tvl
```

### Expected Output (Success)
```
Testing TVL for venus_binance
Chain: binance
RPC: https://bnb-mainnet.g.alchemy.com/v2/...
Latest block: 45,XXX,XXX

Running TVL extraction...
✅ Found 19 markets

First 3 markets:
- vUSDC: TVL = 123,456,789.12 USDC
- vBNB: TVL = 45,678.90 BNB
- vBTC: TVL = 234.56 BTC
```

---

## Quick Verification Commands

Run these in the thesis_v2/ directory:

```bash
# Verify directory structure
tree -L 3 -I '__pycache__'

# Verify generic adapters exist
ls -lh adapters/tvl/compound_v2_style.py
ls -lh adapters/liquidations/compound_v2_style.py

# Verify imports work
python -c "from adapters.tvl.compound_v2_style import get_compound_style_tvl; print('✅ TVL import works')"
python -c "from adapters.liquidations.compound_v2_style import scan_compound_style_liquidations; print('✅ Liquidations import works')"

# Test RPC connection
python -c "from web3 import Web3; from config.rpc_config import get_rpc_url; w3 = Web3(Web3.HTTPProvider(get_rpc_url('ethereum'))); print(f'✅ Connected to Ethereum: block {w3.eth.block_number:,}')"
```

---

## Still Having Issues?

### Debug Mode
Add `--debug` flag to get detailed output:
```bash
python scripts/test_single_csu.py venus_binance --tvl --debug
```

### Manual Test
```python
# test_manual.py
import sys
sys.path.insert(0, '.')

from web3 import Web3
from adapters.tvl.compound_v2_style import get_venus_tvl
from config.rpc_config import get_rpc_url

w3 = Web3(Web3.HTTPProvider(get_rpc_url('binance')))
comptroller = '0xfd36e2c2a6789db23113685031d7f16329158384'

print("Testing Venus TVL...")
results = get_venus_tvl(w3, comptroller)
print(f"Found {len(results)} markets")
print(f"First market: {results[0]['market_symbol']}")
```

Run with:
```bash
python test_manual.py
```

---

## Directory Confusion Diagram

```
┌─────────────────────────────────────────┐
│ CLAUDE'S COMPUTER USE ENVIRONMENT       │
│ Path: /Users/lewisschrock/.../thesis_v2/│
│                                         │
│ This is where I edit files ✏️           │
│ You CANNOT access this directly ❌      │
└─────────────────────────────────────────┘
                    │
                    │ Download via zip file
                    ↓
┌─────────────────────────────────────────┐
│ YOUR LOCAL MACHINE                      │
│ Path: ~/Desktop/Academics/thesis_v2/    │
│                                         │
│ This is where you test 🧪               │
│ You access this via terminal ✅         │
└─────────────────────────────────────────┘
```

**Key insight:** These are **two separate filesystems**. Changes I make in Claude's environment must be **downloaded** (via zip) to your local machine.

---

## Contact Points

If you're still stuck:
1. Check which directory you're in: `pwd`
2. Check if files exist: `ls -la adapters/tvl/`
3. Share the exact error message
4. Share your Python version: `python --version`
