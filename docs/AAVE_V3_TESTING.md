# Testing Aave V3 Adapter

## ✅ Ported Components

**TVL Adapter**: `adapters/tvl/aave_v3.py`
- Resolves Pool + DataProvider from PoolAddressesProvider
- Enumerates all reserves
- Reads aToken, stableDebt, variableDebt totalSupply
- Returns raw integer amounts (no USD conversion)

**Liquidation Adapter**: `adapters/liquidations/aave_v3.py`
- Resolves Pool address from registry  
- Scans for LiquidationCall events via eth_getLogs
- Chunks requests to handle Alchemy limits
- Decodes: borrower, liquidator, collateral/debt assets, amounts

## Testing

### 1. Set API Key

```bash
export ALCHEMY_API_KEY='your_key_here'
```

### 2. Test TVL Extraction

```bash
cd /Users/lewisschrock/Desktop/Academics/thesis_v2
python scripts/test_single_csu.py aave_v3_ethereum --tvl
```

Expected output:
```
============================================================
Testing TVL: aave_v3_ethereum
============================================================
Protocol: aave_v3
Chain: ethereum
Registry: 0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e
Latest block: 21,XXX,XXX

✅ Success! Found ~30-40 markets
```

### 3. Test Liquidation Extraction

```bash
python scripts/test_single_csu.py aave_v3_ethereum --liquidations --blocks 50000
```

Expected output:
```
============================================================
Testing Liquidations: aave_v3_ethereum
============================================================
Protocol: aave_v3
Chain: ethereum
Scanning last 50,000 blocks...

Scanning Pool: 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2
Block range: [21,XXX,XXX, 21,XXX,XXX]
  [21,XXX,XXX, 21,XXX,XXX]: X events
  ...

✅ Success! Found X liquidation events
```

### 4. Test Both Together

```bash
python scripts/test_single_csu.py aave_v3_ethereum --tvl --liquidations
```

## Output Schema

### TVL Output
```python
{
    'underlying': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
    'symbol': 'WETH',
    'decimals': 18,
    'a_token': '0x4d5F47FA6A74757f35C14fD3a6Ef8E3C9BC514E8',
    'stable_debt': '0x...',
    'variable_debt': '0x...',
    'supplied_raw': 1234567890000000000000,  # Raw integer (18 decimals)
    'stable_debt_raw': 0,
    'variable_debt_raw': 5678900000000000000,
}
```

### Liquidation Output
```python
{
    'tx_hash': '0x...',
    'log_index': 42,
    'block_number': 21234567,
    'collateral_asset': '0x...',  # Address
    'debt_asset': '0x...',  # Address
    'borrower': '0x...',
    'liquidator': '0x...',
    'debt_repaid_raw': 1000000000000000000,  # Raw integer
    'collateral_seized_raw': 900000000000000000,
    'receive_a_token': False,
}
```

## All 10 Aave V3 Chains

The same adapter works for all chains - just change the registry address:

| Chain | Registry Address |
|-------|------------------|
| Ethereum | 0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e |
| Polygon | 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb |
| Avalanche | 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb |
| Arbitrum | 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb |
| Optimism | 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb |
| Base | 0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D |
| BSC | 0xff75B6da14FfbbfD355Daf7a2731456b3562Ba6D |
| Polygon zkEVM | 0x061D8e131F26512348ee5FA42e2DF1bA9d6505E9 |
| Gnosis | 0x36616cf17557639614c1cdDb356b1B83fc0B2132 |
| Linea | 0x89502c3731F69DDC95B65753708A07F8Cd0373F4 |

## Next Steps

1. ✅ Test on Ethereum mainnet
2. Add other chain configs to test_single_csu.py
3. Test on 2-3 other chains
4. Port next protocol (Compound V3, Fluid, Venus, etc.)

## Key Simplifications from V1

1. **No base classes** - Just functions
2. **No complex config** - Registry address is all you need
3. **No separate resolvers** - Everything in one file
4. **Manual decoding** - Clear, explicit event parsing
5. **Minimal ABIs** - Only what we actually use

The code is ~200 lines per adapter vs. ~500+ in v1.
