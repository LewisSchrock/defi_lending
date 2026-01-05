import json
from pathlib import Path
import yaml

def _load_chain_cfg():
    # tvl/ directory
    this_dir = Path(__file__).resolve().parent
    # project root is one level up: /.../code
    project_root = this_dir.parent
    # config/chains.yaml under project root
    path = project_root / "config" / "chains.yaml"

    with path.open("r") as f:
        return yaml.safe_load(f)

CHAIN_CFG = _load_chain_cfg()
PROVIDERS = CHAIN_CFG.get("providers", {})

# --------- ABIs ----------
PROVIDER_ABI = [
    {"inputs":[],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getPriceOracle","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getPoolDataProvider","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
]

POOL_ABI = [
    {"inputs":[],"name":"getReservesList","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],
     "stateMutability":"view","type":"function"},
]

DATA_PROVIDER_ABI = [
    {"inputs":[{"internalType":"address","name":"asset","type":"address"}],
     "name":"getReserveTokensAddresses",
     "outputs":[
         {"internalType":"address","name":"aTokenAddress","type":"address"},
         {"internalType":"address","name":"stableDebtTokenAddress","type":"address"},
         {"internalType":"address","name":"variableDebtTokenAddress","type":"address"}
     ],
     "stateMutability":"view","type":"function"},
]

ORACLE_ABI = [
    {"inputs":[{"internalType":"address","name":"asset","type":"address"}],
     "name":"getAssetPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
]

ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"},
]

# Compound-specific ABIs
COMPTROLLER_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"name": "", "type": "address[]"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

CTOKEN_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalBorrows",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "getCash",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalReserves",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "exchangeRateStored",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "underlying",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

ASSET_CLASS_OVERRIDES = {
    "USDC": "base",
    "DAI": "base",
    "USDT": "base",
    "FRAX": "base",
    "LUSD": "base",
    "WETH": "wrapped",
    "WBTC": "wrapped",
    "stETH": "LST",
    "wstETH": "LST",
    "rETH": "LST",
    "cbETH": "LST",
    "weETH": "LST",
    "osETH": "LST",
    "GHO": "synthetic",
    "crvUSD": "synthetic",
    "USDe": "synthetic",
    "sUSDe": "synthetic",
    "eUSDe": "synthetic",
    "RLUSD": "synthetic",
    "AAVE": "gov_token",
    "BAL": "gov_token",
    "CRV": "gov_token",
    "UNI": "gov_token",
    "SNX": "gov_token",
}

FLUID_FTOKEN_ABI = [
    {
        "inputs": [],
        "name": "asset",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

FLUID_LENDING_RESOLVER_ABI = [
    {
        "inputs": [],
        "name": "getAllFTokens",
        "outputs": [
            {
                "internalType": "address[]",
                "name": "",
                "type": "address[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]