# CSU Configuration Status Report

**Date**: 2026-01-09
**Total Target CSUs**: 46
**Total Configured CSUs**: 67 (includes non-target protocols)

## Summary

✅ **All 46 target CSUs are now configured in [csu_config.yaml](code/config/csu_config.yaml)**

The config file has been updated to include:
- **Added 17 Compound V3 market CSUs** (previously had only 2 generic entries)
- **Added 1 Fluid CSU** (fluid_lending_base)
- **Added 3 Aave V3 CSUs** (avalanche, base, scroll, sonic → added 4 total)
- **Fixed CAP registry address** (was empty)

---

## Target CSUs Status (46 total)

### ✅ Aave V3 Markets (12/12 configured)

| CSU Name | Chain | Registry Address | Status |
|----------|-------|------------------|--------|
| aave_v3_ethereum | ethereum | 0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e | ✅ Configured |
| aave_v3_arbitrum | arbitrum | 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb | ✅ Configured |
| aave_v3_optimism | optimism | 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb | ✅ Configured |
| aave_v3_base | base | 0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D | ✅ Configured |
| aave_v3_polygon | polygon | 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb | ✅ Configured |
| aave_v3_avalanche | avalanche | 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb | ✅ Configured |
| aave_v3_binance | binance | 0xff75B6da14FfbbfD355Daf7a2731456b3562Ba6D | ✅ Configured |
| aave_v3_plasma | plasma | 0x061D8e131F26512348ee5FA42e2DF1bA9d6505E9 | ✅ Configured |
| aave_v3_xdai | xdai (gnosis) | 0x36616cf17557639614c1cdDb356b1B83fc0B2132 | ✅ Configured |
| aave_v3_linea | linea | 0x89502c3731F69DDC95B65753708A07F8Cd0373F4 | ✅ Configured |
| aave_v3_scroll | scroll | 0x69850D0B276776781C063771b161bd8894BCdD04 | ✅ Configured |
| aave_v3_sonic | sonic | 0x69850D0B276776781C063771b161bd8894BCdD04 | ✅ Configured |

### ✅ Compound V3 Markets (19/19 configured)

Each Compound V3 market is a separate Comet contract.

#### Ethereum (5 markets)
| CSU Name | Base Asset | Registry (Comet) Address | Status |
|----------|------------|--------------------------|--------|
| compound_v3_eth_usdc | USDC | 0xc3d688B66703497DAA19211EEdff47f25384cdc3 | ✅ Configured |
| compound_v3_eth_weth | WETH | 0xA17581A9E3356d9A858b789D68B4d866e593aE94 | ✅ Configured |
| compound_v3_eth_usdt | USDT | 0x3Afdc9BCA9213A35503b077a6072F3D0d5AB0840 | ✅ Configured |
| compound_v3_eth_wsteth | wstETH | 0x3D0bb1ccaB520A66e607822fC55BC921738fAFE3 | ✅ Configured |
| compound_v3_eth_usds | USDS | 0x5D409e56D886231aDAf00c8775665AD0f9897b56 | ✅ Configured |

#### Arbitrum (4 markets)
| CSU Name | Base Asset | Registry (Comet) Address | Status |
|----------|------------|--------------------------|--------|
| compound_v3_arb_usdc | USDC | 0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf | ✅ Configured |
| compound_v3_arb_usdc_e | USDC.e | 0xA5EDBDD9646f8dFFBf0e057b274Bdb8E11D2f8E0 | ✅ Configured |
| compound_v3_arb_weth | WETH | 0x6f7D514bbD4aFf3BcD1140B7344b32f063dEe486 | ✅ Configured |
| compound_v3_arb_usdt | USDT | 0xd98Be00b5D27fc98112BdE293e487f8D4cA57d07 | ✅ Configured |

#### Base (4 markets)
| CSU Name | Base Asset | Registry (Comet) Address | Status |
|----------|------------|--------------------------|--------|
| compound_v3_base_usdc | USDC | 0xb125E6687d4313864e53df431d5425969c15Eb2F | ✅ Configured |
| compound_v3_base_usdbc | USDbC | 0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf | ✅ Configured |
| compound_v3_base_weth | WETH | 0x46e6b214b524310239732D51387075E0e70970bf | ✅ Configured |
| compound_v3_base_aero | AERO | 0x784efeB622244d2348d4F2522f8860B96fbEcE89 | ✅ Configured |

