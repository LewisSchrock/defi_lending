#!/usr/bin/env bash
# =============================================================================
# Full end-to-end pipeline: TVL completion → Oracle enrichment → Panel rebuild
# =============================================================================
# Run this and walk away. It handles everything sequentially.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "========================================================================"
echo "FULL PIPELINE — $(date)"
echo "========================================================================"

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Wait for any running TVL collections to finish
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "Step 1: Checking TVL collection completeness..."

# Count total expected days per CSU
python3 -c "
import os, glob, json
tvl_base = 'data/bronze/tvl'
csus = sorted([d for d in os.listdir(tvl_base) if os.path.isdir(os.path.join(tvl_base, d))])
incomplete = []
for csu in csus:
    files = glob.glob(os.path.join(tvl_base, csu, '*.json'))
    if len(files) < 100:
        # Could be a short-lived CSU — check if it has a deployment date
        if len(files) > 0:
            dates = sorted([os.path.basename(f).replace('.json','') for f in files])
            print(f'  {csu}: {len(files)} days ({dates[0]} to {dates[-1]})')
        else:
            print(f'  {csu}: NO DATA')
            incomplete.append(csu)
    # else: has enough data
print(f'\nTotal CSUs with bronze TVL: {len(csus)}')
"

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Oracle price enrichment (Aave + DefiLlama fallback)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "========================================================================"
echo "Step 2: Oracle price enrichment (Aave V3 + DefiLlama fallback)"
echo "========================================================================"
python3 -u scripts/enrich_tvl_oracle_prices.py --workers 20

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Rebuild volatility panel
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "========================================================================"
echo "Step 3: Rebuild volatility panel"
echo "========================================================================"
python3 -u scripts/build_volatility_panel.py

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Coverage report
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "========================================================================"
echo "Step 4: Final coverage report"
echo "========================================================================"
python3 -c "
import pandas as pd, json, os, glob
from collections import defaultdict

# Load oracle cache
with open('data/cache/prices/protocol_oracle_prices.json') as f:
    cache = json.load(f)
cached_keys = set(cache.keys())

# Load collateral-basket panel
panel = pd.read_parquet('data/analysis/collateral_basket.parquet')
print(f'Volatility panel: {len(panel):,} observations, {panel[\"csu\"].nunique()} CSUs')
print(f'Date range: {panel[\"date\"].min()} to {panel[\"date\"].max()}')
print()

# Per-CSU coverage in the panel
for csu in sorted(panel['csu'].unique()):
    sub = panel[panel['csu'] == csu]
    n = len(sub)
    non_null = sub['vol_14d'].notna().sum()
    vol_std = sub['vol_14d'].std() if non_null > 0 else 0
    status = 'OK' if non_null >= 200 and vol_std > 0.0001 else 'LOW' if non_null >= 100 else 'BAD'
    print(f'  {csu:<40} {n:>5} obs, {non_null:>5} vol, std={vol_std:.6f} [{status}]')

# Check for CSUs with TVL but NOT in the panel
tvl_csus = set(d for d in os.listdir('data/bronze/tvl') if os.path.isdir(os.path.join('data/bronze/tvl', d)))
panel_csus = set(panel['csu'].unique())
missing = tvl_csus - panel_csus
if missing:
    print(f'\n--- CSUs with bronze TVL but NOT in panel ({len(missing)}) ---')
    for csu in sorted(missing):
        files = glob.glob(os.path.join('data/bronze/tvl', csu, '*.json'))
        print(f'  {csu}: {len(files)} days')

# Oracle cache stats
print(f'\nOracle cache: {len(cached_keys):,} entries')
from collections import Counter
chains = Counter(k.split(':')[0] for k in cached_keys)
for ch, n in chains.most_common():
    print(f'  {ch}: {n:,}')
"

echo ""
echo "========================================================================"
echo "PIPELINE COMPLETE — $(date)"
echo "========================================================================"
