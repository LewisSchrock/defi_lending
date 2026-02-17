#!/usr/bin/env python3
"""
Standalone Test Script for Problematic CSUs
Tests: Gearbox, Cap, Kinetic

Usage:
    export ALCHEMY_API_KEY='your_key'
    python test_problematic_csus.py
"""

import sys
import os
from web3 import Web3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.rpc_config import get_rpc_url
from adapters.tvl.gearbox import get_gearbox_tvl
from adapters.tvl.cap import get_cap_tvl
from adapters.tvl.compound_v2_style import get_compound_v2_tvl


def test_gearbox():
    """Test Gearbox Ethereum"""
    print("=" * 60)
    print("Testing: Gearbox (Ethereum)")
    print("=" * 60)
    
    try:
        rpc = get_rpc_url('ethereum')
        w3 = Web3(Web3.HTTPProvider(rpc))
        
        # Gearbox AddressProvider
        registry = '0xcF64698AFF7E5f27A11dff868AF228653ba53be0'
        
        print(f"Chain: ethereum")
        print(f"Registry: {registry}")
        print(f"RPC: {rpc[:50]}...")
        
        latest_block = w3.eth.block_number
        print(f"Latest block: {latest_block}")
        
        results = get_gearbox_tvl(w3, registry, latest_block)
        
        if results:
            print(f"\n✅ SUCCESS - Found {len(results)} active Credit Managers")
            
            # Show first few
            for i, row in enumerate(results[:3]):
                print(f"\nCredit Manager {i+1}:")
                print(f"  Pool: {row['pool']}")
                print(f"  Token: {row['underlying_symbol']}")
                print(f"  Total Assets: {row['total_assets_raw'] / 10**row['underlying_decimals']:.2f}")
                print(f"  Total Borrowed: {row['total_borrowed_raw'] / 10**row['underlying_decimals']:.2f}")
            
            if len(results) > 3:
                print(f"\n... and {len(results) - 3} more Credit Managers")
                
        else:
            print("\n❌ FAILED - No data returned")
            
    except Exception as e:
        print(f"\n❌ FAILED - Error: {e}")
        import traceback
        traceback.print_exc()


def test_cap():
    """Test Cap Ethereum"""
    print("\n" + "=" * 60)
    print("Testing: Cap (Ethereum)")
    print("=" * 60)
    
    try:
        rpc = get_rpc_url('ethereum')
        w3 = Web3(Web3.HTTPProvider(rpc))
        
        # Cap vault (corrected address)
        registry = '0x3Ed6aa32c930253fc990dE58fF882B9186cd0072'
        
        print(f"Chain: ethereum")
        print(f"Vault: {registry}")
        print(f"RPC: {rpc[:50]}...")
        
        latest_block = w3.eth.block_number
        print(f"Latest block: {latest_block}")
        
        results = get_cap_tvl(w3, registry, latest_block)
        
        if results:
            print(f"\n✅ SUCCESS - Found {len(results)} vault(s)")
            
            row = results[0]
            print(f"\nVault Details:")
            print(f"  Vault: {row['vault']}")
            print(f"  Underlying: {row['underlying_symbol']}")
            print(f"  Debt Token: {row['debt_token']}")
            print(f"  Total Assets: {row['total_assets_raw'] / 10**row['underlying_decimals']:.2f}")
            print(f"  Total Idle: {row['total_idle_raw'] / 10**row['underlying_decimals']:.2f}")
            print(f"  Total Debt (internal): {row['total_debt_raw'] / 10**row['underlying_decimals']:.2f}")
            print(f"  Total Borrowed (debt token): {row['total_borrowed_raw'] / 10**row['underlying_decimals']:.2f}")
            print(f"  Available Liquidity: {row['available_liquidity_raw'] / 10**row['underlying_decimals']:.2f}")
            
        else:
            print("\n❌ FAILED - No data returned")
            
    except Exception as e:
        print(f"\n❌ FAILED - Error: {e}")
        import traceback
        traceback.print_exc()


def test_kinetic():
    """Test Kinetic Flare"""
    print("\n" + "=" * 60)
    print("Testing: Kinetic (Flare)")
    print("=" * 60)
    
    try:
        rpc = get_rpc_url('flare')
        w3 = Web3(Web3.HTTPProvider(rpc))
        
        # Kinetic Comptroller
        registry = '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419'
        
        print(f"Chain: flare")
        print(f"Comptroller: {registry}")
        print(f"RPC: {rpc}")
        
        latest_block = w3.eth.block_number
        print(f"Latest block: {latest_block}")
        
        results = get_compound_v2_tvl(w3, registry, latest_block)
        
        if results:
            print(f"\n✅ SUCCESS - Found {len(results)} markets")
            
            # Show first few
            for i, row in enumerate(results[:3]):
                print(f"\nMarket {i+1}:")
                print(f"  cToken: {row['ctoken'][:10]}...")
                print(f"  Symbol: {row['symbol']}")
                print(f"  Total Supply: {row['total_supply_raw'] / 10**row['decimals']:.2f}")
                print(f"  Total Borrow: {row['total_borrow_raw'] / 10**row['decimals']:.2f}")
            
            if len(results) > 3:
                print(f"\n... and {len(results) - 3} more markets")
                
        else:
            print("\n❌ FAILED - No data returned")
            
    except Exception as e:
        print(f"\n❌ FAILED - Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  STANDALONE TEST: Problematic CSUs".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Check API key
    api_key = os.environ.get('ALCHEMY_API_KEY')
    if not api_key:
        print("⚠️  WARNING: ALCHEMY_API_KEY not set")
        print("   Some tests may fail without it")
        print()
    
    # Run tests
    test_gearbox()
    test_cap()
    test_kinetic()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("\nIf all tests show ✅ SUCCESS, the issues are fixed!")
    print("\nExpected outcomes:")
    print("  1. Gearbox: ~23 active Credit Managers (some failed silently)")
    print("  2. Cap: 1 vault with totalAssets, totalIdle, totalDebt")
    print("  3. Kinetic: Multiple cToken markets")
    print()


if __name__ == '__main__':
    main()
