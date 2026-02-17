# On-Chain Data Pipeline Documentation

**Last Updated**: February 16, 2026
**Data Period**: August 2023 - February 2026
**Pipeline**: Bronze → Silver → Gold → Analysis

This document traces all on-chain data from blockchain sources through each transformation tier.

---

## 📊 Data Sources & Flow Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ON-CHAIN SOURCES (via RPC)                                              │
│  ├── Blockchain Events (eth_getLogs)                                     │
│  ├── Contract State (eth_call)                                           │
│  └── Block Data (eth_getBlockByNumber)                                   │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│  BRONZE - Raw On-Chain Data (929 MB)                                     │
│  ├── liquidations/  - Raw event logs from liquidation events             │
│  └── tvl/           - Daily contract state snapshots                     │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│  SILVER - Cleaned & Validated (486 MB)                                   │
│  ├── liquidations/  - Parsed events with protocol-specific fields        │
│  └── tvl/           - Aggregated CSU-level TVL by date                   │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│  GOLD - Analysis-Ready Panel Data (24 MB)                                │
│  ├── liquidations/  - Daily liquidation panel by CSU                     │
│  ├── panel_base_eth/ - Base + Ethereum CSU panel                         │
│  └── collateral_composition/ - Basket composition by CSU-date            │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│  ANALYSIS - Final Datasets (20 MB)                                       │
│  └── panel_svar_data_qualified.parquet - 22 CSUs, 3 variables           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🌐 Data Type 1: Liquidation Events

### On-Chain Source
**Source**: Blockchain event logs (EVM `LOG` opcodes)
**Method**: `eth_getLogs` via RPC providers
**Reliability**: Immutable blockchain data, 100% reliable post-finality

### Bronze Tier: Raw Liquidation Events

**Location**: `data/bronze/liquidations/{chain}/`
**Format**: Raw JSON event logs
**Collection Script**: `scripts/collect_liquidations_parallel.py`

**On-Chain Data Collected**:
```json
{
  "address": "0x...",          // Contract that emitted event
  "topics": ["0x...", ...],    // Event signature + indexed params
  "data": "0x...",             // ABI-encoded non-indexed params
  "blockNumber": "0x...",      // Block number (hex)
  "transactionHash": "0x...",  // Transaction hash
  "logIndex": "0x...",         // Log index within block
  "blockTimestamp": 1234567890 // Added via eth_getBlockByNumber
}
```

**Collection Process**:
1. **Event Signature Detection**: Query `eth_getLogs` for known liquidation event signatures:
   - `Aave V3`: `0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286`
   - `Compound V3 Collateral`: `0x9850ab1af75177e4a7e9870da8a34d4979b71cc4cd596df22ba4fb8b571430b9`
   - `Compound V3 Debt`: `0x1547a878dc89ad3c367b6338b4be6a65a5dd74fb77ae044da1e8747ef1f4f62f`
   - `Compound V2`: `0x298637f684da70674f26509b10f07ec2fbc77a335ab1e7d6215a4b2484d8bb52`
   - `Fluid`: `0x64f7c2c46814e079964a1934953e50adc025dc52cdbeb7d8e478e9fb9bfd2c2d`
   - `Gearbox`: `0x7dfecd8419723a9d3954585a30c2a270165d70aafa146c11c1e1b88ae1439064`
   - `Cap`: `0xf3fa0eaee8f258c23b013654df25d1527f98a5c7ccd5e951dd77caca400ef972`
   - `Lista`: `0xa4946ede45d0c6f06a0f5ce92c9ad3b4751452d2fe0e25010783bcab57a67e41`

2. **Block Range Scanning**:
   - Query by date range (converted to block numbers via binary search)
   - Parallel workers (13 Alchemy accounts) process chunks simultaneously
   - Each worker manages own rate limiting

3. **Timestamp Enrichment**:
   - Fetch block timestamp via `eth_getBlockByNumber` for each unique block
   - Cache block timestamps in `data/reference/block_timestamps_{chain}.json`

