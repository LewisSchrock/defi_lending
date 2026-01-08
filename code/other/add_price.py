# add prices to reserve data from CoinGecko

# Get to USD

import pandas as pd
import requests
from datetime import datetime

# 1. Mapping from your test file (symbol -> coingecko_id)
COINGECKO_IDS = {
    # Major stables
    "USDC": "usd-coin",
    "USDT": "tether",
    "DAI": "dai",
    "GUSD": "gemini-dollar",
    "LUSD": "liquity-usd",
    "USDS": "usds",
    "sUSD": "nusd",                # Synthetix sUSD
    "USDP": "pax-dollar",
    "TUSD": "true-usd",

    # ETH & derivs
    "WETH": "weth",
    "rETH": "rocket-pool-eth",
    "sETH": "seth",
    "stETH": "staked-ether",
    "cbETH": "coinbase-wrapped-staked-eth",
    "wstETH": "wrapped-steth",
    "ETHx": "stader-ethx",
    "weETH": "wrapped-eeth",
    "osETH": "stakewise-oseth",
    "ezETH": "renzo-restaked-eth",
    "rsETH": "kelp-dao-restaked-eth",
    "ankrETH": "ankreth",
    "lsETH": "liquid-staked-ethereum",
    "aEthWETH": "weth",            # sometimes appears as legacy wrapper

    # BTC wrappers
    "WBTC": "wrapped-bitcoin",
    "cbBTC": "coinbase-wrapped-btc",
    "tBTC": "tbtc",
    "sBTC": "synthetix-network-token",  # synthetix sbtc
    "wBTCb": "wrapped-bitcoin",    # some bridge aliases
    "BTCB": "binance-bitcoin",

    # Layer-1/2 tokens
    "AAVE": "aave",
    "LINK": "chainlink",
    "MKR": "maker",
    "UNI": "uniswap",
    "COMP": "compound-governance-token",
    "SNX": "synthetix-network-token",
    "CRV": "curve-dao-token",
    "BAL": "balancer",
    "LDO": "lido-dao",
    "ENS": "ethereum-name-service",
    "1INCH": "1inch",
    "YFI": "yearn-finance",
    "CVX": "convex-finance",
    "GNO": "gnosis",
    "BNT": "bancor",
    "BAT": "basic-attention-token",
    "REN": "ren",
    "ZRX": "0x",
    "MANA": "decentraland",
    "SAND": "the-sandbox",
    "GRT": "the-graph",
    "OP": "optimism",
    "ARB": "arbitrum",

    # Liquid staking / restaking derivatives
    "swETH": "swell-ethereum",
    "ETHfi": "ethfi",              # if listed
    "pxETH": "pendle-eth",         # Pendle pxETH
    "ETHx": "stader-ethx",
    "rsETH": "kelp-dao-restaked-eth",
    "weETH": "wrapped-eeth",
    "pufETH": "puffer-finance-eth",

    # Stablecoin variants
    "FRAX": "frax",
    "sFRAX": "staked-frax-ether",
    "crvUSD": "crvusd",
    "GHO": "gho",                  # Aave native stablecoin
    "MIM": "magic-internet-money",
    "alUSD": "alchemix-usd",
    "DOLA": "dola-usd",
    "EURS": "stasis-eurs",
    "jEUR": "jarvis-euro",
    "agEUR": "ageur",
    "PYUSD": "paypal-usd",
    "USDX": "usd-x",               # placeholder; verify if appears

    # Misc DeFi assets
    "wstUSDC": "usd-coin",
    "rUSDC": "usd-coin",
    "wUSDM": "mountain-protocol-usdm",
    "AETHUSDC": "usd-coin",
}


def get_prices(token_ids):
    """Fetch current USD prices from CoinGecko by ID."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    ids = ",".join(token_ids)
    r = requests.get(url, params={"ids": ids, "vs_currencies": "usd"})
    r.raise_for_status()
    return r.json()

def main():
    # 2. Load your CSV
    csv_path = "aave_v3_ethereum_reserves_2025-10-28.csv"
    df = pd.read_csv(csv_path)

    # 3. Fetch prices for all CoinGecko IDs we have
    prices = get_prices(list(set(COINGECKO_IDS.values())))

    # 4. Map each symbol to its price
    df["coingecko_id"] = df["underlying_symbol"].map(COINGECKO_IDS)
    df["price_usd"] = df["coingecko_id"].map(lambda x: prices.get(x, {}).get("usd", 0.0))

    # 5. Compute per-token and total TVL
    df["tvl_usd"] = (df["aToken_supply"] -  df["variableDebt_supply"]) * df["price_usd"]
    total_tvl = df["tvl_usd"].sum()

    print(f"\n📊 Aave V3 Polygon TVL Summary ({datetime.utcnow().strftime('%Y-%m-%d')}):\n")
    print(df[["underlying_symbol", "aToken_supply", "price_usd", "tvl_usd"]]
          .sort_values("tvl_usd", ascending=False)
          .to_string(index=False))
    print(f"\n💰 Total TVL (USD): ${total_tvl:,.2f}")

    # 6. Save enriched CSV
    out_path = csv_path.replace(".csv", "_with_prices.csv")
    df.to_csv(out_path, index=False)
    print(f"✅ Wrote enriched file → {out_path}")

if __name__ == "__main__":
    main()
