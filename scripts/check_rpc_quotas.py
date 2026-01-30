#!/usr/bin/env python3
"""
RPC Rate Limit Checker

Tests all RPC endpoints to see if they're rate-limited or available.
Makes actual API calls to detect 429 errors and other rate limiting.

Usage:
    python scripts/check_rpc_quotas.py           # Quick check (1 call per endpoint)
    python scripts/check_rpc_quotas.py --burst   # Burst test (10 rapid calls)
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

# Provider rate limits (requests per second)
RATE_LIMITS = {
    'alchemy': {'rps': 5, 'burst': 30, 'description': '300 CU/sec (~5 getLogs/sec)'},
    'infura': {'rps': 10, 'burst': 50, 'description': '500 credits/sec'},
    'blockpi': {'rps': 20, 'burst': 50, 'description': '400 RU/sec, 20 req/sec'},
    'nodereal': {'rps': 2, 'burst': 10, 'description': '150 CU/sec (~2 getLogs/sec)'},
    'ankr': {'rps': 30, 'burst': 50, 'description': '~30 req/sec'},
    'public': {'rps': 1, 'burst': 5, 'description': 'Variable, often limited'},
}


def build_url(provider: str, key: str, chain: str = 'ethereum') -> str:
    """Build RPC URL for provider."""
    chain_map = {
        'alchemy': {
            'ethereum': 'eth-mainnet',
            'arbitrum': 'arb-mainnet',
            'base': 'base-mainnet',
            'optimism': 'opt-mainnet',
            'polygon': 'polygon-mainnet',
        },
        'infura': {
            'ethereum': 'mainnet',
            'arbitrum': 'arbitrum-mainnet',
            'base': 'base-mainnet',
            'optimism': 'optimism-mainnet',
            'polygon': 'polygon-mainnet',
        },
        'ankr': {
            'ethereum': 'eth',
            'arbitrum': 'arbitrum',
            'base': 'base',
            'optimism': 'optimism',
            'polygon': 'polygon',
            'binance': 'bsc',
            'avalanche': 'avalanche',
        },
        'nodereal': {
            'ethereum': 'eth-mainnet',
            'binance': 'bsc-mainnet',
        },
        'blockpi': {
            'ethereum': 'ethereum',
            'arbitrum': 'arbitrum',
            'base': 'base',
            'optimism': 'optimism',
            'polygon': 'polygon',
            'binance': 'bsc',
            'avalanche': 'avalanche',
            'gnosis': 'gnosis',
            'linea': 'linea',
            'sonic': 'sonic',
            'ink': 'ink',
            'meter': 'meter',
        },
    }

    if provider == 'alchemy':
        chain_slug = chain_map['alchemy'].get(chain, 'eth-mainnet')
        return f'https://{chain_slug}.g.alchemy.com/v2/{key}'
    elif provider == 'infura':
        chain_slug = chain_map['infura'].get(chain, 'mainnet')
        return f'https://{chain_slug}.infura.io/v3/{key}'
    elif provider == 'ankr':
        chain_slug = chain_map['ankr'].get(chain, 'eth')
        return f'https://rpc.ankr.com/{chain_slug}/{key}'
    elif provider == 'nodereal':
        chain_slug = chain_map['nodereal'].get(chain, 'eth-mainnet')
        return f'https://{chain_slug}.nodereal.io/v1/{key}'
    elif provider == 'blockpi':
        chain_slug = chain_map['blockpi'].get(chain, 'ethereum')
        return f'https://{chain_slug}.blockpi.network/v1/rpc/{key}'
    else:
        return None


def test_endpoint(provider: str, key: str, key_name: str, chain: str = 'ethereum') -> Dict:
    """Test a single endpoint and return status."""
    url = build_url(provider, key, chain)
    if not url:
        return {'key_name': key_name, 'status': 'error', 'message': 'Unknown provider'}

    try:
        w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
        start = time.time()
        block = w3.eth.block_number
        latency = (time.time() - start) * 1000

        return {
            'key_name': key_name,
            'provider': provider,
            'status': 'ok',
            'block': block,
            'latency_ms': latency,
            'message': f'Block {block:,} ({latency:.0f}ms)'
        }
    except Exception as e:
        error_str = str(e).lower()
        if '429' in error_str or 'rate' in error_str or 'too many' in error_str:
            return {'key_name': key_name, 'provider': provider, 'status': 'rate_limited', 'message': 'Rate limited (429)'}
        elif '401' in error_str or '403' in error_str or 'unauthorized' in error_str:
            return {'key_name': key_name, 'provider': provider, 'status': 'auth_failed', 'message': 'Auth failed'}
        elif 'timeout' in error_str:
            return {'key_name': key_name, 'provider': provider, 'status': 'timeout', 'message': 'Timeout'}
        elif '502' in error_str or '503' in error_str:
            return {'key_name': key_name, 'provider': provider, 'status': 'server_error', 'message': 'Server error (5xx)'}
        else:
            return {'key_name': key_name, 'provider': provider, 'status': 'error', 'message': str(e)[:60]}


def burst_test(provider: str, key: str, key_name: str, num_calls: int = 10) -> Dict:
    """Test endpoint with rapid burst of calls to detect rate limiting."""
    url = build_url(provider, key)
    if not url:
        return {'key_name': key_name, 'status': 'error', 'message': 'Unknown provider'}

    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 5}))

    successes = 0
    rate_limited = 0
    errors = 0
    latencies = []

    for i in range(num_calls):
        try:
            start = time.time()
            block = w3.eth.block_number
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            successes += 1
        except Exception as e:
            error_str = str(e).lower()
            if '429' in error_str or 'rate' in error_str:
                rate_limited += 1
            else:
                errors += 1

    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    if rate_limited > 0:
        status = 'rate_limited'
        message = f'{successes}/{num_calls} OK, {rate_limited} rate limited'
    elif errors > 0:
        status = 'partial'
        message = f'{successes}/{num_calls} OK, {errors} errors'
    else:
        status = 'ok'
        message = f'{num_calls}/{num_calls} OK, avg {avg_latency:.0f}ms'

    return {
        'key_name': key_name,
        'provider': provider,
        'status': status,
        'successes': successes,
        'rate_limited': rate_limited,
        'errors': errors,
        'avg_latency_ms': avg_latency,
        'message': message
    }


def get_all_endpoints() -> List[Tuple[str, str, str]]:
    """Get all configured endpoints as (provider, key, key_name) tuples."""
    endpoints = []

    # Alchemy keys
    for i in range(1, 20):
        key = os.environ.get(f'ALCHEMY_KEY_{i}')
        if key:
            endpoints.append(('alchemy', key, f'alchemy_{i}'))

    # Single-key providers
    for provider in ['infura', 'nodereal', 'ankr']:
        key = os.environ.get(f'{provider.upper()}_API_KEY')
        if key:
            endpoints.append((provider, key, f'{provider}_1'))

    # BlockPi (just test ethereum endpoint)
    key = os.environ.get('BLOCKPI_KEY_ETHEREUM')
    if key:
        endpoints.append(('blockpi', key, 'blockpi_ethereum'))

    return endpoints


def print_status_table(results: List[Dict]):
    """Print results as a formatted table."""
    # Group by status
    ok = [r for r in results if r['status'] == 'ok']
    rate_limited = [r for r in results if r['status'] == 'rate_limited']
    errors = [r for r in results if r['status'] not in ('ok', 'rate_limited')]

    print("\n" + "=" * 70)
    print(" RPC ENDPOINT STATUS")
    print("=" * 70)

    # Summary
    total = len(results)
    print(f"\n  ✅ Available:    {len(ok)}/{total}")
    print(f"  ⚠️  Rate Limited: {len(rate_limited)}/{total}")
    print(f"  ❌ Errors:       {len(errors)}/{total}")

    # Details
    print("\n" + "-" * 70)
    print(f"{'Endpoint':<25} {'Status':<15} {'Details':<30}")
    print("-" * 70)

    for r in results:
        status_icon = {
            'ok': '✅',
            'rate_limited': '⚠️ ',
            'auth_failed': '🔒',
            'timeout': '⏱️ ',
            'server_error': '💥',
            'error': '❌',
            'partial': '🔶',
        }.get(r['status'], '❓')

        print(f"{r['key_name']:<25} {status_icon} {r['status']:<12} {r['message']:<30}")

    # Rate limit info
    print("\n" + "-" * 70)
    print("RATE LIMITS BY PROVIDER:")
    print("-" * 70)
    for provider, limits in RATE_LIMITS.items():
        if provider != 'public':
            print(f"  {provider:<12} {limits['description']}")


def main():
    parser = argparse.ArgumentParser(description='RPC Rate Limit Checker')
    parser.add_argument('--burst', action='store_true',
                       help='Run burst test (10 rapid calls per endpoint)')
    parser.add_argument('--calls', type=int, default=10,
                       help='Number of calls for burst test (default: 10)')
    args = parser.parse_args()

    endpoints = get_all_endpoints()

    if not endpoints:
        print("No RPC endpoints configured. Check your .env file.")
        return

    print(f"\nTesting {len(endpoints)} endpoints...")

    if args.burst:
        print(f"Running burst test ({args.calls} calls per endpoint)...")
        results = []
        for provider, key, key_name in endpoints:
            print(f"  Testing {key_name}...", end=' ', flush=True)
            result = burst_test(provider, key, key_name, args.calls)
            print(result['message'])
            results.append(result)
    else:
        # Quick parallel test
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(test_endpoint, provider, key, key_name): key_name
                for provider, key, key_name in endpoints
            }
            for future in as_completed(futures):
                results.append(future.result())

        # Sort by key name
        results.sort(key=lambda x: x['key_name'])

    print_status_table(results)
    print()


if __name__ == '__main__':
    main()