**RPC Providers Used**:
- **Primary**: Alchemy (13 accounts for parallelization)
- **Fallback**: Infura, Ankr
- **Rate Limits**: 330 CU/sec per account (Alchemy)

**Chains Covered**:
- Ethereum, Arbitrum, Base, Optimism, Polygon, Avalanche, BSC, Gnosis, Linea, Scroll, Ink

**File Structure**:
```
data/bronze/liquidations/
├── ethereum/
│   ├── checkpoint.json          # Collection progress tracker
│   └── events/
│       └── liquidations_YYYYMMDD.jsonl   # Raw events by collection date
├── arbitrum/
├── base/
└── ... (one folder per chain)
```

**Data Characteristics**:
- **Size**: ~929 MB total
- **Reliability**: 100% on-chain, immutable
- **Completeness**: Event logs are complete post-finality (12-64 blocks)
- **Validation**: Cross-check block numbers, transaction hashes

---

### Silver Tier: Parsed Liquidation Events

**Location**: `data/silver/liquidations/{chain}/liquidations.parquet`
**Format**: Parquet (columnar)
**Processing Script**: `scripts/parse_raw_liquidations.py`

**Transformation Steps**:

1. **Event Signature Decoding**:
   - Identify protocol from `topic[0]` (event signature)
   - ABI-decode `topics` and `data` fields into human-readable parameters

2. **Protocol-Specific Parsing**:

   **Aave V3 / SparkLend / Tydro**:
   ```python
   LiquidationCall(
       collateralAsset,   # Address
       debtAsset,         # Address
       user,              # Address (borrower)
       debtToCover,       # uint256 (debt repaid)
       liquidatedCollateralAmount,  # uint256 (collateral seized)
       liquidator,        # Address
       receiveAToken      # bool
   )
   ```
   - CSU Resolution: Chain + Pool address → `aave_v3_{chain}`, `sparklend_ethereum`, `tydro_ink`

   **Compound V3**:
   ```python
   AbsorbCollateral(
       absorber,          # Address (liquidator)
       borrower,          # Address
       asset,             # Address (collateral token)
       collateralAbsorbed,  # uint256
       usdValue           # uint256
   )

   AbsorbDebt(
       absorber,          # Address
       borrower,          # Address
       basePaidOut,       # uint256 (debt token repaid)
       usdValue           # uint256
   )
   ```
   - CSU Resolution: Contract address → Specific market (e.g., `compound_v3_eth_usdc`)
   - Combine AbsorbCollateral + AbsorbDebt events from same transaction

   **Compound V2 / Venus / Moonwell / Benqi**:
   ```python
   LiquidateBorrow(
       liquidator,        # Address
       borrower,          # Address
       repayAmount,       # uint256 (debt repaid)
       cTokenCollateral,  # Address (cToken seized)
       seizeTokens        # uint256 (cTokens seized)
   )
   ```
   - CSU Resolution: Chain → Primary fork (e.g., `base` → `moonwell_lending_base`)

   **Fluid**:
   ```python
   Liquidation(
       liquidator,        # Address
       borrower,          # Address
       debtToken,         # Address
       collateralToken,   # Address
       debtAmount,        # uint256
       collateralAmount   # uint256
   )
   ```

3. **Standardized Output Schema**:
   ```
   date              datetime  # Date (UTC) from block timestamp
   block_number      int       # Block number
   tx_hash           str       # Transaction hash
   log_index         int       # Log index
   csu               str       # CSU identifier (e.g., "aave_v3_ethereum")
   protocol          str       # Protocol type (e.g., "aave_v3")
   borrower          str       # Borrower address (lowercase)
   liquidator        str       # Liquidator address (lowercase)
   collateral_token  str       # Collateral token address
   debt_token        str       # Debt token address
   collateral_amount float     # Collateral seized (raw units)
   debt_amount       float     # Debt repaid (raw units)
   ```

