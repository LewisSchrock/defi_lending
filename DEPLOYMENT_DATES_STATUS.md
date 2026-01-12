# Deployment Date Tracking - Status

## Overview

To avoid wasting RPC calls on blocks before contracts were deployed, we now track deployment dates for CSUs and skip collection tasks before those dates.

## Implementation

**Files Created/Modified:**
1. `code/config/deployment_dates.yaml` - Central registry of deployment dates
2. `scripts/find_contract_deployment.py` - Script to find deployment dates via binary search
3. `scripts/collect_tvl_parallel.py` - Updated to check deployment dates before collecting

## Current Deployment Dates

### ✅ Verified Deployment Dates

**Compound V3 Markets:**
- `compound_v3_base_usdc`: **2024-03-11**
- `compound_v3_op_usdc`: **2024-04-06**
- `compound_v3_op_usdt`: **2024-05-20**
- `compound_v3_arb_weth`: **2024-06-07**
- `compound_v3_arb_usdt`: **2024-06-20**
- `compound_v3_eth_usdt`: **2024-06-28**
- `compound_v3_op_weth`: **2024-07-15**
- `compound_v3_eth_wsteth`: **2024-09-05**
- `compound_v3_base_aero`: **2024-10-09**
- `compound_v3_eth_usds`: **2024-10-17**

### ⚠️ Estimated/TODO Deployment Dates

**Fluid Lending:**
- `fluid_lending_ethereum`: **2024-02-01** (TODO: Verify exact date)
- `fluid_lending_arbitrum`: **2024-06-11**
- `fluid_lending_base`: **2024-08-01** (TODO: Verify exact date)

**Aave V3:**
- `aave_v3_scroll`: **2023-10-01** (TODO: Verify from block 2,618,760 with POA)
- `aave_v3_linea`: **2024-07-01** (TODO: Verify from block 12,430,823 with POA)

## Impact

**For Full Year 2024 Collection (35 CSUs × 366 days = 12,810 tasks):**

- **Before**: Would attempt all 12,810 tasks, with ~500-700 failing on pre-deployment dates
- **After**: Skips ~500-700 pre-deployment tasks automatically, preventing decode errors

**Example - compound_v3_base_usdc:**
- Deployed: 2024-03-11
- Days skipped: Jan 1 - Mar 10 = **70 days**
- Saves: 70 RPC calls that would have failed

## How It Works

1. **load_deployment_dates()** - Loads `deployment_dates.yaml` at script start
2. **should_collect_date()** - Checks if date >= deployment_date for each CSU
3. **Task generation** - Skips tasks where `should_collect_date()` returns False

## Next Steps

### 1. Verify Remaining Dates

Run the deployment finder to get exact dates:

```bash
source .env
python3 scripts/find_contract_deployment.py --csu fluid_lending_ethereum
python3 scripts/find_contract_deployment.py --csu fluid_lending_base
```

### 2. Fix POA Middleware for Linea/Scroll

The script needs POA middleware to convert block numbers to dates for these chains.

### 3. Add More CSUs

If you find other CSUs with decode errors, add their deployment dates to `deployment_dates.yaml`.

## Usage

The deployment date filtering is **automatic** - no changes needed to run commands:

```bash
# Normal collection - automatically skips pre-deployment tasks
source .env
python3 scripts/collect_tvl_parallel.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --workers 2
```

The script will print:
```
📊 Collection Plan:
   Total tasks: 12,810 (35 CSUs × 366 days)
   Already completed: 2,531
   Skipped (pre-deployment): 520
   Remaining: 9,759
```

## Benefits

1. **Reduces wasted RPC calls** - No more attempts on blocks before contract deployment
2. **Cleaner error logs** - Eliminates ~500-700 "decode error" failures
3. **Faster collection** - Skip tasks that would always fail
4. **Better progress tracking** - Accurate "remaining tasks" count

## Files Reference

- **Config**: [code/config/deployment_dates.yaml](code/config/deployment_dates.yaml)
- **Finder Script**: [scripts/find_contract_deployment.py](scripts/find_contract_deployment.py)
- **Collection Script**: [scripts/collect_tvl_parallel.py](scripts/collect_tvl_parallel.py)
