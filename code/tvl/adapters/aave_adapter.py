from web3 import Web3
from ..config import DATA_PROVIDER_ABI, POOL_ABI, ORACLE_ABI, ERC20_ABI, PROVIDER_ABI

def get_reserves(w3, provider_addr):
    """Fetch reserves from Aave V3 data provider."""
    provider_addr = Web3.to_checksum_address(provider_addr)
    provider = w3.eth.contract(address=provider_addr, abi=PROVIDER_ABI)
    pool_addr = provider.functions.getPool().call()
    data_provider_addr = provider.functions.getPoolDataProvider().call()

    pool = w3.eth.contract(address=pool_addr, abi=POOL_ABI)
    reserves = pool.functions.getReservesList().call()

    dp = w3.eth.contract(address=data_provider_addr, abi=DATA_PROVIDER_ABI)
    data = []
    for asset in reserves:
        aToken, sDebt, vDebt = dp.functions.getReserveTokensAddresses(asset).call()
        def _cs(addr: str) -> str:
            if addr is None:
                return None
            a = addr if isinstance(addr, str) else str(addr)
            if a.lower() == "0x0000000000000000000000000000000000000000":
                return a
            return Web3.to_checksum_address(a)
        
        asset_cs = _cs(asset)
        aToken_cs = _cs(aToken)
        sDebt_cs = _cs(sDebt)
        vDebt_cs = _cs(vDebt)

        token = w3.eth.contract(address=asset, abi=ERC20_ABI)
        try:
            sym = token.functions.symbol().call()
        except Exception:
            sym = "(unknown)"
        data.append({
            "symbol": sym,
            "asset": asset_cs,
            "aToken": aToken_cs,
            "stableDebt": sDebt_cs,
            "variableDebt": vDebt_cs,
        })
    return data

def get_oracle_price(w3, oracle, asset):
    return oracle.functions.getAssetPrice(asset).call() / 1e8

def get_protocol_metadata():
    return {
        "price_scale": 1e8,
        "description": "Aave V3 lending market",
        "version": "v3"
    }