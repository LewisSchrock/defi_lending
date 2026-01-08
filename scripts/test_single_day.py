#!/usr/bin/env python3
"""
Single Day Collection Test

Tests TVL collection for one CSU on one day.
Validates RPC pool, block cache, and adapter work correctly.

Usage:
    python scripts/test_single_day.py --csu aave_v3_ethereum --date 2024-12-31
"""

import sys
import os
from pathlib import Path
import json
import argparse
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.rpc_pool import get_web3
from config.utils.time import ny_date_to_utc_window
from config.utils.block import block_for_ts

# Import adapters
from adapters.tvl.aave_v3 import get_aave_v3_tvl
from adapters.tvl.compound_v3 import get_compound_v3_tvl
from adapters.tvl.compound_v2_style import get_compound_style_tvl
from adapters.tvl.fluid import get_fluid_tvl
from adapters.tvl.lista import get_lista_tvl
from adapters.tvl.gearbox import get_gearbox_tvl
from adapters.tvl.cap import get_cap_tvl


# CSU configurations
CSUS = {
    'aave_v3_ethereum': {'chain': 'ethereum', 'registry': '0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e', 'family': 'aave_v3'},
    'aave_v3_arbitrum': {'chain': 'arbitrum', 'registry': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb', 'family': 'aave_v3'},
    'compound_v3_eth_usdc': {'chain': 'ethereum', 'registry': '0xc3d688B66703497DAA19211EEdff47f25384cdc3', 'family': 'compound_v3'},
    'fluid_ethereum': {'chain': 'ethereum', 'registry': '0xC215485C572365AE87f908ad35233EC2572A3BEC', 'family': 'fluid'},
}


def get_snapshot_block(w3, date_str: str, use_cache: bool = True) -> int:
    """
    Get block number for end-of-day snapshot.
    
    Args:
        w3: Web3 instance
        date_str: Date string (YYYY-MM-DD)
        use_cache: Try to load from cache first
        
    Returns:
        Block number for snapshot
    """
    # Try cache first
    if use_cache:
        cache_dir = Path('data/cache')
        cache_files = list(cache_dir.glob('*_blocks_*.json'))
        
        for cache_file in cache_files:
            try:
                with open(cache_file) as f:
                    cache = json.load(f)
                    if date_str in cache:
                        block = cache[date_str]['block']
                        print(f"   Using cached block: {block}")
                        return block
            except:
                continue
    
    # Not in cache, compute it
    print(f"   Computing block number (not in cache)...")
    ts_start_utc, ts_end_utc = ny_date_to_utc_window(date_str)
    block_num = block_for_ts(w3, ts_end_utc)
    return max(1, block_num - 1)


def collect_tvl(csu_name: str, date_str: str, output_dir: Path):
    """
    Collect TVL for one CSU on one date.
    
    Args:
        csu_name: CSU name (e.g., 'aave_v3_ethereum')
        date_str: Date (YYYY-MM-DD)
        output_dir: Where to save bronze data
    """
    print(f"\n{'='*60}")
    print(f"Collecting TVL: {csu_name} on {date_str}")
    print(f"{'='*60}\n")
    
    # Get CSU config
    if csu_name not in CSUS:
        print(f"❌ Unknown CSU: {csu_name}")
        print(f"   Available: {', '.join(CSUS.keys())}")
        return
    
    csu = CSUS[csu_name]
    chain = csu['chain']
    registry = csu['registry']
    family = csu['family']
    
    print(f"CSU: {csu_name}")
    print(f"Chain: {chain}")
    print(f"Registry: {registry}")
    print(f"Family: {family}")
    print(f"Date: {date_str}\n")
    
    # Get Web3 connection
    print("Connecting to RPC...")
    w3 = get_web3(chain)
    
    try:
        latest = w3.eth.block_number
        print(f"✅ Connected: latest block = {latest}\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}\n")
        return
    
    # Get snapshot block
    print("Getting snapshot block...")
    try:
        block = get_snapshot_block(w3, date_str)
        print(f"✅ Snapshot block: {block}\n")
    except Exception as e:
        print(f"❌ Failed to get block: {e}\n")
        return
    
    # Collect TVL
    print("Collecting TVL data...")
    try:
        if family == 'aave_v3':
            rows = get_aave_v3_tvl(w3, registry, block)
        elif family == 'compound_v3':
            rows = get_compound_v3_tvl(w3, registry, block)
        elif family == 'compound_v2':
            rows = get_compound_style_tvl(w3, registry, block)
        elif family == 'fluid':
            rows = get_fluid_tvl(w3, registry, block)
        elif family == 'lista':
            vaults = csu.get('vaults', [])
            rows = get_lista_tvl(w3, registry, block, vaults)
        elif family == 'gearbox':
            rows = get_gearbox_tvl(w3, registry, block)
        elif family == 'cap':
            rows = get_cap_tvl(w3, registry, block)
        else:
            print(f"❌ Unsupported family: {family}")
            return
        
        print(f"✅ Collected {len(rows)} markets/reserves\n")
        
        if len(rows) == 0:
            print("⚠️  Warning: No data returned!")
            return
        
        # Show sample data
        print("Sample data (first reserve/market):")
        print(json.dumps(rows[0], indent=2, default=str))
        print()
        
    except Exception as e:
        print(f"❌ TVL collection failed: {e}\n")
        import traceback
        traceback.print_exc()
        return
    
    # Save bronze data
    output_file = output_dir / 'tvl' / csu_name / f'{date_str}.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    bronze_data = {
        'csu': csu_name,
        'chain': chain,
        'family': family,
        'registry': registry,
        'date': date_str,
        'block': block,
        'timestamp': datetime.utcnow().isoformat(),
        'num_markets': len(rows),
        'data': rows,
    }
    
    with open(output_file, 'w') as f:
        json.dump(bronze_data, f, indent=2, default=str)
    
    print(f"✅ Saved to: {output_file}")
    print(f"   File size: {output_file.stat().st_size / 1024:.1f} KB\n")
    
    print(f"{'='*60}")
    print("✅ Collection successful!")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Test single day TVL collection')
    parser.add_argument('--csu', required=True, 
                       help='CSU name (e.g., aave_v3_ethereum)')
    parser.add_argument('--date', required=True,
                       help='Date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='data/bronze',
                       help='Output directory for bronze data')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    collect_tvl(args.csu, args.date, output_dir)


if __name__ == '__main__':
    main()
