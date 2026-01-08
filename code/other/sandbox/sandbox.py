#!/usr/bin/env python3

from web3 import Web3

# Adjust import path if your package name is different
from tvl.adapters.compound_adapter import (
    get_reserves,
    get_oracle_price,
    COMPOUND_ORACLE_ABI,
    MAINNET_COMPTROLLER,
)

def main():
    # TODO: put your real mainnet RPC here (Alchemy/Infura/etc.)
    rpc_url = "https://eth-mainnet.g.alchemy.com/v2/cEHzRdgL5rGydq_YIokK2"
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        raise SystemExit("Web3 is not connected. Check your RPC URL / key.")

    # Compound v2 price feed / oracle (from Compound v2 docs)
    # You can swap this if you know a newer oracle address.
    oracle_addr = Web3.to_checksum_address("0x8CF42B08AD13761345531b839487aA4d113955d9")
    oracle = w3.eth.contract(address=oracle_addr, abi=COMPOUND_ORACLE_ABI)

    # ---- 1) Fetch markets via get_reserves ----
    print("Fetching Compound v2 markets from Comptroller...")
    reserves = get_reserves(w3, MAINNET_COMPTROLLER)
    print(f"Found {len(reserves)} markets\n")

    # Show first few reserves
    for r in reserves[:10]:
        print(f"cToken: {r['symbol']}, address: {r['asset']}")

    # ---- 2) Test price lookup on a few markets ----
    print("\nTesting oracle prices for first few markets:")
    for r in reserves[:5]:
        symbol = r["symbol"]
        asset = r["asset"]
        try:
            price = get_oracle_price(w3, oracle, asset)
            print(f"{symbol:6s} ({asset}) -> price ≈ {price:.6f} USD")
        except Exception as e:
            print(f"{symbol:6s} ({asset}) -> ERROR fetching price: {e}")

if __name__ == "__main__":
    main()