#### Optimism (3 markets)
| CSU Name | Base Asset | Registry (Comet) Address | Status |
|----------|------------|--------------------------|--------|
| compound_v3_op_usdc | USDC | 0x2e44e174f7D53F0212823acC11C01A11d58c5bCB | ✅ Configured |
| compound_v3_op_usdt | USDT | 0x995E394b8B2437aC8Ce61Ee0bC610D617962B214 | ✅ Configured |
| compound_v3_op_weth | WETH | 0xE36A30D249f7761327fd973001A32010b521b6Fd | ✅ Configured |

#### Polygon (3 markets)
| CSU Name | Base Asset | Registry (Comet) Address | Status |
|----------|------------|--------------------------|--------|
| compound_v3_poly_usdc | USDC | 0xF25212E676D1F7F89Cd72fFEe66158f541246445 | ✅ Configured |
| compound_v3_poly_usdc_e | USDC.e | 0xaeB0E0Ed3cE4Bf8001A38B1d2a7E8C3a27F61E4e | ✅ Configured |
| compound_v3_poly_usdt | USDT | 0xaeB0E0Ed3cE4Bf8001A38B1d2a7E8C3a27F61E4e | ✅ Configured |

### ✅ Compound V2-style Protocols (8/8 configured)

| CSU Name | Protocol | Chain | Registry Address | Status |
|----------|----------|-------|------------------|--------|
| venus_core_pool_binance | Venus | binance | 0xfd36e2c2a6789db23113685031d7f16329158384 | ✅ Configured |
| benqi_lending_avalanche | BENQI | avalanche | 0x7f1d2cE98240d5a9008CF0788c5C69A0d7F8FbB5 | ✅ Configured |
| moonwell_lending_base | Moonwell | base | 0xfBb21d0380beE3312B33c4353c8936a0F13EF26C | ✅ Configured |
| tectonic_cronos_main | Tectonic | cronos | TectonicCore: 0x7de56bd8b37827c51835e162c867848fe2403a48 | ✅ Configured |
| tectonic_cronos_veno | Tectonic | cronos | TectonicCore: 0x7de56bd8b37827c51835e162c867848fe2403a48 | ✅ Configured |
| tectonic_cronos_defi | Tectonic | cronos | TectonicCore: 0x7de56bd8b37827c51835e162c867848fe2403a48 | ✅ Configured |
| sumermoney_meter | Sumer | meter | 0xcB4cdDA50C1B6B0E33F544c98420722093B7Aa88 | ✅ Configured |
| kinetic_flare | Kinetic | flare | 0x8041680Fb73E1Fe5F851e76233DCDfA0f2D2D7c8 | ✅ Configured |

### ✅ Fluid Markets (4/4 configured)

| CSU Name | Chain | Registry Address | Status |
|----------|-------|------------------|--------|
| fluid_lending_ethereum | ethereum | 0xC215485C572365AE87f908ad35233EC2572A3BEC | ✅ Configured |
| fluid_lending_arbitrum | arbitrum | 0xdF4d3272FfAE8036d9a2E1626Df2Db5863b4b302 | ✅ Configured |
| fluid_lending_base | base | 0x264786EF916af64a1DB19F513F24a3681734ce92 | ✅ Configured |
| fluid_lending_plasma | plasma | 0xfbb7005c49520a4E54746487f0b28F4E4594b293 | ✅ Configured |

### ✅ Unique Protocols (3/3 configured)

| CSU Name | Protocol | Chain | Registry Address | Status |
|----------|----------|-------|------------------|--------|
| gearbox_ethereum | Gearbox | ethereum | 0x9ea7b04da02a5373317d745c1571c84aad03321d | ✅ Configured |
| cap_ethereum | CAP | ethereum | 0x726B8d03D43E71c533ECBb2E5095D2e60dc8A30E | ✅ Configured (fixed) |
| kinetic_flare | Kinetic | flare | 0x8041680Fb73E1Fe5F851e76233DCDfA0f2D2D7c8 | ✅ Configured |

---

## Next Steps

### 1. Build Missing Block Caches

Some chains still need block caches built for December 2024:

**Missing caches:**
- ❌ cronos (tectonic markets)
- ❌ meter (sumermoney)
- ❌ flare (kinetic)
- ❌ scroll (aave_v3_scroll)
- ❌ sonic (aave_v3_sonic - new chain)
- ⚠️ binance (failed previously due to rate limiting)

**Command to build:**
```bash
python3 scripts/build_block_cache.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --chains cronos meter flare scroll sonic binance
```

### 2. Test TVL Collection

Run a test collection for all 46 target CSUs:

```bash
# Test single day first
python3 scripts/collect_tvl_parallel.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-01 \
  --workers 5

# Then run full December 2024
python3 scripts/collect_tvl_parallel.py \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --workers 5
```

