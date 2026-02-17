"""
Simplified testing framework for thesis_v2.
Based on patterns from original sandbox.py but cleaner and more organized.

Usage:
    python scripts/test_single_csu.py aave_v3_ethereum --tvl
    python scripts/test_single_csu.py aave_v3_ethereum --liquidations --blocks 10000
"""

import argparse
import sys
from pathlib import Path
from pprint import pprint
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.rpc_config import get_rpc_url


# CSU Configuration
# Organized by protocol architecture
CSU_CONFIG = {
    # ===== Aave V3-style (10 CSUs) =====
    'aave_v3_ethereum': {
        'protocol': 'aave_v3',
        'chain': 'ethereum',
        'registry': '0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e',
    },
    
    # ===== Compound V3 (3 CSUs) =====
    'compound_v3_ethereum': {
        'protocol': 'compound_v3',
        'chain': 'ethereum',
        'registry': '0xc3d688B66703497DAA19211EEdff47f25384cdc3',
    },
    'compound_v3_arbitrum': {
        'protocol': 'compound_v3',
        'chain': 'arbitrum',
        'registry': '0xa5EDBDD9646f8dFFBf0e057b274Bdb8E11D2f8E0',
    },
    'compound_v3_base': {
        'protocol': 'compound_v3',
        'chain': 'base',
        'registry': '0xb125E6687d4313864e53df431d5425969c15Eb2F',
    },
    
    # ===== Fluid (4 CSUs) =====
    'fluid_ethereum': {
        'protocol': 'fluid',
        'chain': 'ethereum',
        'registry': '0xC215485C572365AE87f908ad35233EC2572A3BEC',
        'liq_registry': '0x129aFd8dde3b96Ea01f847CD4e5B59786A91E4d3',
    },
    'fluid_plasma': {
        'protocol': 'fluid',
        'chain': 'plasma',
        'registry': '0xfbb7005c49520a4E54746487f0b28F4E4594b293',
        'liq_registry': '0x2Ac57990Df31501d7Cf3453528fd103ec54A3750',
    },
    'fluid_arbitrum': {
        'protocol': 'fluid',
        'chain': 'arbitrum',
        'registry': '0xdF4d3272FfAE8036d9a2E1626Df2Db5863b4b302',
        'liq_registry': '0x4D900e473785d09995D4f12e2c12Fa37D5BAda48',
    },
    'fluid_base': {
        'protocol': 'fluid',
        'chain': 'base',
        'registry': '0xdF4d3272FfAE8036d9a2E1626Df2Db5863b4b302',
        'liq_registry': '0x4D900e473785d09995D4f12e2c12Fa37D5BAda48',
    },
    
    # ===== Compound V2-style protocols (7 CSUs) =====
    'venus_binance': {
        'protocol': 'venus',
        'chain': 'binance',
        'registry': '0xfd36e2c2a6789db23113685031d7f16329158384',
    },
    'benqi_avalanche': {
        'protocol': 'benqi',
        'chain': 'avalanche',
        'registry': '0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4',
    },
    'moonwell_base': {
        'protocol': 'moonwell',
        'chain': 'base',
        'registry': '0xfBb21d0380beE3312B33c4353c8936a0F13EF26C',
    },
    'kinetic_flare': {
        'protocol': 'kinetic',
        'chain': 'flare',
        'registry': '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',  # TODO: Verify
    },
    'tectonic_main_cronos': {
        'protocol': 'tectonic',
        'chain': 'cronos',
        'registry': '0xb3831584acb95ED9cCb0C11f677B5AD01DeaeEc0',  # Main market
    },
    'tectonic_vero_cronos': {
        'protocol': 'tectonic',
        'chain': 'cronos',
        'registry': '0xb3831584acb95ED9cCb0C11f677B5AD01DeaeEc0',  # Vero market (same comptroller?)
    },
    'tectonic_defi_cronos': {
        'protocol': 'tectonic',
        'chain': 'cronos',
        'registry': '0xb3831584acb95ED9cCb0C11f677B5AD01DeaeEc0',  # DeFi market (same comptroller?)
    },
    'sumer_core': {
        'protocol': 'sumer',
        'chain': 'core',
        'registry': '0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B',  # TODO: Verify
    },
    
    # ===== Aave V3 forks (2 CSUs) =====
    'sparklend_ethereum': {
        'protocol': 'sparklend',
        'chain': 'ethereum',
        'registry': '0x02C3eA4e34C0cBd694D2adFa2c690EECbC1793eE',
    },
    'tydro_ink': {
        'protocol': 'tydro',
        'chain': 'ink',
        'registry': '0x...', # TODO: Need ink registry address
    },
    
    # ===== Unique protocols (3 CSUs) =====
    'lista_binance': {
        'protocol': 'lista',
        'chain': 'binance',
        'registry': '0x8F73b65B4caAf64FBA2aF91cC5D4a2A1318E5D8C',  # Moolah
        'vaults': [
            '0x834e8641d7422fe7c19a56d05516ed877b3d01e0',
            '0x3036929665c69358fc092ee726448ed9c096014f',
            '0x724205704cd9384793e0baf3426d5dde8cf9b1b4',
        ],
    },
    'gearbox_ethereum': {
        'protocol': 'gearbox',
        'chain': 'ethereum',
        'registry': '0xcF64698AFF7E5f27A11dff868AF228653ba53be0',  # AddressProvider
    },
    'cap_ethereum': {
        'protocol': 'cap',
        'chain': 'ethereum',
        'registry': '0x8dee5bf2e5e68ab80cc00c3bb7fb7577ec719e04',  # USDC vault
    },
}


