from web3 import Web3
from datetime import datetime
import csv

# ---------- RPC setup ----------
RPC = "https://eth-mainnet.g.alchemy.com/v2/cEHzRdgL5rGydq_YIokK2"
w3 = Web3(Web3.HTTPProvider(RPC))
assert w3.is_connected(), "❌ RPC connection failed"

# ---------- Core contracts ----------
ADDRESSES_PROVIDER = Web3.to_checksum_address("0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e")  # Ethereum V3
DATA_PROVIDER      = Web3.to_checksum_address("0x0a16f2FCC0D44FaE41cc54e079281D84A363bECD")

# ---------- ABIs ----------
ADDRESSES_PROVIDER_ABI = [
    {"inputs":[],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getPriceOracle","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]

POOL_ABI = [
    {"inputs":[],"name":"getReservesList","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],
     "stateMutability":"view","type":"function"}
]

DATA_PROVIDER_ABI = [
    {"inputs":[{"internalType":"address","name":"asset","type":"address"}],
     "name":"getReserveTokensAddresses",
     "outputs":[
         {"internalType":"address","name":"aTokenAddress","type":"address"},
         {"internalType":"address","name":"stableDebtTokenAddress","type":"address"},
         {"internalType":"address","name":"variableDebtTokenAddress","type":"address"}
     ],
     "stateMutability":"view","type":"function"}
]

ORACLE_ABI = [
    {"inputs":[{"internalType":"address","name":"asset","type":"address"}],
     "name":"getAssetPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"asset","type":"address"}],
     "name":"getSourceOfAsset","outputs":[{"internalType":"address","name":"","type":"address"}],
     "stateMutability":"view","type":"function"}
]

CHAINLINK_FEED_ABI = [
    {"inputs": [], "name": "description", "outputs": [{"internalType": "string", "name": "", "type": "string"}],
     "stateMutability": "view", "type": "function"}
]

ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}
]

# ---------- Initialize contracts ----------
provider = w3.eth.contract(address=ADDRESSES_PROVIDER, abi=ADDRESSES_PROVIDER_ABI)
pool_addr = provider.functions.getPool().call()
oracle_addr = provider.functions.getPriceOracle().call()

pool   = w3.eth.contract(address=pool_addr, abi=POOL_ABI)
oracle = w3.eth.contract(address=oracle_addr, abi=ORACLE_ABI)
dp     = w3.eth.contract(address=DATA_PROVIDER, abi=DATA_PROVIDER_ABI)

# ---------- Helper functions ----------
def classify_from_oracle(asset, symbol):
    """Classify based on oracle feed description and symbol fallback."""
    try:
        src = oracle.functions.getSourceOfAsset(asset).call()
        feed = w3.eth.contract(address=src, abi=CHAINLINK_FEED_ABI)
        desc = feed.functions.description().call()
        desc = desc.upper()

        if "/ETH" in desc:
            return "LST"
        elif "STETH" in desc or "RETH" in desc:
            return "LST"
        elif "USDE" in desc or "SUSDE" in desc or "CRVUSD" in desc:
            return "Synthetic"
        elif "/USD" in desc:
            return "Base"
        else:
            return "Other"
    except Exception:
        # Fallback to symbol heuristic
        s = symbol.upper()
        if "STETH" in s or "RETH" in s or "ETHX" in s or "WEETH" in s:
            return "LST"
        elif "USDE" in s or "SUSDE" in s or "CRVUSD" in s:
            return "Synthetic"
        else:
            return "Unknown"

# ---------- Enumerate reserves ----------
reserves = pool.functions.getReservesList().call()
print(f"Found {len(reserves)} reserves.")
results = []
total_usd = 0
base_usd = 0
date_str = datetime.utcnow().strftime("%Y-%m-%d")

for asset in reserves:
    try:
        aToken, _, _ = dp.functions.getReserveTokensAddresses(asset).call()
        aToken_contract = w3.eth.contract(address=aToken, abi=ERC20_ABI)
        decimals = aToken_contract.functions.decimals().call()
        symbol = aToken_contract.functions.symbol().call()
        raw_supply = aToken_contract.functions.totalSupply().call()
        normalized_supply = raw_supply / (10 ** decimals)
        price = oracle.functions.getAssetPrice(asset).call() / 1e8  # 1e8 precision
        tvl = normalized_supply * price
        category = classify_from_oracle(asset, symbol)

        total_usd += tvl
        if category == "Base":
            base_usd += tvl

        results.append({
            "symbol": symbol,
            "asset": asset,
            "aToken": aToken,
            "supply": normalized_supply,
            "price_usd": price,
            "tvl_usd": tvl,
            "category": category
        })

        print(f"{symbol:10}  {category:10}  {normalized_supply:>15,.2f} × ${price:<10.2f} = ${tvl:,.2f}")

    except Exception as e:
        print(f"⚠️ Error for {asset}: {e}")

print(f"\n✅ Total TVL (all reserves): ${total_usd:,.2f}")
print(f"✅ Base TVL (Aave/DefiLlama-style): ${base_usd:,.2f}")
print(f"🔹 LST/Synthetic share: {(1 - base_usd/total_usd)*100:.2f}% of total")

# ---------- Save CSV ----------
with open(f"aave_v3_eth_tvl_classified_{date_str}.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["symbol","asset","aToken","supply","price_usd","tvl_usd","category"])
    writer.writeheader()
    writer.writerows(results)