**Data Quality**:
- **Validation**: Check for duplicate (tx_hash, log_index)
- **Filtering**: Remove events with zero amounts
- **Normalization**: All addresses lowercase, standardized CSU names

**File Size**: ~486 MB total across all chains

---

### Gold Tier: Daily Liquidation Panel

**Location**: `data/gold/liquidations/all_chains/daily_panel.parquet`
**Format**: Parquet panel data (date × CSU)
**Processing Script**: `scripts/build_gold_liquidations.py`

**Transformation Steps**:

1. **Price Enrichment** (from `scripts/enrich_liquidations_multi_oracle.py`):
   - Fetch on-chain oracle prices for collateral/debt tokens at liquidation blocks
   - Use protocol-specific oracles:
     - Aave: ChainlinkAggregator
     - Compound: PriceFeed contract
     - Uniswap V3 TWAP for missing tokens
   - Cache prices in `data/reference/price_cache_liquidations_{chain}.json`

2. **USD Conversion**:
   ```python
   collateral_usd = collateral_amount * (collateral_price / 10**collateral_decimals)
   debt_usd = debt_amount * (debt_price / 10**debt_decimals)
   ```

3. **Daily Aggregation**:
   ```python
   daily_panel = liquidations.groupby(['date', 'csu']).agg({
       'collateral_usd': 'sum',    # Total collateral seized (USD)
       'debt_usd': 'sum',          # Total debt repaid (USD)
       'tx_hash': 'nunique',       # Number of liquidation transactions
       'borrower': 'nunique'       # Number of unique borrowers liquidated
   })
   ```

**Schema**:
```
date                 datetime   # Date (UTC)
csu                  str        # CSU identifier
total_collateral_usd float      # Sum of collateral seized (USD)
total_debt_usd       float      # Sum of debt repaid (USD)
n_liquidations       int        # Count of liquidation events
n_borrowers          int        # Count of unique borrowers
```

**Coverage**: All CSUs with liquidation data (22+ CSUs)

---

## 🏦 Data Type 2: TVL (Total Value Locked)

### On-Chain Source
**Source**: Smart contract state variables
**Method**: `eth_call` to read contract storage
**Reliability**: 100% reliable, deterministic contract reads

### Bronze Tier: Daily TVL Snapshots

**Location**: `data/bronze/tvl/{csu}/YYYY-MM-DD.json`
**Format**: JSON (one file per CSU per day)
**Collection Script**: `scripts/collect_tvl_parallel.py`

**On-Chain Data Collected**:

For each market/pool in a CSU, call protocol-specific view functions:

**Aave V3**:
```solidity
// Pool.getReserveData(address asset) returns ReserveData
{
  "configuration": {...},
  "liquidityIndex": "...",        // Ray (1e27)
  "currentLiquidityRate": "...",  // Ray
  "variableBorrowIndex": "...",   // Ray
  "currentVariableBorrowRate": "...", // Ray
  "currentStableBorrowRate": "...",   // Ray
  "lastUpdateTimestamp": 123,
  "id": 0,
  "aTokenAddress": "0x...",
  "stableDebtTokenAddress": "0x...",
  "variableDebtTokenAddress": "0x..."
}

// Then call totalSupply() on each token:
aToken.totalSupply()           → total supplied (raw)
variableDebtToken.totalSupply() → total borrowed (raw)
```

**Compound V3**:
```solidity
// Comet.totalsBasic() returns (uint104 borrowed, uint104 supplied)
{
  "baseSupplyIndex": "...",   // uint64
  "trackingSupplyIndex": "...", // uint64
  "trackingBorrowIndex": "...", // uint64
  "totalSupplyBase": "...",   // uint104 (supplied)
  "totalBorrowBase": "...",   // uint104 (borrowed)
  "lastAccrualTime": 123,     // uint40
  "pauseFlags": 0             // uint8
}
```

