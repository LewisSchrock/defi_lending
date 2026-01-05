# tvl/adapters/venus.py

from typing import List, Dict, Any
from web3 import Web3

# Minimal ABI for Venus Comptroller / Unitroller: we only need getAllMarkets()
VENUS_COMPTROLLER_ABI = [
    {
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [
            {
                "internalType": "address[]",
                "name": "",
                "type": "address[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# Minimal ABI for Venus vTokens (Compound-style)
VENUS_VTOKEN_ABI = [
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
    # underlying() – may revert for native BNB markets
    {
        "constant": True,
        "inputs": [],
        "name": "underlying",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Super-minimal ERC-20 ABI for underlying token metadata
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


def _safe(fn, default=None):
    """Call fn(), return default on any exception."""
    try:
        return fn()
    except Exception:
        return default


def get_venus_core_tvl_raw(rpc_url: str, registry: str) -> List[Dict[str, Any]]:
    """
    Raw Venus Core Pool TVL.

    Parameters
    ----------
    rpc_url : str
        BNB Chain RPC endpoint.
    registry : str
        Address of the Venus Unitroller/Comptroller for the *core pool*
        (this comes from your csu_config.yaml as `registry`).

    Returns
    -------
    List[Dict[str, Any]]
        One dict per vToken, with balances and a TVL estimate in underlying units:
        tvl_underlying = getCash + totalBorrows - totalReserves
    """
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    comptroller_addr = Web3.to_checksum_address(registry)
    comptroller = w3.eth.contract(
        address=comptroller_addr,
        abi=VENUS_COMPTROLLER_ABI,
    )

    # Discover all vTokens for the core pool
    vtoken_addrs = _safe(lambda: comptroller.functions.getAllMarkets().call(), []) or []

    rows: List[Dict[str, Any]] = []

    for addr in vtoken_addrs:
        vaddr = Web3.to_checksum_address(addr)
        v = w3.eth.contract(address=vaddr, abi=VENUS_VTOKEN_ABI)

        v_symbol = _safe(lambda: v.functions.symbol().call(), None)
        v_decimals = _safe(lambda: v.functions.decimals().call(), 8)

        get_cash = _safe(lambda: v.functions.getCash().call(), 0) or 0
        total_borrows = _safe(lambda: v.functions.totalBorrows().call(), 0) or 0
        total_reserves = _safe(lambda: v.functions.totalReserves().call(), 0) or 0
        total_supply = _safe(lambda: v.functions.totalSupply().call(), 0) or 0

        # Underlying metadata – some Venus markets are native BNB, so underlying() may revert.
        underlying_addr = _safe(lambda: v.functions.underlying().call(), None)
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
                "market": vaddr,
                "market_symbol": v_symbol,
                "market_decimals": int(v_decimals),
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