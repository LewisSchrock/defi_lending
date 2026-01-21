#!/usr/bin/env python3
"""
RPC Usage Monitor & CU Tracker

Monitors Alchemy API usage and estimates compute unit consumption.
Helps track progress toward monthly limits and predict when you'll hit caps.

Alchemy Free Tier Limits:
- 30,000,000 CU per month per account
- 300 CU/second throughput

CU Costs per method:
- eth_blockNumber: 10 CU
- eth_getBlockByNumber: 20 CU
- eth_call: 26 CU
- eth_getLogs: 60 CU
- eth_sendRawTransaction: 40 CU

Usage:
    python scripts/rpc_monitor.py                    # Show current status
    python scripts/rpc_monitor.py --test             # Test all connections
    python scripts/rpc_monitor.py --estimate-job    # Estimate CU for a job
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

# =============================================================================
# CONSTANTS
# =============================================================================

# Alchemy CU costs per method
CU_COSTS = {
    'eth_blockNumber': 10,
    'eth_getBlockByNumber': 20,
    'eth_getBalance': 20,
    'eth_getCode': 20,
    'eth_getTransactionByHash': 20,
    'eth_getBlockByHash': 20,
    'eth_getTransactionReceipt': 20,
    'eth_estimateGas': 20,
    'eth_gasPrice': 20,
    'eth_getStorageAt': 20,
    'eth_getTransactionCount': 20,
    'eth_accounts': 10,
    'eth_chainId': 0,
    'eth_syncing': 0,
    'eth_call': 26,
    'eth_getLogs': 60,
    'eth_sendRawTransaction': 40,
}

# Alchemy limits
FREE_TIER_MONTHLY_CU = 30_000_000
FREE_TIER_CU_PER_SEC = 300

# Block counts per chain (2024+2025 combined)
CHAIN_BLOCKS = {
    'ethereum': 5_212_893,
    'arbitrum': 250_118_465,
    'avalanche': 34_967_402,
    'base': 31_492_800,
    'binance': 38_742_955,
    'cronos': 28_287_471,
    'flare': 35_511_028,
    'gnosis': 12_177_080,
    'ink': 31_449_600,
    'linea': 25_772_174,
    'meter': 37_488_172,
    'optimism': 31_492_800,
    'polygon': 29_182_918,
    'scroll': 11_813_100,
    'sonic': 57_122_193,
    'plasma': 10_312_927,
}

# Usage tracking file
USAGE_FILE = Path('data/.rpc_usage.json')


# =============================================================================
# USAGE TRACKING
# =============================================================================

def load_usage() -> Dict:
    """Load usage tracking data."""
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'accounts': {},
        'last_reset': datetime.now().strftime('%Y-%m-01'),
    }


def save_usage(usage: Dict):
    """Save usage tracking data."""
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, 'w') as f:
        json.dump(usage, f, indent=2)


def record_usage(key_name: str, method: str, count: int = 1):
    """Record API usage for tracking."""
    usage = load_usage()

    # Check if we need to reset (new month)
    current_month = datetime.now().strftime('%Y-%m-01')
    if usage.get('last_reset') != current_month:
        usage = {'accounts': {}, 'last_reset': current_month}

    if key_name not in usage['accounts']:
        usage['accounts'][key_name] = {'calls': 0, 'cu': 0, 'by_method': {}}

    cu_cost = CU_COSTS.get(method, 26)  # Default to eth_call cost
    usage['accounts'][key_name]['calls'] += count
    usage['accounts'][key_name]['cu'] += cu_cost * count

    if method not in usage['accounts'][key_name]['by_method']:
        usage['accounts'][key_name]['by_method'][method] = 0
    usage['accounts'][key_name]['by_method'][method] += count

    save_usage(usage)


def get_usage_summary() -> Dict:
    """Get summary of current usage."""
    usage = load_usage()

    summary = {
        'month': usage.get('last_reset', 'unknown'),
        'accounts': {},
        'total_cu': 0,
        'total_calls': 0,
    }

    for key_name, data in usage.get('accounts', {}).items():
        cu = data.get('cu', 0)
        calls = data.get('calls', 0)

        summary['accounts'][key_name] = {
            'cu_used': cu,
            'cu_remaining': FREE_TIER_MONTHLY_CU - cu,
            'cu_pct': (cu / FREE_TIER_MONTHLY_CU) * 100,
            'calls': calls,
        }
        summary['total_cu'] += cu
        summary['total_calls'] += calls

    return summary


# =============================================================================
# CONNECTION TESTING
# =============================================================================

def test_connections():
    """Test all RPC connections and show status."""
    from config.rpc_pool import (
        ALCHEMY_KEYS, CHAIN_KEY_MAPPING, ALCHEMY_CHAINS, PUBLIC_RPCS,
        get_blacklisted_keys
    )
    from web3 import Web3

    print("=" * 70)
    print("RPC CONNECTION TEST")
    print("=" * 70)

    # Count keys
    print(f"\nAlchemy Keys Configured: {len(ALCHEMY_KEYS)}")
    for key_name in sorted(ALCHEMY_KEYS.keys()):
        print(f"  - {key_name}: {'*' * 8}...{ALCHEMY_KEYS[key_name][-4:]}")

    print("\n" + "-" * 70)
    print("CHAIN STATUS")
    print("-" * 70)

    results = {}

    for chain in sorted(set(list(ALCHEMY_CHAINS.keys()) + list(PUBLIC_RPCS.keys()))):
        blacklisted = get_blacklisted_keys(chain)
        working_keys = CHAIN_KEY_MAPPING.get(chain, [])
        available_keys = [k for k in working_keys if k not in blacklisted]

        # Test connection
        connected = False
        block_num = None
        provider_type = "none"

        # Try Alchemy first
        if chain in ALCHEMY_CHAINS and available_keys:
            chain_pattern = ALCHEMY_CHAINS[chain]
            key_value = ALCHEMY_KEYS.get(available_keys[0])
            if key_value:
                url = f'https://{chain_pattern}.g.alchemy.com/v2/{key_value}'
                try:
                    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
                    block_num = w3.eth.block_number
                    connected = True
                    provider_type = f"alchemy ({len(available_keys)} keys)"
                except Exception as e:
                    pass

        # Try public RPC if Alchemy failed
        if not connected and chain in PUBLIC_RPCS:
            for url in PUBLIC_RPCS[chain][:1]:  # Just test first one
                try:
                    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
                    block_num = w3.eth.block_number
                    connected = True
                    provider_type = "public"
                    break
                except Exception:
                    pass

        status = "OK" if connected else "FAILED"
        block_str = f"block {block_num:,}" if block_num else "no connection"
        blacklist_str = f" ({len(blacklisted)} blacklisted)" if blacklisted else ""

        print(f"  {chain:15} [{status:6}] {provider_type:25} {block_str}{blacklist_str}")

        results[chain] = {
            'connected': connected,
            'block': block_num,
            'provider': provider_type,
            'blacklisted': len(blacklisted),
        }

    working = sum(1 for r in results.values() if r['connected'])
    print(f"\nWorking: {working}/{len(results)} chains")

    return results


# =============================================================================
# CU ESTIMATION
# =============================================================================

def estimate_liquidation_cu(chain: str, start_date: str, end_date: str, chunk_size: int = 10) -> Dict:
    """Estimate CU required for liquidation collection on a chain."""

    # Load block cache to get actual block range
    cache_dir = Path('data/cache')
    blocks = 0

    for pattern in [f'{chain}_blocks_*.json']:
        for cache_file in cache_dir.glob(pattern):
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                    if start_date in data and end_date in data:
                        blocks = data[end_date]['block'] - data[start_date]['block']
                        break
                    # Try to estimate from available data
                    dates = sorted(data.keys())
                    if dates:
                        first = data[dates[0]]['block']
                        last = data[dates[-1]]['block']
                        blocks = max(blocks, last - first)
            except Exception:
                continue

    if blocks == 0:
        blocks = CHAIN_BLOCKS.get(chain, 0)

    chunks = blocks // chunk_size

    # CU calculation
    get_logs_cu = chunks * CU_COSTS['eth_getLogs']
    # Assume ~1% of chunks have events needing block timestamp lookup
    get_block_cu = int(chunks * 0.01) * CU_COSTS['eth_getBlockByNumber']
    total_cu = get_logs_cu + get_block_cu

    accounts_needed = (total_cu + FREE_TIER_MONTHLY_CU - 1) // FREE_TIER_MONTHLY_CU

    return {
        'chain': chain,
        'blocks': blocks,
        'chunks': chunks,
        'chunk_size': chunk_size,
        'get_logs_cu': get_logs_cu,
        'get_block_cu': get_block_cu,
        'total_cu': total_cu,
        'accounts_needed': accounts_needed,
        'pct_of_free_tier': (total_cu / FREE_TIER_MONTHLY_CU) * 100,
    }


def estimate_tvl_cu(csu: str, days: int = 365) -> Dict:
    """Estimate CU required for TVL collection on a CSU."""

    # TVL collection does ~10-50 eth_call per day per CSU
    # Plus some eth_getBlockByNumber for date->block conversion

    calls_per_day = 30  # Average estimate

    eth_call_cu = days * calls_per_day * CU_COSTS['eth_call']
    block_lookup_cu = days * CU_COSTS['eth_getBlockByNumber']
    total_cu = eth_call_cu + block_lookup_cu

    return {
        'csu': csu,
        'days': days,
        'calls_per_day': calls_per_day,
        'total_calls': days * calls_per_day,
        'total_cu': total_cu,
        'pct_of_free_tier': (total_cu / FREE_TIER_MONTHLY_CU) * 100,
    }


# =============================================================================
# DISPLAY
# =============================================================================

def show_status():
    """Show current RPC status and usage."""
    from config.rpc_pool import ALCHEMY_KEYS, CHAIN_KEY_MAPPING, get_blacklisted_keys

    print("=" * 70)
    print("RPC MONITOR - STATUS")
    print("=" * 70)

    # Account summary
    print(f"\n{'─' * 70}")
    print("ALCHEMY ACCOUNTS")
    print(f"{'─' * 70}")

    print(f"\nConfigured: {len(ALCHEMY_KEYS)} accounts")
    print(f"Monthly CU per account: {FREE_TIER_MONTHLY_CU:,}")
    print(f"Total monthly capacity: {len(ALCHEMY_KEYS) * FREE_TIER_MONTHLY_CU:,} CU")

    # Usage summary (if tracked)
    summary = get_usage_summary()
    if summary['total_cu'] > 0:
        print(f"\n{'─' * 70}")
        print(f"USAGE THIS MONTH ({summary['month']})")
        print(f"{'─' * 70}")

        for key_name, data in sorted(summary['accounts'].items()):
            bar_len = int(data['cu_pct'] / 5)  # 20 char max
            bar = '█' * bar_len + '░' * (20 - bar_len)
            print(f"  {key_name}: [{bar}] {data['cu_pct']:.1f}% ({data['cu_used']:,} / {FREE_TIER_MONTHLY_CU:,} CU)")

        print(f"\n  Total CU used: {summary['total_cu']:,}")
        print(f"  Total calls: {summary['total_calls']:,}")

    # Chain coverage
    print(f"\n{'─' * 70}")
    print("CHAIN COVERAGE")
    print(f"{'─' * 70}")

    for chain in sorted(CHAIN_KEY_MAPPING.keys()):
        keys = CHAIN_KEY_MAPPING[chain]
        blacklisted = get_blacklisted_keys(chain)
        available = len([k for k in keys if k not in blacklisted])

        if available == 0:
            status = "PUBLIC RPC"
        else:
            status = f"{available} keys"

        blocks = CHAIN_BLOCKS.get(chain, 0)
        print(f"  {chain:15} {status:15} ~{blocks:>12,} blocks")

    # Estimation summary
    print(f"\n{'─' * 70}")
    print("LIQUIDATION COLLECTION ESTIMATES (2024-2025)")
    print(f"{'─' * 70}")

    total_cu = 0
    estimates = []
    for chain in sorted(CHAIN_BLOCKS.keys(), key=lambda x: -CHAIN_BLOCKS[x]):
        est = estimate_liquidation_cu(chain, '2024-01-01', '2025-12-31')
        estimates.append(est)
        total_cu += est['total_cu']

    # Show top consumers
    for est in estimates[:5]:
        accounts = est['accounts_needed']
        print(f"  {est['chain']:15} {est['total_cu']:>15,} CU ({est['pct_of_free_tier']:>6.1f}% of 1 account) - needs {accounts} account(s)")

    print(f"  ...")
    print(f"  {'TOTAL':15} {total_cu:>15,} CU")
    print(f"\n  With {len(ALCHEMY_KEYS)} accounts: {total_cu / (len(ALCHEMY_KEYS) * FREE_TIER_MONTHLY_CU):.1f} months to complete")


def show_job_estimate(chain: str, start_date: str, end_date: str):
    """Show detailed CU estimate for a specific job."""
    print("=" * 70)
    print(f"CU ESTIMATE: {chain} ({start_date} to {end_date})")
    print("=" * 70)

    est = estimate_liquidation_cu(chain, start_date, end_date)

    print(f"\n  Blocks:           {est['blocks']:,}")
    print(f"  Chunks (10 blks): {est['chunks']:,}")
    print(f"\n  eth_getLogs CU:   {est['get_logs_cu']:,}")
    print(f"  eth_getBlock CU:  {est['get_block_cu']:,}")
    print(f"  ─────────────────────────")
    print(f"  Total CU:         {est['total_cu']:,}")
    print(f"\n  % of 1 account:   {est['pct_of_free_tier']:.1f}%")
    print(f"  Accounts needed:  {est['accounts_needed']}")

    # Time estimate
    from config.rpc_pool import ALCHEMY_KEYS
    capacity_per_sec = len(ALCHEMY_KEYS) * FREE_TIER_CU_PER_SEC
    seconds = est['total_cu'] / capacity_per_sec
    hours = seconds / 3600

    print(f"\n  At {capacity_per_sec} CU/sec ({len(ALCHEMY_KEYS)} accounts):")
    print(f"    Minimum time:   {hours:.1f} hours")
    print(f"    Realistic:      {hours * 2:.1f} hours (with retries/backoff)")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='RPC Usage Monitor & CU Tracker')
    parser.add_argument('--test', action='store_true', help='Test all connections')
    parser.add_argument('--estimate', action='store_true', help='Show job estimate')
    parser.add_argument('--chain', type=str, help='Chain for estimate')
    parser.add_argument('--start-date', type=str, default='2024-01-01')
    parser.add_argument('--end-date', type=str, default='2025-12-31')
    parser.add_argument('--reset-usage', action='store_true', help='Reset usage tracking')

    args = parser.parse_args()

    if args.test:
        test_connections()
    elif args.estimate and args.chain:
        show_job_estimate(args.chain, args.start_date, args.end_date)
    elif args.reset_usage:
        save_usage({'accounts': {}, 'last_reset': datetime.now().strftime('%Y-%m-01')})
        print("Usage tracking reset.")
    else:
        show_status()


if __name__ == '__main__':
    main()
