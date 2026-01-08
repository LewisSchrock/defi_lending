# Compound V3 Port Complete ✅

## What Was Ported

**3 CSUs:**
- Ethereum: USDC market (0xc3d688B66703497DAA19211EEdff47f25384cdc3)
- Arbitrum: USDC market (0xa5EDBDD9646f8dFFBf0e057b274Bdb8E11D2f8E0)
- Base: USDbC market (0xb125E6687d4313864e53df431d5425969c15Eb2F)

## Key Differences from Compound V2

| Feature | Compound V2 | Compound V3 |
|---------|-------------|-------------|
| Architecture | Multiple cTokens per Comptroller | One Comet = one market |
| Assets | All assets can be borrowed | Only base asset borrowable |
| Collateral | Borrow any cToken | Multiple collateral-only assets |
| Liquidation Event | `LiquidateBorrow` | `AbsorbCollateral` + `AbsorbDebt` |
| TVL | Per-cToken | Base + collaterals in single Comet |

## Implementation

### TVL Adapter (`adapters/tvl/compound_v3.py`)

**What it does:**
1. Reads base asset supply/borrow from Comet contract
2. Enumerates collateral assets via `numAssets()` and `getAssetInfo()`
3. Reads collateral balances via `totalsCollateral()`
4. Returns raw token amounts

**Key functions:**
- `baseToken()` - Get borrowable asset
- `totalSupply()` - Base asset supplied
- `totalBorrow()` - Base asset borrowed
- `numAssets()` - Number of collateral types
- `getAssetInfo(i)` - Get collateral asset info
- `totalsCollateral(asset)` - Get collateral supply

### Liquidation Adapter (`adapters/liquidations/compound_v3.py`)

**What it scans:**
- `AbsorbCollateral` events - Collateral seized from bad positions
- `AbsorbDebt` events - Debt absorbed by protocol

**Event signatures:**
```solidity
event AbsorbCollateral(
    address indexed absorber,
    address indexed borrower,
    address indexed asset,
    uint collateralAbsorbed,
    uint usdValue
)

event AbsorbDebt(
    address indexed absorber,
    address indexed borrower,
    uint basePaidOut,
    uint usdValue
)
```

**Rate limiting:**
- 10-block chunks (Alchemy safe)
- Exponential backoff on retries
- 100ms pacing between chunks

## Testing

### Test TVL
```bash
cd /Users/lewisschrock/Desktop/Academics/thesis_v2
export ALCHEMY_API_KEY='your_key'

# Ethereum
python scripts/test_single_csu.py compound_v3_ethereum --tvl

# Arbitrum
python scripts/test_single_csu.py compound_v3_arbitrum --tvl

# Base
python scripts/test_single_csu.py compound_v3_base --tvl
```

Expected output:
```
✅ Found 5-10 assets
Base asset:
  Symbol: USDC
  Supplied: 50,000,000.00
  Borrowed: 30,000,000.00

Collateral assets (4-9):
  WETH: 15,000.50
  WBTC: 250.25
  ...
```

### Test Liquidations
```bash
# Quick test (100 blocks)
python scripts/test_single_csu.py compound_v3_ethereum --liquidations --blocks 100

# Bigger test (10k blocks)
python scripts/test_single_csu.py compound_v3_ethereum --liquidations --blocks 10000
```

Expected output:
```
Scanning Comet: 0xc3d6...
Block range: [21,XXX,XXX, 21,XXX,XXX]
Chunk size: 10 blocks
  [21,XXX,XXX, 21,XXX,XXX]: 2 events
  [21,XXX,XXX, 21,XXX,XXX]: 0 events
✅ Scan complete: 10 chunks processed, 0 chunks failed

✅ Found X absorption events
First event:
  Type: AbsorbCollateral
  Absorber: 0x...
  Borrower: 0x...
  Collateral asset: 0x... (WETH)
  Collateral absorbed: 1.5
```

## Output Schema

### TVL Output
```python
[
    # Base asset
    {
        'asset_type': 'base',
        'underlying': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # USDC
        'symbol': 'USDC',
        'decimals': 6,
        'supplied_raw': 50000000000000,  # 50M USDC (6 decimals)
        'borrowed_raw': 30000000000000,  # 30M USDC
    },
    # Collateral assets
    {
        'asset_type': 'collateral',
        'underlying': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
        'symbol': 'WETH',
        'decimals': 18,
        'supplied_raw': 15000500000000000000000,  # 15k WETH (18 decimals)
        'borrowed_raw': 0,  # Collateral can't be borrowed
    },
    # ... more collateral assets
]
```

### Liquidation Output
```python
[
    {
        'tx_hash': '0x...',
        'log_index': 42,
        'block_number': 21234567,
        'event_type': 'AbsorbCollateral',
        'absorber': '0x...',  # Liquidator
        'borrower': '0x...',  # Bad position owner
        'collateral_asset': '0x...',  # What was seized
        'collateral_absorbed_raw': 1500000000000000000,  # Raw amount
        'usd_value_raw': 3000000000,  # USD value (8 decimals)
    },
    {
        'event_type': 'AbsorbDebt',
        'absorber': '0x...',
        'borrower': '0x...',
        'base_paid_out_raw': 2000000000,  # Base asset repaid
        'usd_value_raw': 2000000000,
    },
]
```

## Important Notes

### 1. Multiple Markets Per Chain
Each Comet contract is a separate market. Compound V3 has multiple markets per chain:

**Ethereum:**
- USDC market (main): 0xc3d6...
- WETH market: 0xA17581...
- We're starting with USDC (largest)

**Arbitrum:**
- USDC.e market: 0xa5ED...
- USDC native market: different address
- We're starting with USDC.e

If you want ALL Compound V3 data, you'd need to scan each market separately.

### 2. Event Pairing
`AbsorbCollateral` and `AbsorbDebt` are separate events but often appear together in the same transaction. For daily aggregation, you may want to group by transaction hash.

### 3. USD Values in Events
The events include `usdValue` fields (8 decimals). This is convenient for quick analysis but:
- Based on Compound's oracle prices at liquidation time
- May differ slightly from your pricing system
- Good for validation/cross-checking

## Progress Update

**Total CSUs ported: 13 / 30 (43%)**

✅ Aave V3: 10 CSUs
✅ Compound V3: 3 CSUs

**Remaining: 17 CSUs**
- Fluid: 4 CSUs
- Tectonic: 3 CSUs
- SparkLend: 1 CSU
- Venus: 1 CSU
- Lista: 1 CSU
- Benqi: 1 CSU
- Moonwell: 1 CSU
- Gearbox: 1 CSU
- cap: 1 CSU
- Kinetic: 1 CSU
- Tydro: 1 CSU
- Sumer: 1 CSU

## Next Protocol

**Recommended: Fluid (4 CSUs)**
- High value: 4 chains = 13% of remaining
- Ethereum, Plasma, Arbitrum, Base
- Unique architecture (worth understanding)

**Alternative: SparkLend (1 CSU)**
- Quick win: Almost identical to Aave V3
- ~30 minutes to port