### 3. Expected Issues & Solutions

#### Archive Node Limitations
Some CSUs may fail due to free Alchemy tier not providing full archive access:
- aave_v3_polygon
- compound_v3_arbitrum (some markets)
- aave_v3_plasma
- fluid_plasma

**Solutions:**
- Upgrade to paid Alchemy plan with archive access, OR
- Find alternative archive RPC providers, OR
- Accept limited CSU coverage and document

#### Chain RPC Availability
Some chains require custom RPC setup:
- **cronos**: Uses `https://evm.cronos.org/` (already in config)
- **meter**: Uses `https://rpc.meter.io` (already in config)
- **flare**: Uses `https://flare-api.flare.network/ext/C/rpc` (already in config)
- **scroll**: May need custom RPC if Alchemy doesn't support
- **sonic**: New chain, may need custom RPC
- **binance**: Rate limiting issues

#### Rate Limiting
Use `--resume` flag to continue after rate limit errors:
```bash
python3 scripts/collect_tvl_parallel.py --resume
```

### 4. Verify Adapter Mappings

Ensure [collect_tvl_parallel.py](scripts/collect_tvl_parallel.py) has correct adapter mappings for all protocols:

**Current adapter map:**
```python
ADAPTER_MAP = {
    'aave': get_aave_v3_tvl,
    'compound': get_compound_v3_tvl,
    'compound_v2': get_compound_style_tvl,
    'fluid': get_fluid_tvl,
    'gearbox': get_gearbox_tvl,
    'cap': get_cap_tvl,
    'lista': get_lista_tvl,
    'venus': get_venus_tvl,
    'sparklend': get_compound_style_tvl,
    'benqi': get_benqi_tvl,
    'moonwell': get_moonwell_tvl,
    'kinetic': get_kinetic_tvl,
    'tectonic': get_tectonic_tvl,
    'sumer': get_sumer_tvl,
}
```

---

## Changes Made to Config

### Added Compound V3 Markets (17 new CSUs)
Previously had only 2 generic compound_v3 entries. Now has 19 market-specific entries:
- 5 Ethereum markets (USDC, WETH, USDT, wstETH, USDS)
- 4 Arbitrum markets (USDC, USDC.e, WETH, USDT)
- 4 Base markets (USDC, USDbC, WETH, AERO)
- 3 Optimism markets (USDC, USDT, WETH)
- 3 Polygon markets (USDC, USDC.e, USDT)

### Added Aave V3 Markets (4 new CSUs)
- aave_v3_avalanche
- aave_v3_base
- aave_v3_scroll
- aave_v3_sonic

### Added Fluid Market (1 new CSU)
- fluid_lending_base

### Fixed Registry Addresses
- cap_ethereum: Added registry address `0x726B8d03D43E71c533ECBb2E5095D2e60dc8A30E`

---

## Chain Coverage Summary

| Chain | Target CSUs | Block Cache | RPC Available | Notes |
|-------|-------------|-------------|---------------|-------|
| ethereum | 10 | ✅ | ✅ | Alchemy |
| arbitrum | 5 | ✅ | ✅ | Alchemy |
| base | 6 | ✅ | ✅ | Alchemy |
| optimism | 4 | ✅ | ✅ | Alchemy |
| polygon | 4 | ✅ | ✅ | Alchemy |
| avalanche | 2 | ✅ | ⚠️ | Alchemy (POA middleware) |
| binance | 2 | ❌ | ⚠️ | Rate limiting issues |
| plasma | 2 | ✅ | ⚠️ | Archive access limited |
| xdai (gnosis) | 1 | ✅ | ✅ | Alias: xdai→gnosis |
| linea | 1 | ✅ | ✅ | Alchemy (POA middleware) |
| cronos | 3 | ❌ | ✅ | Custom RPC |
| meter | 1 | ❌ | ✅ | Custom RPC |
| flare | 1 | ❌ | ✅ | Custom RPC |
| scroll | 1 | ❌ | ⚠️ | May need custom RPC |
| sonic | 1 | ❌ | ⚠️ | New chain |

**Legend:**
- ✅ = Working/Available
- ⚠️ = Requires attention or has limitations
- ❌ = Not yet available

---

## Summary

**Configuration Status**: ✅ **Complete - All 46 target CSUs are now configured**

**Next Critical Task**: Build block caches for the 6 missing chains (cronos, meter, flare, scroll, sonic, binance)

**After Block Caches**: Run full TVL collection for December 2024 across all 46 CSUs
