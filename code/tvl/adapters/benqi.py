from typing import List, Dict, Any

from web3 import Web3, HTTPProvider
from web3.contract import Contract

from tvl.config import COMPTROLLER_ABI, CTOKEN_ABI

# Benqi Comptroller on Avalanche C-Chain
BENQI_COMPTROLLER = "0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4"

# Wrapped AVAX token (used as underlying for qiAVAX-style market)
WAVAX_ADDRESS = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7"


def _get_comptroller(web3: Web3, comptroller_address: str) -> Contract:
    return web3.eth.contract(
        address=web3.to_checksum_address(comptroller_address),
        abi=COMPTROLLER_ABI,
    )


def _get_ctoken(web3: Web3, ctoken_address: str) -> Contract:
    return web3.eth.contract(
        address=web3.to_checksum_address(ctoken_address),
        abi=CTOKEN_ABI,
    )


def _get_markets(web3: Web3, comptroller_address: str) -> List[str]:
    """
    Return the list of all Benqi cToken market addresses via Comptroller.getAllMarkets().
    """
    comptroller = _get_comptroller(web3, comptroller_address)
    markets = comptroller.functions.getAllMarkets().call()
    return [web3.to_checksum_address(m) for m in markets]


def get_benqi_lending_tvl_raw(
    rpc_url: str,
    comptroller: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetch raw TVL-related state for all Benqi lending markets.

    Returns a list of dicts, one per cToken, with:
      - ctoken
      - symbol
      - underlying
      - cash
      - total_borrows
      - total_reserves
      - exchange_rate_stored
      - ctoken_decimals
      - underlying_decimals (if we can fetch; None if not)
    """
    web3 = Web3(HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise RuntimeError(f"Failed to connect to RPC at {rpc_url}")

    comptroller_address = comptroller or BENQI_COMPTROLLER
    markets = _get_markets(web3, comptroller_address)

    rows: List[Dict[str, Any]] = []

    for caddr in markets:
        ctoken = _get_ctoken(web3, caddr)

        # Basic metadata
        try:
            symbol = ctoken.functions.symbol().call()
        except Exception:
            symbol = None

        try:
            ctoken_decimals = ctoken.functions.decimals().call()
        except Exception:
            ctoken_decimals = None

        # Underlying:
        # - For most cTokens, underlying() exists and returns an ERC20 address.
        # - For qiAVAX (the native AVAX market), underlying() usually reverts:
        #   in that case we treat the underlying as WAVAX.
        underlying_address: str | None
        underlying_decimals: int | None

        try:
            underlying_address = ctoken.functions.underlying().call()
            underlying_address = web3.to_checksum_address(underlying_address)
        except Exception:
            # Native AVAX market (qiAVAX-like) – use WAVAX as canonical underlying.
            underlying_address = web3.to_checksum_address(WAVAX_ADDRESS)

        # Try to fetch underlying decimals via a minimal ERC20 call.
        # If it fails (should be rare), we just set None.
        underlying_decimals = None
        try:
            erc20 = web3.eth.contract(
                address=underlying_address,
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
            underlying_decimals = None

        # Core state for TVL
        try:
            cash = ctoken.functions.getCash().call()
        except Exception:
            cash = None

        try:
            total_borrows = ctoken.functions.totalBorrows().call()
        except Exception:
            total_borrows = None

        try:
            total_reserves = ctoken.functions.totalReserves().call()
        except Exception:
            total_reserves = None

        try:
            exchange_rate_stored = ctoken.functions.exchangeRateStored().call()
        except Exception:
            exchange_rate_stored = None

        rows.append(
            {
                "ctoken": caddr,
                "symbol": symbol,
                "ctoken_decimals": ctoken_decimals,
                "underlying": underlying_address,
                "underlying_decimals": underlying_decimals,
                "cash": cash,
                "total_borrows": total_borrows,
                "total_reserves": total_reserves,
                "exchange_rate_stored": exchange_rate_stored,
            }
        )

    return rows