**Compound V2 / Forks**:
```solidity
cToken.totalSupply()       → total cTokens
cToken.totalBorrows()      → total borrowed (underlying)
cToken.getCash()           → cash on hand
cToken.exchangeRateCurrent() → cToken:underlying ratio
```

**Collection Process**:
1. **Daily Snapshots**: Call at midnight UTC (or latest block before midnight)
2. **Multi-Call Batching**: Use Multicall3 contract to batch reads (gas efficient)
3. **Block Number Caching**: Cache midnight block numbers per chain
4. **Market Discovery**: Query protocol registries for active markets

**File Structure** (per CSU):
```json
{
  "csu": "aave_v3_ethereum",
  "chain": "ethereum",
  "date": "2024-01-01",
  "block_number": 18885000,
  "markets": [
    {
      "asset": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  // WETH
      "symbol": "WETH",
      "decimals": 18,
      "total_supplied_raw": "1234567890123456789012345",
      "total_borrowed_raw": "987654321098765432109876",
      "supply_apy": "0.0234",
      "borrow_apy": "0.0456"
    },
    // ... one per market
  ]
}
```

**Data Characteristics**:
- **Size**: ~929 MB total (daily snapshots accumulate)
- **Reliability**: 100% deterministic contract reads
- **Completeness**: One snapshot per CSU per day
- **Validation**: Check block numbers match expected dates

---

### Silver Tier: Aggregated Daily TVL

**Location**: `data/silver/tvl/daily_tvl.csv`
**Format**: CSV (consolidated across all CSUs)
**Processing Script**: `scripts/build_silver_tvl.py`

**Transformation Steps**:

1. **Token Price Lookup**:
   - Use Chainlink oracles for major tokens (WETH, USDC, USDT, DAI, etc.)
   - Cache prices in `data/reference/price_cache_{chain}.json`
   - Fallback to Uniswap V3 TWAP for long-tail tokens

2. **USD Conversion**:
   ```python
   supplied_usd = (total_supplied_raw / 10**decimals) * token_price_usd
   borrowed_usd = (total_borrowed_raw / 10**decimals) * token_price_usd
   ```

3. **CSU-Level Aggregation**:
   ```python
   daily_tvl = markets.groupby(['date', 'csu']).agg({
       'supplied_usd': 'sum',   # Total supplied across all markets
       'borrowed_usd': 'sum',   # Total borrowed across all markets
   })
   ```

**Schema**:
```
date               datetime   # Date (UTC)
csu                str        # CSU identifier
total_supply_usd   float      # Total supplied (USD) - sum across markets
total_borrow_usd   float      # Total borrowed (USD) - sum across markets
n_markets          int        # Number of active markets
```

**Coverage**: 42 CSUs across 11 chains

**File Size**: ~486 MB

**Data Quality**:
- **Validation**: Check for missing dates (fill forward if < 7 days gap)
- **Outlier Detection**: Flag sudden 10x changes in TVL
- **Consistency**: Cross-check with on-chain total supply if available

---

### Gold Tier: Panel TVL Data

**Location**: Integrated into gold panels (e.g., `data/gold/panel_base_eth/gold_panel_base_eth.parquet`)
**Format**: Parquet panel data
**Processing Script**: `scripts/build_gold_panel_base_eth.py`

**Transformation**: None (Silver TVL is already analysis-ready)

---

## 🎨 Data Type 3: Collateral Composition

### On-Chain Source
**Source**: Liquidation events (collateral tokens) + contract state (balances)
**Method**: Aggregated from Bronze liquidations + Silver TVL
**Reliability**: Derived from on-chain data

### Gold Tier: Daily Collateral Baskets

**Location**: `data/gold/collateral_composition/{chain}/all_csus_composition.parquet`
**Format**: Parquet (date × CSU × token)
**Processing Script**: `scripts/build_collateral_composition.py`

**Transformation Steps**:

1. **Extract Collateral Tokens**:
   ```python
   # From liquidation events
   collateral_tokens = liquidations.groupby(['date', 'csu', 'collateral_token']).agg({
       'collateral_amount': 'sum',
       'collateral_usd': 'sum'
   })
   ```

