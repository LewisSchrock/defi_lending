from web3 import Web3
import requests
import csv
from datetime import datetime

# 1. RPC setup (Polygon Mainnet via Alchemy)
w3 = Web3(Web3.HTTPProvider("https://polygon-mainnet.g.alchemy.com/v2/cEHzRdgL5rGydq_YIokK2"))
assert w3.is_connected(), "RPC connection failed"

# 2. aTokens and their Coingecko IDs
tokens = [
    {"symbol": "USDC",  "aToken": "0x625E7708f30cA75bfd92586e17077590C60eb4cD", "coingecko_id": "usd-coin"},
    {"symbol": "DAI",   "aToken": "0x078f358208685046a11C85e8ad32895DED33A249", "coingecko_id": "dai"},
    {"symbol": "USDT",  "aToken": "0x6ab707Aca953eDAeFBc4fD23bA73294241490620", "coingecko_id": "tether"},
    {"symbol": "WETH",  "aToken": "0xe50fA9b3c56FfB159cB0FCA61F5c9D750e8128c8", "coingecko_id": "weth"},
    {"symbol": "WMATIC","aToken": "0x8343091F2499FD4b6174A46D067A920a3b851FF9", "coingecko_id": "wmatic"},
    {"symbol": "WBTC",  "aToken": "0x1F3Af095CDa17d63cad238358837321e95FC5915", "coingecko_id": "wrapped-bitcoin"},
    {"symbol": "AAVE",  "aToken": "0x078f358208685046a11C85e8ad32895DED33A249", "coingecko_id": "aave"},
    {"symbol": "GHST",  "aToken": "0x3EF10DFf4928279c004308EbADc4Db8B7620d6fc", "coingecko_id": "aavegotchi"},
    {"symbol": "CRV",   "aToken": "0x8f9fA3Dab22dD5CdfEC96f31E1C4e68cA0c9bC57", "coingecko_id": "curve-dao-token"},
    {"symbol": "BAL",   "aToken": "0xCCed3781D7FD6BdC3B4D7d91F4bE5156fEdcA7e3", "coingecko_id": "balancer"},
    {"symbol": "SUSHI", "aToken": "0x69A7098a3E0188A1B35151f252eC0Fb5e962BB42", "coingecko_id": "sushi"},
    {"symbol": "LINK",  "aToken": "0x66e4B3B8Ec70AA5F9C5eaaF5D9Fc7D1a6556F043", "coingecko_id": "chainlink"},
    {"symbol": "MAI",   "aToken": "0x0d58EdB835Aa8A323EE8A89d38bD313e4fE9a06E", "coingecko_id": "mai"},
    {"symbol": "EURS",  "aToken": "0xC3c28c8Bf7d30aC214b2e2aC7f587d2D2E1dBdE8", "coingecko_id": "stasis-eurs"},
]

# 3. ABI for totalSupply() and decimals()
aToken_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

# 4. Get all USD prices from CoinGecko in one call
def get_prices(token_ids):
    ids = ",".join(token_ids)
    url = "https://api.coingecko.com/api/v3/simple/price"
    r = requests.get(url, params={"ids": ids, "vs_currencies": "usd"})
    return r.json()

token_ids = [t["coingecko_id"] for t in tokens]
prices = get_prices(token_ids)

# 5. Output setup
results = []
total_usd = 0
chain = "Polygon"
protocol = "Aave V3"
date_str = datetime.utcnow().strftime("%Y-%m-%d")

print(f"\n📊 {protocol} {chain} TVL Breakdown ({date_str}):\n")

for t in tokens:
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(t["aToken"]), abi=aToken_ABI)
        supply = contract.functions.totalSupply().call()
        decimals = contract.functions.decimals().call()
        normalized = supply / (10 ** decimals)

        price = prices.get(t["coingecko_id"], {}).get("usd", None)
        if price is None:
            print(f"⚠️ Missing price for {t['symbol']}")
            continue

        usd_value = normalized * price
        total_usd += usd_value

        print(f"{t['symbol']:6} → {normalized:,.2f} × ${price:.2f} = ${usd_value:,.2f}")

        results.append({
            "protocol": protocol,
            "chain": chain,
            "date": date_str,
            "token": t["symbol"],
            "amount": normalized,
            "price": price,
            "usd_value": usd_value
        })

    except Exception as e:
        print(f"⚠️ Error for {t['symbol']}: {e}")

# Add TOTAL row
results.append({
    "protocol": protocol,
    "chain": chain,
    "date": date_str,
    "token": "TOTAL",
    "amount": "",
    "price": "",
    "usd_value": total_usd
})

# 6. Save to CSV
filename = f"aave_polygon_tvl_{date_str}.csv"
with open(filename, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["protocol", "chain", "date", "token", "amount", "price", "usd_value"])
    writer.writeheader()
    writer.writerows(results)

print(f"\n✅ TVL data written to: {filename}")
