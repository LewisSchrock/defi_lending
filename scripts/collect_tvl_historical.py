#!/usr/bin/env python3
"""
Historical TVL Collection with Retry Logic

Collects TVL data for October and November 2024 with:
- Automatic retry on rate limit errors (429)
- Configurable pause between retries
- Focus on Alchemy-supported chains only
- Checkpoint/resume support
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import subprocess
import time
import json

# Chains to use (Alchemy-supported only, exclude problematic chains)
ALCHEMY_CHAINS = {
    'ethereum', 'arbitrum', 'base', 'optimism', 'avalanche',
    'linea', 'gnosis', 'scroll'
}

EXCLUDE_CHAINS = {'polygon', 'plasma', 'sonic', 'meter', 'binance', 'cronos', 'flare'}

def load_checkpoint(checkpoint_file):
    """Load checkpoint if exists."""
    if Path(checkpoint_file).exists():
        with open(checkpoint_file) as f:
            return json.load(f)
    return None

def count_rate_limit_errors(checkpoint_file):
    """Count how many 429 errors in checkpoint."""
    checkpoint = load_checkpoint(checkpoint_file)
    if not checkpoint:
        return 0

    rate_limit_count = 0
    for task in checkpoint.get('failed', []):
        if '429' in task.get('error', '') or 'Too Many Requests' in task.get('error', ''):
            rate_limit_count += 1

    return rate_limit_count

def run_collection(start_date, end_date, workers=3, checkpoint_file='data/.checkpoint_tvl.json'):
    """Run TVL collection with retry logic."""

    # Load config to filter CSUs
    import yaml
    config_file = Path('code/config/csu_config.yaml')
    with open(config_file) as f:
        config = yaml.safe_load(f)

    csus = config.get('csus', config)

    # Filter to only Alchemy-supported chains
    working_csus = [
        csu_name for csu_name, csu_config in csus.items()
        if csu_config.get('chain') in ALCHEMY_CHAINS
    ]

    print("=" * 80)
    print("Historical TVL Collection - October & November 2024")
    print("=" * 80)
    print(f"Date range: {start_date} → {end_date}")
    print(f"Workers: {workers}")
    print(f"Total CSUs in config: {len(csus)}")
    print(f"Using Alchemy chains: {', '.join(sorted(ALCHEMY_CHAINS))}")
    print(f"Excluded chains: {', '.join(sorted(EXCLUDE_CHAINS))}")
    print(f"Working CSUs: {len(working_csus)}")
    print("=" * 80)
    print()

    # Initial run
    print("🚀 Starting initial collection...")
    print()

    cmd = [
        'python3', 'scripts/collect_tvl_parallel.py',
        '--start-date', start_date,
        '--end-date', end_date,
        '--workers', str(workers),
        '--csus'
    ] + working_csus

    result = subprocess.run(cmd)

    # Check for rate limit errors
    rate_limit_errors = count_rate_limit_errors(checkpoint_file)

    if rate_limit_errors == 0:
        print()
        print("✅ Collection completed successfully with no rate limit errors!")
        return 0

    print()
    print(f"⚠️  Found {rate_limit_errors} rate limit errors")
    print("⏱️  Waiting 60 seconds before retry...")
    print()

    time.sleep(60)

    # Retry with resume
    print("🔄 Retrying failed tasks...")
    print()

    cmd_retry = [
        'python3', 'scripts/collect_tvl_parallel.py',
        '--resume',
        '--workers', str(workers)
    ]

    result_retry = subprocess.run(cmd_retry)

    # Check again
    rate_limit_errors_after = count_rate_limit_errors(checkpoint_file)

    print()
    print("=" * 80)
    print("Final Results")
    print("=" * 80)

    if rate_limit_errors_after == 0:
        print("✅ All tasks completed successfully!")
    else:
        print(f"⚠️  {rate_limit_errors_after} tasks still failed")
        print(f"📉 Reduced from {rate_limit_errors} to {rate_limit_errors_after}")
        print()
        print("To retry again, run:")
        print("  python3 scripts/collect_tvl_parallel.py --resume --workers 2")

    print("=" * 80)

    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Historical TVL Collection')
    parser.add_argument('--start-date', default='2024-10-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-11-30', help='End date (YYYY-MM-DD)')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers')

    args = parser.parse_args()

    exit(run_collection(args.start_date, args.end_date, args.workers))