2. **Weight Calculation**:
   ```python
   # Daily basket weights
   basket = collateral_tokens.groupby(['date', 'csu']).apply(
       lambda x: x['collateral_usd'] / x['collateral_usd'].sum()
   )
   ```

3. **Token Metadata**:
   - Fetch token symbol, decimals from `data/reference/token_registry_{chain}.json`
   - Built from on-chain `ERC20.symbol()` and `ERC20.decimals()` calls

**Schema**:
```
date           datetime  # Date (UTC)
csu            str       # CSU identifier
token_address  str       # Collateral token address
token_symbol   str       # Token symbol (e.g., "WETH")
weight         float     # % of total collateral (0-1)
amount_usd     float     # USD value in basket
```

**Usage**: Calculate collateral-weighted basket volatility for Panel SVAR

---

## 📐 Data Type 4: Reference Data (Prices & Metadata)

### On-Chain Sources

**Location**: `data/reference/`

#### 4.1 Block Timestamps

**Source**: `eth_getBlockByNumber`
**File**: `block_timestamps_{chain}.json`
**Format**: `{block_number: timestamp}`

```json
{
  "18885000": 1704067200,
  "18885001": 1704067212,
  ...
}
```

**Collection**: Built during liquidation collection, cached for reuse

---

#### 4.2 Token Metadata

**Source**: On-chain ERC20 contract calls
**File**: `token_registry_{chain}.json`
**Methods**: `ERC20.symbol()`, `ERC20.decimals()`, `ERC20.name()`

```json
{
  "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": {
    "symbol": "WETH",
    "decimals": 18,
    "name": "Wrapped Ether",
    "chain": "ethereum"
  },
  ...
}
```

**Collection**: On-demand during parsing, cached forever (immutable)

---

#### 4.3 Oracle Prices

**Source**: On-chain Chainlink, Uniswap V3 TWAP
**Files**:
- `price_cache_ethereum.json`
- `price_cache_liquidations_{chain}.json`

**Chainlink Oracle Reads**:
```solidity
AggregatorV3Interface.latestRoundData() returns (
  uint80 roundId,
  int256 answer,         // Price in oracle decimals (typically 8)
  uint256 startedAt,
  uint256 updatedAt,
  uint80 answeredInRound
)
```

**Uniswap V3 TWAP**:
```solidity
// Query pool.observe() for 30-minute TWAP
pool.observe([1800, 0])  // 30 min ago, now
```

**Format**:
```json
{
  "ethereum:0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2:18885000": {
    "price_usd": 2234.56,
    "source": "chainlink",
    "decimals": 8,
    "timestamp": 1704067200
  },
  ...
}
```

**Cache Key**: `{chain}:{token_address}:{block_number}`

---

## 🎯 Analysis Tier: Panel SVAR Dataset

**Location**: `data/analysis/panel_svar_data_qualified.parquet`
**Format**: Parquet panel data (date × CSU)
**Processing Script**: `scripts/prepare_panel_svar_data.py`

### Transformations from Gold → Analysis

#### Variable 1: Utilization (Leverage Ratio)

**Source**: Silver TVL data
**Formula**:
```python
utilization = total_borrow_usd / total_supply_usd
```

**Bounds**: Clipped to [0, 1]
**Economic Meaning**: Protocol leverage, measures capital efficiency

---

#### Variable 2: Liquidation (Log-Transformed)

**Source**: Gold liquidations panel
**Formula**:
```python
liquidation = log(1 + total_collateral_usd)
```

**Transformation Rationale**:
- Handle zeros (no liquidations on some days)
- Reduce right-skew (large liquidation cascades)
- Interpretable as % change in IRFs

**Economic Meaning**: Severity of liquidation activity

---

#### Variable 3: Volatility (Collateral-Weighted Basket)

