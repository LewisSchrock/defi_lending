from web3 import Web3
import csv
from datetime import datetime

# ---------- ABIs ----------
IPoolAddressesProvider_ABI = [
    {"inputs": [], "name": "getPoolDataProvider", "outputs": [{"internalType": "address", "name": "", "type": "address"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getPool", "outputs": [{"internalType": "address", "name": "", "type": "address"}],
     "stateMutability": "view", "type": "function"}
]

IAaveProtocolDataProvider_ABI = [
    {"inputs": [], "name": "getAllReservesTokens", "outputs": [
        {"components": [
            {"internalType": "string", "name": "symbol", "type": "string"},
            {"internalType": "address", "name": "tokenAddress", "type": "address"}],
         "internalType": "struct AaveProtocolDataProvider.TokenData[]", "name": "", "type": "tuple[]"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
     "name": "getReserveTokensAddresses",
     "outputs": [
         {"internalType": "address", "name": "aTokenAddress", "type": "address"},
         {"internalType": "address", "name": "stableDebtTokenAddress", "type": "address"},
         {"internalType": "address", "name": "variableDebtTokenAddress", "type": "address"}],
     "stateMutability": "view", "type": "function"}
]

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}],
     "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

# ---------- Core Functions ----------

def connect_rpc(rpc_url):
    """Initialize web3 connection."""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    assert w3.is_connected(), "RPC connection failed"
    return w3


def get_data_provider(w3, provider_addr):
    """Get Pool and DataProvider addresses from PoolAddressesProvider."""
    provider = w3.eth.contract(address=Web3.to_checksum_address(provider_addr), abi=IPoolAddressesProvider_ABI)

    # Some chains (Polygon) don't expose getPool(); handle gracefully
    try:
        pool = provider.functions.getPool().call()
    except Exception:
        pool = None  # not critical for TVL export

    data_provider = provider.functions.getPoolDataProvider().call()
    return pool, Web3.to_checksum_address(data_provider)


def get_reserves(w3, data_provider_addr):
    """Get all reserves and their corresponding token addresses."""
    dp = w3.eth.contract(address=data_provider_addr, abi=IAaveProtocolDataProvider_ABI)
    reserves = dp.functions.getAllReservesTokens().call()
    data = []
    for sym, underlying in reserves:
        aToken, sDebt, vDebt = dp.functions.getReserveTokensAddresses(underlying).call()
        data.append({
            "underlying_symbol": sym,
            "underlying": Web3.to_checksum_address(underlying),
            "aToken": Web3.to_checksum_address(aToken),
            "stableDebt": Web3.to_checksum_address(sDebt),
            "variableDebt": Web3.to_checksum_address(vDebt)
        })
    return data


def get_total_supply(w3, token_addr):
    """Return normalized total supply (float) and decimals, or (0, None) if not ERC20."""
    token_addr = Web3.to_checksum_address(token_addr)
    code = w3.eth.get_code(token_addr)
    if len(code) < 100:  # no bytecode or too small to be ERC20
        return 0.0, None

    c = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
    try:
        decimals = c.functions.decimals().call()
        raw_supply = c.functions.totalSupply().call()
        return raw_supply / (10 ** decimals), decimals
    except Exception:
        return 0.0, None



def export_aave_v3_reserves(rpc, provider, chain="chain", out_file=None):
    """Main function: connects, enumerates reserves, and exports CSV."""
    w3 = connect_rpc(rpc)
    pool_addr, data_provider_addr = get_data_provider(w3, provider)
    reserves = get_reserves(w3, data_provider_addr)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_file = out_file or f"aave_v3_{chain}_reserves_{today}.csv"

    header = [
        "date", "chain", "underlying_symbol", "underlying_address",
        "aToken_address", "aToken_supply", "stableDebt_address",
        "stableDebt_supply", "variableDebt_address", "variableDebt_supply"
    ]

    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for r in reserves:
            try:
                a_supply, _ = get_total_supply(w3, r["aToken"])
                s_supply, _ = get_total_supply(w3, r["stableDebt"])
                v_supply, _ = get_total_supply(w3, r["variableDebt"])
                writer.writerow([
                    today, chain,
                    r["underlying_symbol"], r["underlying"],
                    r["aToken"], f"{a_supply:.6f}",
                    r["stableDebt"], f"{s_supply:.6f}",
                    r["variableDebt"], f"{v_supply:.6f}"
                ])
            except Exception as e:
                print(f"⚠️ Error reading {r['underlying_symbol']}: {e}")

    print(f"✅ Exported {len(reserves)} reserves → {out_file}")
    print(f"Pool: {pool_addr}\nData Provider: {data_provider_addr}")


# ---------- Example Main ----------

def main():


    # rpc = "https://polygon-mainnet.g.alchemy.com/v2/cEHzRdgL5rGydq_YIokK2"
    # provider_addr = Web3.to_checksum_address("0xA97684ead0E402dC232d5A977953DF7ECBaB3CDb")
    # w3 = Web3(Web3.HTTPProvider(rpc))

    # abi = [{
    #     "inputs": [],
    #     "name": "getPoolDataProvider",
    #     "outputs": [{"internalType": "address", "name": "", "type": "address"}],
    #     "stateMutability": "view",
    #     "type": "function"
    # }]

    # contract = w3.eth.contract(address=provider_addr, abi=abi)
    # print(contract.functions.getPoolDataProvider().call())


    rpc = "https://eth-mainnet.g.alchemy.com/v2/cEHzRdgL5rGydq_YIokK2"
    provider = "0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e"  # Aave V3 Polygon Provider
    chain = "ethereum"
    export_aave_v3_reserves(rpc, provider, chain)


if __name__ == "__main__":
    main()
