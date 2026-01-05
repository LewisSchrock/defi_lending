# tvl/adapters/moonwell.py

from typing import List, Dict, Any
from web3 import Web3, HTTPProvider
from web3.contract import Contract

from tvl.config import COMPTROLLER_ABI, CTOKEN_ABI

# Moonwell Comptroller on Base
MOONWELL_COMPTROLLER = "0xfBb21d0380beE3312B33c4353c8936a0F13EF26C"


def _get_comptroller(web3: Web3, addr: str) -> Contract:
    return web3.eth.contract(
        address=web3.to_checksum_address(addr),
        abi=COMPTROLLER_ABI,
    )


def _get_ctoken(web3: Web3, addr: str) -> Contract:
    return web3.eth.contract(
        address=web3.to_checksum_address(addr),
        abi=CTOKEN_ABI,
    )


def _get_markets(web3: Web3, comptroller_addr: str) -> List[str]:
    comptroller = _get_comptroller(web3, comptroller_addr)
    markets = comptroller.functions.getAllMarkets().call()
    return [web3.to_checksum_address(m) for m in markets]


def get_moonwell_lending_tvl_raw(
    rpc_url: str,
    comptroller: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Pull Moonwell lending TVL state from Base.
    Returns list of dicts for each mToken market.
    """
    web3 = Web3(HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise RuntimeError(f"Failed to connect to RPC at {rpc_url}")

    comptroller_addr = comptroller or MOONWELL_COMPTROLLER
    markets = _get_markets(web3, comptroller_addr)

    rows: List[Dict[str, Any]] = []

    for maddr in markets:
        mtoken = _get_ctoken(web3, maddr)

        try:
            symbol = mtoken.functions.symbol().call()
        except Exception:
            symbol = None

        try:
            mtoken_decimals = mtoken.functions.decimals().call()
        except Exception:
            mtoken_decimals = None

        # Underlying may revert for native markets; in Moonwell all are ERC20-style,
        # but we still wrap in try/except for safety.
        underlying = None
        underlying_decimals = None
        try:
            underlying = mtoken.functions.underlying().call()
            underlying = web3.to_checksum_address(underlying)

            erc20 = web3.eth.contract(
                address=underlying,
                abi=[
                    {
                        "constant": True,
                        "inputs": [],
                        "name": "decimals",
                        "outputs": [{"name": "", "type": "uint8"}],
                        "payable": False,
                        "stateMutability": "view",
                        "type": "function",
                    }
                ],
            )
            underlying_decimals = erc20.functions.decimals().call()
        except Exception:
            # leave underlying / underlying_decimals as None if this fails
            pass

        try:
            cash = mtoken.functions.getCash().call()
        except Exception:
            cash = None

        try:
            total_borrows = mtoken.functions.totalBorrows().call()
        except Exception:
            total_borrows = None

        try:
            total_reserves = mtoken.functions.totalReserves().call()
        except Exception:
            total_reserves = None

        try:
            exchange_rate_stored = mtoken.functions.exchangeRateStored().call()
        except Exception:
            exchange_rate_stored = None

        rows.append(
            {
                "ctoken": maddr,
                "symbol": symbol,
                "ctoken_decimals": mtoken_decimals,
                "underlying": underlying,
                "underlying_decimals": underlying_decimals,
                "cash": cash,
                "total_borrows": total_borrows,
                "total_reserves": total_reserves,
                "exchange_rate_stored": exchange_rate_stored,
            }
        )

    return rows