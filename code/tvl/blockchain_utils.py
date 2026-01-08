from web3 import Web3
from .config import PROVIDER_ABI, ERC20_ABI

def connect_rpc(rpc_url):
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    assert w3.is_connected(), "RPC connection failed"
    return w3

def get_pool_addresses(w3, provider_addr):
    provider_addr = Web3.to_checksum_address(provider_addr)
    provider = w3.eth.contract(address=provider_addr, abi=PROVIDER_ABI)
    return {
        "pool": provider.functions.getPool().call(),
        "oracle": provider.functions.getPriceOracle().call(),
        "data_provider": provider.functions.getPoolDataProvider().call(),
    }

def get_total_supply(w3, token_addr):
    token_addr = Web3.to_checksum_address(token_addr)
    try:
        if len(w3.eth.get_code(token_addr)) < 100:
            return 0.0
        c = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        decimals = c.functions.decimals().call()
        raw = c.functions.totalSupply().call()
        return raw / (10 ** decimals)
    except Exception:
        return 0.0