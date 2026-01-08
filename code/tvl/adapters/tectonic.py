"""Tectonic (Cronos) TVL helpers.

Tectonic is a Compound-v2-style money market on Cronos (EVM).

You are modeling CSU = protocol × chain × version.
If you treat each pool as its own CSU, use version ∈ {main, veno, defi}.

This module focuses on *TVL primitives*:
- Discover markets via comptroller-like contract (pool socket / unitroller) or core.
- Read per-market supply/borrows using Compound-v2 math.

Liquidations are handled elsewhere (scan each market for LiquidateBorrow-like events).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Canonical addresses (Cronos)
# -----------------------------

# Shared core address (as provided)
TECTONIC_CORE = "0x7De56Bd8b37827c51835e162c867848fE2403a48"

# Pool sockets (likely Unitroller proxies per pool)
TECTONIC_SOCKET_MAIN = "0xb3831584acb95ed9ccb0c11f677b5ad01deaEc0"
TECTONIC_SOCKET_VENO = "0x7E0067CEf1e7558daFbaB3B1F8F6Fa75Ff64725f"
TECTONIC_SOCKET_DEFI = "0x8312A8d5d1deC499D00eb28e1a2723b13aA53C1e"


@dataclass(frozen=True)
class TectonicPoolConfig:
    pool: str  # main | veno | defi
    chain: str = "cronos"
    protocol: str = "tectonic"
    core: str = TECTONIC_CORE
    socket: str = ""
    markets: Optional[List[str]] = None  # optional explicit market list (preferred)


def default_pool_configs() -> Dict[str, TectonicPoolConfig]:
    return {
        "main": TectonicPoolConfig(pool="main", socket=TECTONIC_SOCKET_MAIN),
        "veno": TectonicPoolConfig(pool="veno", socket=TECTONIC_SOCKET_VENO),
        "defi": TectonicPoolConfig(pool="defi", socket=TECTONIC_SOCKET_DEFI),
    }


def _to_checksum(w3, addr: str) -> str:
    """Convert an address to checksum format if possible."""
    try:
        return w3.to_checksum_address(addr)
    except Exception:
        return addr


# -----------------------------
# Minimal Comptroller/TectonicCore ABI
# -----------------------------

# Your full ABI includes getAllMarkets() and oracle(). We only need those.
COMPTROLLER_ABI = [
    {
        "type": "function",
        "name": "getAllMarkets",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address[]"}],
    },
    {
        "type": "function",
        "name": "oracle",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
    },
]


def discover_markets(w3, comptroller_address: str) -> List[str]:
    """Return all market (tToken) addresses registered in the comptroller-like contract.

    You should call this on the *pool socket* address (main/veno/defi) when treating pools as CSUs.
    Calling it on TECTONIC_CORE may return a global list depending on deployment.
    """

    c = w3.eth.contract(address=_to_checksum(w3, comptroller_address), abi=COMPTROLLER_ABI)
    markets = c.functions.getAllMarkets().call()
    return [_to_checksum(w3, a) for a in markets]


def get_oracle_address(w3, comptroller_address: str) -> str:
    c = w3.eth.contract(address=_to_checksum(w3, comptroller_address), abi=COMPTROLLER_ABI)
    return _to_checksum(w3, c.functions.oracle().call())


# -----------------------------
# Minimal Compound-v2 market ABI
# -----------------------------

CTOKEN_MARKET_ABI = [
    {
        "type": "function",
        "name": "totalSupply",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "totalBorrows",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "totalReserves",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "getCash",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "exchangeRateStored",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # ERC20 markets implement underlying(); native CRO market will revert.
    {
        "type": "function",
        "name": "underlying",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
    },
    {
        "type": "function",
        "name": "decimals",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
]

ERC20_DECIMALS_ABI = [
    {
        "type": "function",
        "name": "decimals",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    }
]


# -----------------------------
# TVL math helpers (Compound-v2 style)
# -----------------------------

NATIVE_ADDR = "0x0000000000000000000000000000000000000000"


def read_market_state(w3, market_address: str) -> Dict[str, int]:
    """Read raw market state from a tToken (Compound-v2-style market)."""

    m = w3.eth.contract(address=_to_checksum(w3, market_address), abi=CTOKEN_MARKET_ABI)

    state: Dict[str, int] = {}
    state["totalSupply"] = int(m.functions.totalSupply().call())
    state["totalBorrows"] = int(m.functions.totalBorrows().call())
    state["totalReserves"] = int(m.functions.totalReserves().call())
    state["cash"] = int(m.functions.getCash().call())
    state["exchangeRateStored"] = int(m.functions.exchangeRateStored().call())

    try:
        state["marketDecimals"] = int(m.functions.decimals().call())
    except Exception:
        state["marketDecimals"] = 8  # common default in Compound v2

    try:
        state["underlying"] = _to_checksum(w3, m.functions.underlying().call())
        state["isNative"] = 0
    except Exception:
        state["underlying"] = NATIVE_ADDR
        state["isNative"] = 1

    return state


def read_underlying_decimals(w3, underlying_address: str) -> int:
    """Read ERC20 decimals, defaulting to 18 if unknown."""

    if underlying_address.lower() == NATIVE_ADDR:
        return 18
    erc20 = w3.eth.contract(address=_to_checksum(w3, underlying_address), abi=ERC20_DECIMALS_ABI)
    try:
        return int(erc20.functions.decimals().call())
    except Exception:
        return 18


def compute_totals_underlying(
    state: Dict[str, int],
    underlying_decimals: int
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Compute (tvl, borrows, reserves) in underlying *token units*.

    IMPORTANT:
    For Tectonic (and some Compound-v2 forks), exchangeRateStored scaling
    is unreliable for TVL reconstruction. We therefore compute TVL using
    the accounting identity:

        TVL = cash + totalBorrows - totalReserves

    All values are returned in underlying token units (not base units).
    """

    scale = Decimal(10) ** Decimal(underlying_decimals)

    cash_underlying = Decimal(state["cash"]) / scale
    borrows_underlying = Decimal(state["totalBorrows"]) / scale
    reserves_underlying = Decimal(state["totalReserves"]) / scale

    tvl_underlying = cash_underlying + borrows_underlying - reserves_underlying

    return tvl_underlying, borrows_underlying, reserves_underlying


def make_pool_config(pool: str, markets: Optional[List[str]] = None) -> TectonicPoolConfig:
    cfgs = default_pool_configs()
    if pool not in cfgs:
        raise ValueError(f"Unknown pool: {pool}. Expected one of {list(cfgs.keys())}")
    base = cfgs[pool]
    if markets is None:
        return base
    return TectonicPoolConfig(pool=base.pool, socket=base.socket, markets=markets)
