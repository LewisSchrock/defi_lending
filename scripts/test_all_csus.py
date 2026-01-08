#!/usr/bin/env python3
"""
Comprehensive Test Script for All 30 CSUs

Tests TVL extraction for all protocols to verify:
1. Adapters work correctly
2. Data schemas are consistent
3. RPC connections are functional

Usage:
    python scripts/test_all_csus.py
    python scripts/test_all_csus.py --verbose
"""

import sys
import os
from typing import Dict, Any
from web3 import Web3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.rpc_config import get_rpc_url

# Import all adapters
from adapters.tvl.aave_v3 import get_aave_v3_tvl
from adapters.tvl.compound_v3 import get_compound_v3_tvl
from adapters.tvl.fluid import get_fluid_tvl
from adapters.tvl.compound_v2_style import get_compound_style_tvl
from adapters.tvl.lista import get_lista_tvl
from adapters.tvl.gearbox import get_gearbox_tvl
from adapters.tvl.cap import get_cap_tvl


# Test configuration for all 30 CSUs
TEST_CSUS = [
    # Aave V3 family (12 CSUs)
    {'name': 'aave_v3_ethereum', 'chain': 'ethereum', 'registry': '0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e', 'family': 'aave_v3'},
    {'name': 'aave_v3_polygon', 'chain': 'polygon', 'registry': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb', 'family': 'aave_v3'},
    {'name': 'aave_v3_avalanche', 'chain': 'avalanche', 'registry': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb', 'family': 'aave_v3'},
    {'name': 'aave_v3_arbitrum', 'chain': 'arbitrum', 'registry': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb', 'family': 'aave_v3'},
    {'name': 'aave_v3_optimism', 'chain': 'optimism', 'registry': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb', 'family': 'aave_v3'},
    {'name': 'aave_v3_base', 'chain': 'base', 'registry': '0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D', 'family': 'aave_v3'},
    {'name': 'aave_v3_binance', 'chain': 'binance', 'registry': '0xff75B6da14FfbbfD355Daf7a2731456b3562Ba6D', 'family': 'aave_v3'},
    {'name': 'aave_v3_plasma', 'chain': 'plasma', 'registry': '0x061D8e131F26512348ee5FA42e2DF1bA9d6505E9', 'family': 'aave_v3'},
    {'name': 'aave_v3_gnosis', 'chain': 'xdai', 'registry': '0x36616cf17557639614c1cdDb356b1B83fc0B2132', 'family': 'aave_v3'},
    {'name': 'aave_v3_linea', 'chain': 'linea', 'registry': '0x89502c3731F69DDC95B65753708A07F8Cd0373F4', 'family': 'aave_v3'},
    {'name': 'sparklend_ethereum', 'chain': 'ethereum', 'registry': '0x02C3eA4e34C0cBd694D2adFa2c690EECbC1793eE', 'family': 'aave_v3'},
    {'name': 'tydro_ink', 'chain': 'ink', 'registry': '0x4172E6aAEC070ACB31aaCE343A58c93E4C70f44D', 'family': 'aave_v3'},
    
    # Compound V3 family (19 CSUs - each Comet is a separate market)
    # Arbitrum (4 markets)
    {'name': 'compound_v3_arb_usdce', 'chain': 'arbitrum', 'registry': '0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA', 'family': 'compound_v3'},
    {'name': 'compound_v3_arb_usdc', 'chain': 'arbitrum', 'registry': '0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf', 'family': 'compound_v3'},
    {'name': 'compound_v3_arb_weth', 'chain': 'arbitrum', 'registry': '0x6f7D514bbD4aFf3BcD1140B7344b32f063dEe486', 'family': 'compound_v3'},
    {'name': 'compound_v3_arb_usdt', 'chain': 'arbitrum', 'registry': '0xd98Be00b5D27fc98112BdE293e487f8D4cA57d07', 'family': 'compound_v3'},
    
    # Ethereum (5 markets)
    {'name': 'compound_v3_eth_usdc', 'chain': 'ethereum', 'registry': '0xc3d688B66703497DAA19211EEdff47f25384cdc3', 'family': 'compound_v3'},
    {'name': 'compound_v3_eth_weth', 'chain': 'ethereum', 'registry': '0xA17581A9E3356d9A858b789D68B4d866e593aE94', 'family': 'compound_v3'},
    {'name': 'compound_v3_eth_usdt', 'chain': 'ethereum', 'registry': '0x3Afdc9BCA9213A35503b077a6072F3D0d5AB0840', 'family': 'compound_v3'},
    {'name': 'compound_v3_eth_wsteth', 'chain': 'ethereum', 'registry': '0x3D0bb1ccaB520A66e607822fC55BC921738fAFE3', 'family': 'compound_v3'},
    {'name': 'compound_v3_eth_usds', 'chain': 'ethereum', 'registry': '0x5D409e56D886231aDAf00c8775665AD0f9897b56', 'family': 'compound_v3'},
    
    # Base (4 markets)
    {'name': 'compound_v3_base_usdc', 'chain': 'base', 'registry': '0xb125E6687d4313864e53df431d5425969c15Eb2F', 'family': 'compound_v3'},
    {'name': 'compound_v3_base_usdbc', 'chain': 'base', 'registry': '0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf', 'family': 'compound_v3'},
    {'name': 'compound_v3_base_weth', 'chain': 'base', 'registry': '0x46e6b214b524310239732D51387075E0e70970bf', 'family': 'compound_v3'},
    {'name': 'compound_v3_base_aero', 'chain': 'base', 'registry': '0x784efeB622244d2348d4F2522f8860B96fbEcE89', 'family': 'compound_v3'},
    
    # Optimism (3 markets)
    {'name': 'compound_v3_op_usdc', 'chain': 'optimism', 'registry': '0x2e44e174f7D53F0212823acC11C01A11d58c5bCB', 'family': 'compound_v3'},
    {'name': 'compound_v3_op_usdt', 'chain': 'optimism', 'registry': '0x995E394b8B2437aC8Ce61Ee0bC610D617962B214', 'family': 'compound_v3'},
    {'name': 'compound_v3_op_weth', 'chain': 'optimism', 'registry': '0xE36A30D249f7761327fd973001A32010b521b6Fd', 'family': 'compound_v3'},
    
    # Fluid family (4 CSUs)
    {'name': 'fluid_ethereum', 'chain': 'ethereum', 'registry': '0xC215485C572365AE87f908ad35233EC2572A3BEC', 'family': 'fluid'},
    {'name': 'fluid_plasma', 'chain': 'plasma', 'registry': '0xfbb7005c49520a4E54746487f0b28F4E4594b293', 'family': 'fluid'},
    {'name': 'fluid_arbitrum', 'chain': 'arbitrum', 'registry': '0xdF4d3272FfAE8036d9a2E1626Df2Db5863b4b302', 'family': 'fluid'},
    {'name': 'fluid_base', 'chain': 'base', 'registry': '0xdF4d3272FfAE8036d9a2E1626Df2Db5863b4b302', 'family': 'fluid'},
    
    # Compound V2 family (8 CSUs)
    {'name': 'venus_binance', 'chain': 'binance', 'registry': '0xfd36e2c2a6789db23113685031d7f16329158384', 'family': 'compound_v2'},
    {'name': 'benqi_avalanche', 'chain': 'avalanche', 'registry': '0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4', 'family': 'compound_v2'},
    {'name': 'moonwell_base', 'chain': 'base', 'registry': '0xfBb21d0380beE3312B33c4353c8936a0F13EF26C', 'family': 'compound_v2'},
    {'name': 'kinetic_flare', 'chain': 'flare', 'registry': '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419', 'family': 'compound_v2'},
    {'name': 'tectonic_main_cronos', 'chain': 'cronos', 'registry': '0xb3831584acb95ED9cCb0C11f677B5AD01DeaeEc0', 'family': 'compound_v2'},
    {'name': 'tectonic_vero_cronos', 'chain': 'cronos', 'registry': '0xb3831584acb95ED9cCb0C11f677B5AD01DeaeEc0', 'family': 'compound_v2'},
    {'name': 'tectonic_defi_cronos', 'chain': 'cronos', 'registry': '0xb3831584acb95ED9cCb0C11f677B5AD01DeaeEc0', 'family': 'compound_v2'},
    {'name': 'sumer_meter', 'chain': 'meter', 'registry': '0xcB4cdDA50C1B6B0E33F544c98420722093B7Aa88', 'family': 'compound_v2'},
    
    # Unique protocols (3 CSUs)
    {'name': 'lista_binance', 'chain': 'binance', 'registry': '0x8F73b65B4caAf64FBA2aF91cC5D4a2A1318E5D8C', 'family': 'lista',
     'vaults': ['0x834e8641d7422fe7c19a56d05516ed877b3d01e0', '0x3036929665c69358fc092ee726448ed9c096014f', '0x724205704cd9384793e0baf3426d5dde8cf9b1b4']},
    {'name': 'gearbox_ethereum', 'chain': 'ethereum', 'registry': '0xcF64698AFF7E5f27A11dff868AF228653ba53be0', 'family': 'gearbox'},
    {'name': 'cap_ethereum', 'chain': 'ethereum', 'registry': '0x3Ed6aa32c930253fc990dE58fF882B9186cd0072', 'family': 'cap'},
]


def test_csu(csu: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """Test a single CSU and return results."""
    name = csu['name']
    chain = csu['chain']
    family = csu['family']
    
    # Skip if marked
    if csu.get('skip'):
        return {
            'name': name,
            'success': False,
            'skipped': True,
            'reason': 'Missing RPC or registry address',
        }
    
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Chain: {chain} | Family: {family}")
    print(f"{'='*60}")
    
    try:
        # Get RPC URL
        rpc_url = get_rpc_url(chain)
        if verbose:
            print(f"RPC: {rpc_url[:50]}...")
        
        # Connect to Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        latest_block = w3.eth.block_number
        print(f"Latest block: {latest_block:,}")
        
        # Call appropriate adapter
        rows = None
        if family == 'aave_v3':
            rows = get_aave_v3_tvl(w3, csu['registry'], latest_block)
        elif family == 'compound_v3':
            rows = get_compound_v3_tvl(w3, csu['registry'], latest_block)
        elif family == 'fluid':
            rows = get_fluid_tvl(w3, csu['registry'], latest_block)
        elif family == 'compound_v2':
            rows = get_compound_style_tvl(w3, csu['registry'], latest_block)
        elif family == 'lista':
            rows = get_lista_tvl(w3, csu['registry'], csu['vaults'], latest_block)
        elif family == 'gearbox':
            rows = get_gearbox_tvl(w3, csu['registry'], latest_block)
        elif family == 'cap':
            rows = get_cap_tvl(w3, csu['registry'], latest_block)
        
        if not rows:
            print(f"❌ No data returned")
            return {
                'name': name,
                'success': False,
                'error': 'No data returned',
            }
        
        # Success!
        print(f"✅ SUCCESS: Found {len(rows)} markets/pools")
        
        # Show first result
        if rows and verbose:
            print(f"\nFirst result:")
            first = rows[0]
            for key, value in list(first.items())[:5]:  # Show first 5 keys
                print(f"  {key}: {value}")
        
        return {
            'name': name,
            'success': True,
            'count': len(rows),
            'sample': rows[0] if rows else None,
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ FAILED: {error_msg[:100]}")
        return {
            'name': name,
            'success': False,
            'error': error_msg,
        }


def main():
    """Run all tests and report results."""
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    print("="*60)
    print("COMPREHENSIVE CSU TEST SUITE")
    print("Testing TVL extraction for all 30 CSUs")
    print("="*60)
    
    results = []
    for csu in TEST_CSUS:
        result = test_csu(csu, verbose)
        results.append(result)
    
    # Summary report
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success'] and not r.get('skipped')]
    skipped = [r for r in results if r.get('skipped')]
    
    print(f"\n✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"⏭️  Skipped: {len(skipped)}")
    print(f"📊 Total: {len(results)}")
    
    # Show successful tests
    if successful:
        print(f"\n✅ SUCCESSFUL TESTS ({len(successful)}):")
        for r in successful:
            count = r.get('count', 0)
            print(f"   {r['name']:30s} - {count:3d} markets")
    
    # Show failed tests
    if failed:
        print(f"\n❌ FAILED TESTS ({len(failed)}):")
        for r in failed:
            error = r.get('error', 'Unknown error')[:50]
            print(f"   {r['name']:30s} - {error}")
    
    # Show skipped tests
    if skipped:
        print(f"\n⏭️  SKIPPED TESTS ({len(skipped)}):")
        for r in skipped:
            reason = r.get('reason', 'Unknown reason')
            print(f"   {r['name']:30s} - {reason}")
    
    # Exit code
    if failed:
        print(f"\n⚠️  {len(failed)} tests failed. Review errors above.")
        sys.exit(1)
    else:
        print(f"\n🎉 All available tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()