**Source**: Gold collateral composition + Reference prices
**Formula**:
```python
# Step 1: Calculate daily token returns
returns[token] = (price[t] - price[t-1]) / price[t-1]

# Step 2: Weight by collateral basket composition
basket_return[t] = sum(weight[token] * returns[token])

# Step 3: Rolling standard deviation (7-day window)
volatility[t] = rolling_std(basket_return, window=7)
```

**Economic Meaning**: Collateral risk exposure, measures portfolio volatility

---

### Final Dataset Schema

```
date         datetime   # Date (UTC)
csu          str        # CSU identifier
utilization  float      # Leverage ratio (0-1)
liquidation  float      # log(1 + collateral_seized_usd)
volatility   float      # 7-day rolling std of basket returns
```

**Coverage Filtering**:
- Include CSUs with ≥70% data coverage across all 3 variables
- Result: 22 qualified CSUs, 20,218 observations

---

## ✅ Data Quality & Validation

### On-Chain Data Reliability

1. **Immutability**: All blockchain data is immutable post-finality
2. **Determinism**: Contract state reads are deterministic
3. **Validation**: Cross-check with block explorers (Etherscan, Arbiscan, etc.)

### Transformation Validation

**Bronze → Silver**:
- [ ] No duplicate events (tx_hash + log_index unique)
- [ ] All events have valid block timestamps
- [ ] Token addresses checksummed correctly

**Silver → Gold**:
- [ ] Price data available for ≥95% of liquidations
- [ ] TVL aggregations match sum of markets
- [ ] No missing dates (forward-fill < 7 days)

**Gold → Analysis**:
- [ ] No infinite/NaN values in final panel
- [ ] Coverage ≥70% for qualified CSUs
- [ ] Variable distributions reasonable (no 1000x outliers)

### Data Lineage

Every analysis datapoint can be traced back to:
1. **Transaction hash** (liquidations)
2. **Block number** (TVL snapshots)
3. **Oracle contract** (prices)
4. **Smart contract address** (metadata)

---

## 🔄 Update Frequency

- **Bronze**: Updated as needed (historical collection complete)
- **Silver**: Regenerated when Bronze changes
- **Gold**: Regenerated when Silver changes
- **Analysis**: Regenerated when Gold changes or variables redefined

**Last Full Pipeline Run**: February 16, 2026

---

## 📁 File Size Summary

```
Bronze:   929 MB   (raw on-chain data)
Silver:   486 MB   (parsed & validated)
Gold:      24 MB   (analysis-ready panels)
Analysis:  20 MB   (final SVAR dataset)
Reference: 25 MB   (prices, metadata, block timestamps)
───────────────────
Total:    1.48 GB
```

---

## 🛠️ Reproducibility

To reproduce the entire pipeline from scratch:

```bash
# 1. Collect raw on-chain data
python scripts/collect_liquidations_parallel.py --chain all --start-date 2023-08-01 --end-date 2026-02-12
python scripts/collect_tvl_parallel.py --start-date 2023-08-01 --end-date 2026-02-12

# 2. Parse & clean (Bronze → Silver)
python scripts/parse_raw_liquidations.py --chain all
python scripts/build_silver_tvl.py

# 3. Enrich with prices
python scripts/enrich_liquidations_multi_oracle.py --chain all

# 4. Build analysis panels (Silver → Gold)
python scripts/build_gold_liquidations.py
python scripts/build_gold_panel_base_eth.py
python scripts/build_collateral_composition.py

# 5. Prepare SVAR dataset (Gold → Analysis)
python scripts/prepare_panel_svar_data.py --threshold 0.70
```

**RPC Requirements**:
- 13 Alchemy accounts (or equivalent rate limits)
- ~1M RPC calls for full historical collection
- ~24 hours for complete pipeline

---

## 📚 Related Documentation

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Project organization
- [README.md](README.md) - Quick start guide
- Protocol adapter code: `adapters/liquidations/`, `adapters/tvl/`
- Processing scripts: `scripts/`

---

**Maintained By**: Thesis v2.10 Team
**Contact**: See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
