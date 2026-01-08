#!/usr/bin/env python3
"""
Alchemy Key-Chain Mapping Test

Tests each API key individually against all chains to determine which
keys have access to which chains. Creates a mapping file for optimized
connection pool configuration.

Usage:
    python3 scripts/test_key_mapping.py
"""

import os
import sys
from pathlib import Path
import json
from web3 import Web3
from typing import Dict, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load API keys from environment
ALCHEMY_KEYS = {
    'key_1': os.environ.get('ALCHEMY_KEY_1'),
    'key_2': os.environ.get('ALCHEMY_KEY_2'),
    'key_3': os.environ.get('ALCHEMY_KEY_3'),
    'key_4': os.environ.get('ALCHEMY_KEY_4'),
    'key_5': os.environ.get('ALCHEMY_KEY_5'),
}

# Remove None values
ALCHEMY_KEYS = {k: v for k, v in ALCHEMY_KEYS.items() if v}

# Alchemy chain patterns
ALCHEMY_CHAINS = {
    'ethereum': 'eth-mainnet',
    'arbitrum': 'arb-mainnet',
    'optimism': 'opt-mainnet',
    'base': 'base-mainnet',
    'polygon': 'polygon-mainnet',
    'avalanche': 'avax-mainnet',
    'binance': 'bnb-mainnet',
    'plasma': 'polygonzkevm-mainnet',
    'linea': 'linea-mainnet',
    'gnosis': 'gnosis-mainnet',
}


def test_key_chain(key_name: str, key_value: str, chain: str, chain_pattern: str) -> dict:
    """
    Test if a specific key can access a specific chain.
    
    Returns:
        dict with 'success', 'block', 'error'
    """
    url = f'https://{chain_pattern}.g.alchemy.com/v2/{key_value}'
    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
    
    try:
        block = w3.eth.block_number
        return {
            'success': True,
            'block': block,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'block': None,
            'error': str(e)
        }


def test_all_mappings():
    """
    Test all key-chain combinations.
    
    Returns:
        Dict mapping keys to their accessible chains
    """
    print("\n" + "="*70)
    print("ALCHEMY KEY-CHAIN MAPPING TEST")
    print("="*70 + "\n")
    
    print(f"Testing {len(ALCHEMY_KEYS)} API keys across {len(ALCHEMY_CHAINS)} chains")
    print(f"Total tests: {len(ALCHEMY_KEYS) * len(ALCHEMY_CHAINS)}\n")
    
    results = {}
    
    for key_name, key_value in ALCHEMY_KEYS.items():
        print(f"\n{'='*70}")
        print(f"Testing {key_name}: {key_value[:10]}...")
        print(f"{'='*70}\n")
        
        results[key_name] = {
            'key_value': key_value,
            'chains': {}
        }
        
        for chain, chain_pattern in ALCHEMY_CHAINS.items():
            result = test_key_chain(key_name, key_value, chain, chain_pattern)
            results[key_name]['chains'][chain] = result
            
            if result['success']:
                print(f"  ✅ {chain:15} - Block {result['block']}")
            else:
                error_msg = result['error'][:50] + "..." if len(result['error']) > 50 else result['error']
                print(f"  ❌ {chain:15} - {error_msg}")
    
    return results


def create_summary(results: dict) -> dict:
    """
    Create summary showing which chains are available and which keys work for them.
    
    Returns:
        Dict mapping chains to list of working keys
    """
    chain_to_keys = {}
    
    for chain in ALCHEMY_CHAINS.keys():
        chain_to_keys[chain] = []
        for key_name, key_data in results.items():
            if key_data['chains'][chain]['success']:
                chain_to_keys[chain].append(key_name)
    
    return chain_to_keys