def setup_web3(chain: str) -> Web3:
    """Create Web3 instance for a chain."""
    rpc_url = get_rpc_url(chain)
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
    
    # Add POA middleware for some chains
    if chain in ['binance', 'polygon', 'xdai']:
        try:
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        except Exception:
            pass
    
    return w3


def test_tvl(csu_key: str):
    """Test TVL extraction for a CSU."""
    print(f"\n{'='*60}")
    print(f"Testing TVL: {csu_key}")
    print('='*60)
    
    config = CSU_CONFIG.get(csu_key)
    if not config:
        print(f"❌ CSU '{csu_key}' not found in config")
        return
    
    protocol = config['protocol']
    chain = config['chain']
    
    print(f"Protocol: {protocol}")
    print(f"Chain: {chain}")
    print(f"Registry: {config.get('registry', 'N/A')}")
    
    # Create Web3 instance
    w3 = setup_web3(chain)
    latest_block = w3.eth.block_number
    print(f"Latest block: {latest_block:,}")
    
    # Import and run adapter
    try:
        if protocol == 'aave_v3':
            from adapters.tvl.aave_v3 import get_aave_v3_tvl
            rows = get_aave_v3_tvl(w3, config['registry'], latest_block)
        elif protocol == 'compound_v3':
            from adapters.tvl.compound_v3 import get_compound_v3_tvl
            rows = get_compound_v3_tvl(w3, config['registry'], latest_block)
        elif protocol == 'fluid':
            from adapters.tvl.fluid import get_fluid_tvl
            rows = get_fluid_tvl(w3, config['registry'], latest_block)
        elif protocol in ['venus', 'benqi', 'moonwell', 'kinetic', 'tectonic', 'sumer']:
            # All use generic Compound V2-style adapter
            from adapters.tvl.compound_v2_style import get_compound_style_tvl
            rows = get_compound_style_tvl(w3, config['registry'], latest_block, 
                                         token_prefix=f"{protocol}Token")
        elif protocol == 'sparklend':
            # SparkLend is Aave V3 fork - use same adapter
            from adapters.tvl.aave_v3 import get_aave_v3_tvl
            rows = get_aave_v3_tvl(w3, config['registry'], latest_block)
        elif protocol == 'tydro':
            # Tydro is Aave V3 fork - use same adapter
            from adapters.tvl.aave_v3 import get_aave_v3_tvl
            rows = get_aave_v3_tvl(w3, config['registry'], latest_block)
        elif protocol == 'lista':
            from adapters.tvl.lista import get_lista_tvl
            vaults = config.get('vaults', [])
            rows = get_lista_tvl(w3, config['registry'], vaults, latest_block)
        elif protocol == 'gearbox':
            from adapters.tvl.gearbox import get_gearbox_tvl
            rows = get_gearbox_tvl(w3, config['registry'], latest_block)
        elif protocol == 'cap':
            from adapters.tvl.cap import get_cap_tvl
            rows = get_cap_tvl(w3, config['registry'], latest_block)
        else:
            print(f"❌ No TVL adapter for protocol: {protocol} (unique architecture - TODO)")
            return
        
        print(f"\n✅ Success! Found {len(rows)} markets")
        if rows:
            print("\nFirst market:")
            pprint(rows[0])
            
            if len(rows) > 1:
                print(f"\n... and {len(rows)-1} more markets")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_liquidations(csu_key: str, n_blocks: int = 10000):
    """Test liquidation extraction for a CSU."""
    print(f"\n{'='*60}")
    print(f"Testing Liquidations: {csu_key}")
    print('='*60)
    
    config = CSU_CONFIG.get(csu_key)
    if not config:
        print(f"❌ CSU '{csu_key}' not found in config")
        return
    
    protocol = config['protocol']
    chain = config['chain']
    
    print(f"Protocol: {protocol}")
    print(f"Chain: {chain}")
    print(f"Scanning last {n_blocks:,} blocks...")
    
    # Create Web3 instance
    w3 = setup_web3(chain)
    latest_block = w3.eth.block_number
    from_block = max(latest_block - n_blocks, 0)
    
    print(f"Block range: [{from_block:,}, {latest_block:,}]")
    
    # Import and run adapter
    try:
        if protocol == 'aave_v3':
            from adapters.liquidations.aave_v3 import scan_aave_liquidations
            events = scan_aave_liquidations(w3, config['registry'], from_block, latest_block, 
                                           chunk_size=10, pace_seconds=0.1)
        elif protocol == 'compound_v3':
            from adapters.liquidations.compound_v3 import scan_compound_v3_liquidations
            events = scan_compound_v3_liquidations(w3, config['registry'], from_block, latest_block,
                                                   chunk_size=10, pace_seconds=0.1)
        elif protocol == 'fluid':
            from adapters.liquidations.fluid import scan_fluid_liquidations
            liq_contract = config.get('liq_registry', config['registry'])
            events = scan_fluid_liquidations(w3, liq_contract, from_block, latest_block,
                                            chunk_size=10, pace_seconds=0.1)
        elif protocol in ['venus', 'benqi', 'moonwell', 'kinetic', 'tectonic', 'sumer']:
            # All use generic Compound V2-style adapter
            from adapters.liquidations.compound_v2_style import scan_compound_style_liquidations
            events = scan_compound_style_liquidations(w3, config['registry'], from_block, latest_block,
                                                     chunk_size=10, pace_seconds=0.1)
        elif protocol == 'sparklend':
            # SparkLend is Aave V3 fork - use same adapter
            from adapters.liquidations.aave_v3 import scan_aave_liquidations
            events = scan_aave_liquidations(w3, config['registry'], from_block, latest_block,
                                           chunk_size=10, pace_seconds=0.1)
        elif protocol == 'tydro':
            # Tydro is Aave V3 fork - use same adapter
            from adapters.liquidations.aave_v3 import scan_aave_liquidations
            events = scan_aave_liquidations(w3, config['registry'], from_block, latest_block,
                                           chunk_size=10, pace_seconds=0.1)
        elif protocol == 'lista':
            from adapters.liquidations.lista import scan_lista_liquidations
            events = scan_lista_liquidations(w3, config['registry'], from_block, latest_block,
                                            chunk_size=10, pace_seconds=0.1)
        elif protocol == 'gearbox':
            from adapters.liquidations.gearbox import scan_gearbox_liquidations
            events = scan_gearbox_liquidations(w3, config['registry'], from_block, latest_block,
                                              chunk_size=10, pace_seconds=0.1)
        elif protocol == 'cap':
            from adapters.liquidations.cap import scan_cap_liquidations
            events = scan_cap_liquidations(w3, config['registry'], from_block, latest_block,
                                          chunk_size=10, pace_seconds=0.1)
        else:
            print(f"❌ No liquidation adapter for protocol: {protocol} (unique architecture - TODO)")
            return
        
        print(f"\n✅ Success! Found {len(events)} liquidation events")
        if events:
            print("\nFirst event:")
            pprint(events[0])
            
            if len(events) > 1:
                print(f"\n... and {len(events)-1} more events")
        else:
            print("\nNo liquidations found in this range (may be expected)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='Test single CSU data collection')
    parser.add_argument('csu', help='CSU key (e.g., aave_v3_ethereum)')
    parser.add_argument('--tvl', action='store_true', help='Test TVL extraction')
    parser.add_argument('--liquidations', action='store_true', help='Test liquidation extraction')
    parser.add_argument('--blocks', type=int, default=10000, 
                       help='Number of blocks to scan for liquidations (default: 10000)')
    
    args = parser.parse_args()
    
    # Default to TVL if no flags specified
    if not args.tvl and not args.liquidations:
        args.tvl = True
    
    if args.tvl:
        test_tvl(args.csu)
    
    if args.liquidations:
        test_liquidations(args.csu, args.blocks)


if __name__ == '__main__':
    main()
