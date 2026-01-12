#!/bin/bash
# Full 2024 Collection - Overnight Run
# Builds block caches then collects TVL data for entire 2024

set -e  # Exit on any error

cd /Users/lewisschrock/Desktop/Academics/thesis_v2.9

echo "============================================================"
echo "Full 2024 Data Collection - Overnight Run"
echo "============================================================"
echo "Start time: $(date)"
echo ""

# Step 1: Build block caches for entire 2024
echo "STEP 1: Building block caches for 2024..."
echo "Chains: ethereum, arbitrum, base, optimism, avalanche, linea, gnosis, scroll"
echo "Date range: 2024-01-01 to 2024-12-31 (366 days)"
echo "Expected time: 1-2 hours"
echo ""

python3 scripts/build_block_cache.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --chains ethereum arbitrum base optimism avalanche linea gnosis scroll

echo ""
echo "✅ Block caches completed at: $(date)"
echo ""

# Step 2: Clean checkpoint and collect TVL
echo "STEP 2: Collecting TVL data for 2024..."
echo "Workers: 2 (slow and reliable for overnight run)"
echo "Expected CSUs: ~30"
echo "Expected tasks: ~11,000 (30 CSUs × 366 days)"
echo "Expected time: 8-12 hours"
echo ""

# Remove old checkpoint to start fresh
if [ -f data/.checkpoint_tvl.json ]; then
  echo "Backing up old checkpoint..."
  cp data/.checkpoint_tvl.json data/.checkpoint_tvl_backup_$(date +%Y%m%d_%H%M%S).json
  rm data/.checkpoint_tvl.json
fi

python3 scripts/collect_tvl_parallel.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --workers 2

echo ""
echo "============================================================"
echo "Full 2024 Collection Complete!"
echo "============================================================"
echo "End time: $(date)"
echo ""

# Summary
echo "Summary:"
python3 -c "
import json
from pathlib import Path

checkpoint = Path('data/.checkpoint_tvl.json')
if checkpoint.exists():
    with open(checkpoint) as f:
        data = json.load(f)
    print(f'  Completed: {len(data.get(\"completed\", []))}')
    print(f'  Failed: {len(data.get(\"failed\", []))}')
else:
    print('  No checkpoint found')

# Count collected files
import os
total_files = 0
for root, dirs, files in os.walk('data/bronze/tvl'):
    total_files += len([f for f in files if f.endswith('.json')])
print(f'  Total JSON files: {total_files}')
"

echo ""
echo "Check results in: data/bronze/tvl/"
echo "Check checkpoint: data/.checkpoint_tvl.json"