def print_summary(chain_to_keys: dict):
    """Print summary of chain availability"""
    print("\n" + "="*70)
    print("SUMMARY: Chain Availability")
    print("="*70 + "\n")
    
    for chain, keys in sorted(chain_to_keys.items()):
        num_keys = len(keys)
        if num_keys > 0:
            keys_str = ", ".join(keys)
            print(f"✅ {chain:15} - {num_keys} key(s): {keys_str}")
        else:
            print(f"❌ {chain:15} - NO KEYS AVAILABLE")
    
    # Overall stats
    print("\n" + "="*70)
    print("Statistics")
    print("="*70 + "\n")
    
    total_chains = len(ALCHEMY_CHAINS)
    working_chains = sum(1 for keys in chain_to_keys.values() if len(keys) > 0)
    
    print(f"Total chains tested: {total_chains}")
    print(f"Working chains: {working_chains}/{total_chains}")
    print(f"Failed chains: {total_chains - working_chains}")
    
    # Check if all chains have at least one key
    missing_chains = [chain for chain, keys in chain_to_keys.items() if len(keys) == 0]
    if missing_chains:
        print(f"\n⚠️  WARNING: These chains have NO working keys:")
        for chain in missing_chains:
            print(f"   - {chain}")
    else:
        print(f"\n✅ All chains have at least one working key!")


def save_mapping(results: dict, chain_to_keys: dict, output_file: Path):
    """Save mapping to JSON file"""
    mapping = {
        'timestamp': str(Path(__file__).stat().st_mtime),
        'full_results': results,
        'chain_to_keys': chain_to_keys,
        'usage_instructions': {
            'description': 'This file maps each chain to available API keys',
            'chain_to_keys': 'Use this to get list of working keys for a chain',
            'full_results': 'Complete test results for debugging'
        }
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\n✅ Saved mapping to: {output_file}")


def create_optimized_pool_config(chain_to_keys: dict, output_file: Path):
    """
    Create optimized rpc_pool configuration that only uses working keys.
    """
    config_template = '''"""
Optimized RPC Pool Configuration

Auto-generated from test_key_mapping.py
Only includes keys that have been verified to work for each chain.
"""

# Key-to-chain mapping (auto-generated)
CHAIN_KEY_MAPPING = {mapping}

def get_keys_for_chain(chain: str) -> list:
    """Get list of working API key names for a chain"""
    return CHAIN_KEY_MAPPING.get(chain, [])
'''
    
    config_content = config_template.format(
        mapping=json.dumps(chain_to_keys, indent=4)
    )
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Saved optimized config to: {output_file}")


def main():
    # Check if keys are loaded
    if len(ALCHEMY_KEYS) == 0:
        print("❌ ERROR: No API keys found!")
        print("   Make sure you ran: source .env")
        print("   Test with: echo $ALCHEMY_KEY_1")
        sys.exit(1)
    
    print(f"Found {len(ALCHEMY_KEYS)} API keys to test")
    
    # Run tests
    results = test_all_mappings()
    
    # Create summary
    chain_to_keys = create_summary(results)
    print_summary(chain_to_keys)
    
    # Save results
    output_dir = Path('data/config')
    save_mapping(results, chain_to_keys, output_dir / 'key_chain_mapping.json')
    create_optimized_pool_config(chain_to_keys, output_dir / 'optimized_pool_config.py')
    
    # Final recommendations
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70 + "\n")
    
    # Check for chains with only 1 key
    single_key_chains = [chain for chain, keys in chain_to_keys.items() if len(keys) == 1]
    if single_key_chains:
        print("⚠️  These chains only have 1 working key (may hit rate limits):")
        for chain in single_key_chains:
            print(f"   - {chain} (key: {chain_to_keys[chain][0]})")
    
    # Check for chains with multiple keys
    multi_key_chains = [chain for chain, keys in chain_to_keys.items() if len(keys) > 1]
    if multi_key_chains:
        print(f"\n✅ These chains have multiple keys (good for load distribution):")
        for chain in multi_key_chains:
            print(f"   - {chain} ({len(chain_to_keys[chain])} keys)")
    
    print("\n" + "="*70)
    print("✅ Mapping test complete!")
    print("="*70 + "\n")
    
    print("Next steps:")
    print("1. Review: data/config/key_chain_mapping.json")
    print("2. Update config/rpc_pool.py to use this mapping")
    print("3. Continue with: python3 scripts/build_block_cache.py")


if __name__ == '__main__':
    main()
