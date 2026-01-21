#!/usr/bin/env python3
"""
Test all configured RPC providers and show capacity summary.

Usage:
    python scripts/test_rpc_providers.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.rpc_pool_v2 import test_all_chains, get_provider_stats, API_KEYS, PROVIDERS

def main():
    print("=" * 70)
    print("RPC PROVIDER CAPACITY ANALYSIS")
    print("=" * 70)

    # Show configured keys
    print("\nCONFIGURED API KEYS:")
    print("-" * 40)
    total_monthly = 0
    for provider, keys in sorted(API_KEYS.items()):
        if isinstance(keys, dict):
            # BlockPi: per-chain keys
            count = len(keys)
            if provider in PROVIDERS:
                config = PROVIDERS[provider]
                monthly = config.monthly_limit  # Shared quota
                total_monthly += monthly
                logs_capacity = monthly // config.get_logs_cost
                print(f"  {provider:12} {count} chains → {monthly/1e6:.0f}M RU/mo  ({logs_capacity/1e6:.1f}M eth_getLogs)")
                print(f"               Chains: {', '.join(sorted(keys.keys()))}")
        elif isinstance(keys, list):
            count = len(keys)
            if provider in PROVIDERS:
                config = PROVIDERS[provider]
                monthly = config.monthly_limit * count
                total_monthly += monthly
                logs_capacity = monthly // config.get_logs_cost
                print(f"  {provider:12} {count} key(s)  → {monthly/1e6:.0f}M CU/mo  ({logs_capacity/1e6:.1f}M eth_getLogs)")
            else:
                print(f"  {provider:12} {count} key(s)")

    print(f"\n  TOTAL MONTHLY CAPACITY: {total_monthly/1e6:.0f}M CU")

    # Calculate eth_getLogs capacity
    print("\n" + "=" * 70)
    print("eth_getLogs CAPACITY BY PROVIDER")
    print("=" * 70)

    total_logs = 0
    for provider, keys in sorted(API_KEYS.items()):
        if provider in PROVIDERS and keys:
            config = PROVIDERS[provider]
            count = len(keys)
            monthly = config.monthly_limit * count
            logs_capacity = monthly // config.get_logs_cost
            total_logs += logs_capacity

            # Per-second capacity
            sec_capacity = config.burst_limit // config.get_logs_cost

            print(f"  {provider:12} {logs_capacity/1e6:>6.1f}M logs/mo  ({sec_capacity:.0f} logs/sec burst)")

    print(f"\n  TOTAL: {total_logs/1e6:.1f}M eth_getLogs calls/month")

    # Compare to liquidation needs
    print("\n" + "=" * 70)
    print("LIQUIDATION COLLECTION FEASIBILITY")
    print("=" * 70)

    # From earlier analysis: ~67M chunks needed (at 10 blocks/chunk)
    # Each chunk = 1 eth_getLogs + maybe 0.01 eth_getBlockByNumber
    chunks_needed = 67_000_000

    print(f"  Chunks needed (all chains, 2024-2025): {chunks_needed/1e6:.0f}M")
    print(f"  Your eth_getLogs capacity/month:       {total_logs/1e6:.1f}M")

    if total_logs >= chunks_needed:
        print(f"\n  ✅ FEASIBLE: Can complete in ~1 month!")
    else:
        months = chunks_needed / total_logs if total_logs > 0 else float('inf')
        print(f"\n  ⚠️  Would take ~{months:.1f} months with current capacity")

    # Test connections
    print("\n")
    test_all_chains()


if __name__ == '__main__':
    main()
