#!/usr/bin/env python3
"""
Find Contract Deployment Dates

For CSUs that fail with decode errors (contract returns empty data),
this script finds when the contract was actually deployed.

It performs binary search to find the first block where the contract
has code deployed, then converts that to a date.

Usage:
    python3 scripts/find_contract_deployment.py --csu compound_v3_base_usdc
    python3 scripts/find_contract_deployment.py --all-failed
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import yaml
from datetime import datetime, timezone
import pytz
from config.rpc_pool import get_web3

# Import POA middleware
try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        from web3.middleware import geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None

NY_TZ = pytz.timezone("America/New_York")
POA_CHAINS = ['binance', 'polygon', 'gnosis', 'avalanche', 'optimism', 'linea', 'scroll', 'xdai']


def find_deployment_block(w3, contract_address: str) -> int:
    """
    Binary search to find the first block where contract has code.

    Returns:
        Block number where contract was deployed (or 0 if not found)
    """
    latest = w3.eth.block_number

    # Check if contract exists now
    code_now = w3.eth.get_code(contract_address)
    if code_now == b'' or code_now == b'0x':
        print(f"  ❌ Contract has no code even at latest block {latest}")
        return 0

    print(f"  🔍 Searching blocks 1 to {latest:,}...")

    # Binary search
    lo, hi = 1, latest
    result = latest

    while lo <= hi:
        mid = (lo + hi) // 2

        try:
            code = w3.eth.get_code(contract_address, block_identifier=mid)
            has_code = code != b'' and code != b'0x'

            if has_code:
                # Contract exists at mid, search earlier
                result = mid
                hi = mid - 1
            else:
                # No code at mid, search later
                lo = mid + 1

        except Exception as e:
            # If we can't get code at this block, search later
            lo = mid + 1

    return result


def block_to_date(w3, block_number: int) -> str:
    """Convert block number to NY date string."""
    try:
        block = w3.eth.get_block(block_number)
        timestamp = block['timestamp']
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        dt_ny = dt_utc.astimezone(NY_TZ)
        return dt_ny.date().isoformat()
    except Exception as e:
        return f"Error: {e}"


def get_contract_address(csu_name: str, csu_config: dict) -> str:
    """
    Extract the main contract address from CSU config.

    For Compound V3: Use 'registry' field (comet address)
    For Aave V3: Use 'registry' field (pool address provider or pool)
    For Fluid: Use 'registry' field (liquidity layer)
    """
    registry = csu_config.get('registry')

    if registry:
        return registry

    # Fallback for older configs
    comptroller = csu_config.get('comptroller')
    if comptroller:
        return comptroller

    return None


def find_deployment_for_csu(csu_name: str, csu_config: dict):
    """Find deployment date for a specific CSU."""

    chain = csu_config.get('chain')
    if not chain:
        print(f"❌ {csu_name}: No chain specified")
        return

    contract_address = get_contract_address(csu_name, csu_config)
    if not contract_address:
        print(f"❌ {csu_name}: No contract address found in config")
        return

    print(f"\n{'='*70}")
    print(f"{csu_name}")
    print(f"{'='*70}")
    print(f"  Chain: {chain}")
    print(f"  Contract: {contract_address}")

    # Setup Web3
    try:
        w3 = get_web3(chain)

        # Inject POA middleware if needed
        if chain in POA_CHAINS and geth_poa_middleware:
            try:
                if hasattr(w3, 'middleware_onion'):
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            except Exception:
                pass  # May already be injected

        latest = w3.eth.block_number
        print(f"  Latest block: {latest:,}")
    except Exception as e:
        print(f"  ❌ Failed to connect to {chain}: {e}")
        return

    # Find deployment block
    deployment_block = find_deployment_block(w3, contract_address)

    if deployment_block == 0:
        return

    # Convert to date
    deployment_date = block_to_date(w3, deployment_block)

    print(f"\n  ✅ Deployment found:")
    print(f"     Block: {deployment_block:,}")
    print(f"     Date:  {deployment_date}")
    print(f"\n  📝 Add to config:")
    print(f"     deployment_date: \"{deployment_date}\"")


def find_all_failed_deployments():
    """
    Find deployment dates for all CSUs that failed with decode errors.
    """
    # Load checkpoint to see which CSUs failed
    checkpoint_file = Path('data/.checkpoint_tvl.json')
    if not checkpoint_file.exists():
        print("❌ No checkpoint file found. Run a collection first.")
        return

    with open(checkpoint_file) as f:
        checkpoint = json.load(f)

    # Extract CSUs with decode errors
    decode_error_csus = set()
    for task in checkpoint.get('failed', []):
        error = task.get('error', '')
        if 'Could not decode' in error:
            task_str = task['task']
            csu = task_str.split(':')[0]
            decode_error_csus.add(csu)

    if not decode_error_csus:
        print("✅ No CSUs with decode errors found!")
        return

    print(f"Found {len(decode_error_csus)} CSUs with decode errors")
    print()

    # Load config
    config_file = Path('code/config/csu_config.yaml')
    with open(config_file) as f:
        config = yaml.safe_load(f)

    csus = config.get('csus', config)

    # Find deployment for each
    for csu_name in sorted(decode_error_csus):
        if csu_name in csus:
            find_deployment_for_csu(csu_name, csus[csu_name])
        else:
            print(f"⚠️  {csu_name}: Not found in config (may be commented out)")


def main():
    parser = argparse.ArgumentParser(description='Find contract deployment dates')
    parser.add_argument('--csu', help='Specific CSU to check')
    parser.add_argument('--all-failed', action='store_true',
                       help='Check all CSUs that failed with decode errors')

    args = parser.parse_args()

    if args.all_failed:
        find_all_failed_deployments()
    elif args.csu:
        # Load config
        config_file = Path('code/config/csu_config.yaml')
        with open(config_file) as f:
            config = yaml.safe_load(f)

        csus = config.get('csus', config)

        if args.csu in csus:
            find_deployment_for_csu(args.csu, csus[args.csu])
        else:
            print(f"❌ CSU '{args.csu}' not found in config")
    else:
        print("Usage:")
        print("  python3 scripts/find_contract_deployment.py --csu compound_v3_base_usdc")
        print("  python3 scripts/find_contract_deployment.py --all-failed")


if __name__ == '__main__':
    main()
