from typing import List, Dict, Any
from web3 import Web3

CTOKEN_ABI = [
    # symbol()
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    # decimals()
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    # totalSupply()
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    # getCash()
    {
        "constant": True,
        "inputs": [],
        "name": "getCash",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    # totalBorrows()
    {
        "constant": True,
        "inputs": [],
        "name": "totalBorrows",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    # totalReserves()
    {
        "constant": True,
        "inputs": [],
        "name": "totalReserves",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    # underlying() – may revert on native markets
    {
        "constant": True,
        "inputs": [],
        "name": "underlying",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

ERC20_ABI_MIN = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]

CAPYFI_ETH_MARKETS: List[Dict[str, str]] = [
    {"symbol": "caUXD",  "address": "0x98Ac8AC56d833bD69d34F909Ac15226772FAc9aa"},
    {"symbol": "caETH",  "address": "0x37DE57183491Fa9745d8Fa5DCd950f0c3a4645c9"},
    {"symbol": "caLAC",  "address": "0x0568F6cb5A0E84FACa107D02f81ddEB1803f3B50"},
    {"symbol": "caWBTC", "address": "0xDa5928d59ECE82808Af2cbBE4f2872FeA8E12CD6"},
    {"symbol": "caUSDT", "address": "0x0f864A3e50D1070adDE5100fd848446C0567362B"},
    {"symbol": "caUSDC", "address": "0xc3aD34De18B59A24BD0877e454Fb924181F09C8f"},
    {"symbol": "caRPC",  "address": "0xF61159B4a0EE5b1615c9Afb3dA38111043344c32"},
    {"symbol": "caWARS", "address": "0xf80eeec09f417Fa7FCc4A848Ef03af9dF2658d7B"},
]


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def get_capyfi_tvl_raw(rpc_url: str, registry: str) -> List[Dict[str, Any]]:
    """
    Raw CapyFi TVL rows.

    TVL per market is computed as:
        tvl_underlying = getCash() + totalBorrows() - totalReserves()

    All amounts are in underlying token units (before applying price oracle).
    """
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    rows: List[Dict[str, Any]] = []

    for m in CAPYFI_ETH_MARKETS:
        caddr = Web3.to_checksum_address(m["address"])
        c = w3.eth.contract(address=caddr, abi=CTOKEN_ABI)

        c_symbol = _safe(lambda: c.functions.symbol().call(), m["symbol"])
        c_decimals = _safe(lambda: c.functions.decimals().call(), 8)

        get_cash = _safe(lambda: c.functions.getCash().call(), 0) or 0
        total_borrows = _safe(lambda: c.functions.totalBorrows().call(), 0) or 0
        total_reserves = _safe(lambda: c.functions.totalReserves().call(), 0) or 0

        # for diagnostics only
        total_supply = _safe(lambda: c.functions.totalSupply().call(), 0) or 0

        # underlying metadata (optional)
        underlying_addr = _safe(lambda: c.functions.underlying().call(), None)
        underlying_symbol = None
        underlying_decimals = None

        if isinstance(underlying_addr, str):
            u = w3.eth.contract(
                address=Web3.to_checksum_address(underlying_addr),
                abi=ERC20_ABI_MIN,
            )
            underlying_symbol = _safe(lambda: u.functions.symbol().call(), None)
            underlying_decimals = _safe(lambda: u.functions.decimals().call(), 18)

        tvl_underlying = int(get_cash) + int(total_borrows) - int(total_reserves)

        rows.append(
            {
                "market": caddr,
                "market_symbol": c_symbol,
                "market_decimals": int(c_decimals),
                "underlying": underlying_addr,
                "underlying_symbol": underlying_symbol,
                "underlying_decimals": underlying_decimals,
                "get_cash": int(get_cash),
                "total_borrows": int(total_borrows),
                "total_reserves": int(total_reserves),
                "total_supply": int(total_supply),
                "tvl_underlying": tvl_underlying,
            }
        )

    return rows