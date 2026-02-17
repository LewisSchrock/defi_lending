#!/usr/bin/env python3
"""
TVL Collection - Working Chains Only

Excludes chains with known infrastructure issues:
- Polygon: Public RPCs don't support historical state
- Plasma: No working archive nodes
- Sonic: New chain, unstable
- Meter: Limited RPC support

Focuses on thesis-grade infrastructure:
- Ethereum, Arbitrum, Base, Optimism, Avalanche
- Linea, Scroll, Gnosis (xdai)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess

# Chains to EXCLUDE (infrastructure problems)
EXCLUDE_CHAINS = {'polygon', 'plasma', 'sonic', 'meter'}

# Load config and filter CSUs
import yaml

config_file = Path('code/config/csu_config.yaml')
with open(config_file) as f:
    config = yaml.safe_load(f)

csus = config.get('csus', config)

# Filter to only working chains
working_csus = [
    csu_name for csu_name, csu_config in csus.items()
    if csu_config.get('chain') not in EXCLUDE_CHAINS
]

print("=" * 80)
print("TVL Collection - Working Chains Only")
print("=" * 80)
print(f"Total CSUs in config: {len(csus)}")
print(f"Excluded chains: {', '.join(sorted(EXCLUDE_CHAINS))}")
print(f"Working CSUs: {len(working_csus)}")
print("=" * 80)
print()

# Build command
cmd = [
    'python3', 'scripts/collect_tvl_parallel.py',
    '--resume',
    '--workers', '3',
    '--csus'
] + working_csus

print(f"Running: {' '.join(cmd[:6])} [+{len(working_csus)} CSUs]")
print()

# Run
subprocess.run(cmd)
