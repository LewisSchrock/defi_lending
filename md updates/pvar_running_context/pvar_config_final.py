# ============================================================================
# Panel SVAR Configuration - FINAL VERSION
# For: Pedroni_Panel_SVAR and statsmodels comparison
# ============================================================================

# Data source
excel_path = "vol_util_panel.xlsx"
excel_sheet_name = "panel_data"

# Panel structure
td_col = ["date"]
member_col = "csu"

# Variables
variables = {
    'utilization': [0],
    'volatility': [0],
}

# Cholesky ordering
variable_order = ['utilization', 'volatility']

# ============================================================================
# DATA QUALITY FILTERS
# ============================================================================

# Exclude CSUs with near-zero utilization (< 1%)
# These have no meaningful leverage to analyze
exclude_csus = [
    'fluid_lending_arbitrum',   # util = 0.000
    'fluid_lending_ethereum',   # util = 0.000
    'gearbox_ethereum',         # util = 0.000
    'sumermoney_meter',         # util = 0.003
    'compound_v3_base_usdbc',   # util = 0.000
]

# Optionally exclude CSUs with short time series
min_observations = 300  # At least ~10 months of data

# After filtering: 30 CSUs remain
# - Pooled: 14 (Aave 10, Benqi 1, Moonwell 1, Sparklend 1, Venus 1)
# - Isolated: 16 (Compound V3 markets)

# ============================================================================
# FINAL CSU LISTS (After Quality Filters)
# ============================================================================

pooled_csus = [
    # Aave V3 (10 chains - exclude scroll if min_obs filter)
    'aave_v3_arbitrum',      # 551 days, util=0.418
    'aave_v3_avalanche',     # 549 days, util=0.341
    'aave_v3_base',          # 551 days, util=0.457
    'aave_v3_binance',       # 550 days, util=0.332
    'aave_v3_ethereum',      # 551 days, util=0.428
    'aave_v3_linea',         # 323 days, util=0.415 (may exclude)
    'aave_v3_optimism',      # 551 days, util=0.380
    'aave_v3_polygon',       # 551 days, util=0.317
    'aave_v3_scroll',        # 70 days, util=0.415 (EXCLUDE - too short)
    'aave_v3_xdai',          # 550 days, util=0.250
    # Other pooled protocols
    'benqi_lending_avalanche',   # 548 days, util=0.645
    'moonwell_lending_base',     # 551 days, util=0.545
    'sparklend_ethereum',        # 551 days, util=0.354
    'venus_core_pool_binance',   # 551 days, util=0.342
]

isolated_csus = [
    'compound_v3_arb_usdc',      # 551 days, util=0.301
    'compound_v3_arb_usdc_e',    # 551 days, util=0.274
    'compound_v3_arb_usdt',      # 551 days, util=0.105
    'compound_v3_arb_weth',      # 551 days, util=0.418
    'compound_v3_base_aero',     # 446 days, util=0.184
    'compound_v3_base_usdc',     # 551 days, util=0.306
    'compound_v3_base_weth',     # 551 days, util=0.451
    'compound_v3_eth_usdc',      # 551 days, util=0.293
    'compound_v3_eth_usds',      # 439 days, util=0.490
    'compound_v3_eth_usdt',      # 544 days, util=0.289
    'compound_v3_eth_weth',      # 551 days, util=0.440
    'compound_v3_eth_wsteth',    # 384 days, util=0.207
    'compound_v3_op_usdc',       # 551 days, util=0.290
    'compound_v3_op_usdt',       # 551 days, util=0.303
    'compound_v3_op_weth',       # 526 days, util=0.439
    'compound_v3_poly_usdc',     # 551 days, util=0.297
]

# ============================================================================
# SECONDARY CATEGORIZATION: Base Asset Type
# ============================================================================

# For Compound V3 isolated markets, we can further categorize by base asset
stablecoin_markets = [
    'compound_v3_arb_usdc',
    'compound_v3_arb_usdc_e', 
    'compound_v3_arb_usdt',
    'compound_v3_base_usdc',
    'compound_v3_eth_usdc',
    'compound_v3_eth_usds',
    'compound_v3_eth_usdt',
    'compound_v3_op_usdc',
    'compound_v3_op_usdt',
    'compound_v3_poly_usdc',
]

volatile_asset_markets = [
    'compound_v3_arb_weth',
    'compound_v3_base_aero',
    'compound_v3_base_weth',
    'compound_v3_eth_weth',
    'compound_v3_eth_wsteth',
    'compound_v3_op_weth',
]

# ============================================================================
# VAR SETTINGS
# ============================================================================

var_lags = 2
max_lags = 10
include_fixed_effects = True
include_time_effects = False

# IRF settings
irf_periods = 20
n_bootstrap = 500
ci_level = 0.95
orthogonalized = True

# ============================================================================
# ANALYSIS RUNS
# ============================================================================

analyses_to_run = [
    {
        'name': 'full_sample',
        'description': 'All CSUs (after quality filters)',
        'csus': pooled_csus + isolated_csus,
    },
    {
        'name': 'pooled_only',
        'description': 'Pooled architecture (Aave, Benqi, Moonwell, Spark, Venus)',
        'csus': pooled_csus,
    },
    {
        'name': 'isolated_only', 
        'description': 'Isolated architecture (Compound V3)',
        'csus': isolated_csus,
    },
    {
        'name': 'stablecoin_markets',
        'description': 'Compound V3 stablecoin base markets',
        'csus': stablecoin_markets,
    },
    {
        'name': 'volatile_markets',
        'description': 'Compound V3 WETH/volatile base markets',
        'csus': volatile_asset_markets,
    },
]

# ============================================================================
# OUTPUT
# ============================================================================

output_dir = "results/"
save_plots = True
save_tables = True

# Summary stats to compute
summary_stats = [
    'observations',
    'csus',
    'granger_pvalue',
    'cumulative_irf',
    'peak_response',
    'peak_period',
    'half_life',
]
