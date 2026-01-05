# tvl/adapters/fluid.py

from typing import List, Dict, Any
from web3 import Web3
from tvl.config import FLUID_LENDING_RESOLVER_ABI, FLUID_FTOKEN_ABI, ERC20_ABI

# Assumed: you'll add these to tvl/config.py (or wherever you keep ABIs)
#   - FLUID_LENDING_RESOLVER_ABI: ABI for the Fluid SmartLending resolver
#   - ERC20_ABI: standard ERC20 ABI (for decimals / symbol if needed)


def _get_web3(rpc_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to RPC at {rpc_url}")
    return w3


def get_fluid_lending_tvl_raw(rpc_url: str, registry: str) -> List[Dict[str, Any]]:
    """
    Low-level TVL fetcher for Fluid Lending.

    Parameters
    ----------
    rpc_url : str
        JSON-RPC URL for the chain (Ethereum / Arbitrum / Plasma).
    registry : str
        Address of the Fluid SmartLending resolver (or analogous registry)
        for the given chain. You will fill this per-CSU in your YAML.

    Returns
    -------
    List[Dict[str, Any]]
        One dict per fToken/market with decoded on-chain data:

            {
                "market": <fToken address>,
                "market_symbol": str,
                "market_decimals": int,
                "underlying": <underlying ERC20 address>,
                "underlying_symbol": Optional[str],
                "underlying_decimals": Optional[int],
                "total_assets": int,   # vault TVL in underlying units
                "total_supply": int,   # fToken supply
            }
    """
    if FLUID_LENDING_RESOLVER_ABI is None:
        raise RuntimeError("FLUID_LENDING_RESOLVER_ABI not found; define it in tvl.config")

    w3 = _get_web3(rpc_url)
    resolver_addr = Web3.to_checksum_address(registry)
    resolver = w3.eth.contract(address=resolver_addr, abi=FLUID_LENDING_RESOLVER_ABI)

    # === STEP 1: Get list of all fTokens =====================
    try:
        ftoken_addrs: List[str] = resolver.functions.getAllFTokens().call()
    except Exception as e:
        raise RuntimeError(
            f"Failed to call getAllFTokens() on resolver {resolver_addr}. Error: {e}"
        ) from e

    rows: List[Dict[str, Any]] = []
    for addr in ftoken_addrs:
        ftoken_addr = Web3.to_checksum_address(addr)
        ftoken = w3.eth.contract(address=ftoken_addr, abi=FLUID_FTOKEN_ABI)

        symbol = ftoken.functions.symbol().call()
        fdec = ftoken.functions.decimals().call()

        underlying_addr = ftoken.functions.asset().call()
        underlying_addr = Web3.to_checksum_address(underlying_addr)
        underlying = w3.eth.contract(address=underlying_addr, abi=ERC20_ABI)

        try:
            udec = underlying.functions.decimals().call()
        except:
            udec = None

        try:
            usym = underlying.functions.symbol().call()
        except:
            usym = None

        total_assets = ftoken.functions.totalAssets().call()
        total_supply = ftoken.functions.totalSupply().call()

        rows.append({
            "market": ftoken_addr,
            "market_symbol": symbol,
            "market_decimals": fdec,
            "underlying": underlying_addr,
            "underlying_symbol": usym,
            "underlying_decimals": udec,
            "total_assets": total_assets,
            "total_supply": total_supply,
        })

    return rows