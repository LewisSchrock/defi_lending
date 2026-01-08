from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from web3 import Web3


# -------- Minimal ABIs --------

UNITROLLER_ABI_MIN = [
    {
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

CTOKEN_ABI_MIN = [
    {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalSupply", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "exchangeRateStored", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalBorrows", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalReserves", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getCash", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "underlying", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
]

ERC20_ABI_MIN = [
    {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
]


# -------- Core helpers --------

def discover_markets(w3: Web3, unitroller: str) -> List[str]:
    comp = w3.eth.contract(address=Web3.to_checksum_address(unitroller), abi=UNITROLLER_ABI_MIN)
    markets = comp.functions.getAllMarkets().call()
    return [Web3.to_checksum_address(m) for m in markets]


def _safe_call(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def read_market_state(w3: Web3, market: str) -> Dict:
    c = w3.eth.contract(address=Web3.to_checksum_address(market), abi=CTOKEN_ABI_MIN)

    market_decimals = int(c.functions.decimals().call())
    total_supply = int(c.functions.totalSupply().call())
    exchange_rate = int(c.functions.exchangeRateStored().call())
    total_borrows = int(c.functions.totalBorrows().call())
    total_reserves = int(c.functions.totalReserves().call())
    cash = _safe_call(lambda: int(c.functions.getCash().call()), default=None)

    # underlying() will revert for the native market (CEther-style)
    underlying = _safe_call(lambda: Web3.to_checksum_address(c.functions.underlying().call()), default=None)
    is_native = underlying is None

    sym = _safe_call(lambda: c.functions.symbol().call(), default=None)

    return {
        "market": Web3.to_checksum_address(market),
        "marketDecimals": market_decimals,
        "totalSupply": total_supply,
        "exchangeRateStored": exchange_rate,
        "totalBorrows": total_borrows,
        "totalReserves": total_reserves,
        "cash": cash,
        "underlying": underlying,   # None if native
        "isNative": is_native,
        "marketSymbol": sym,
    }


def read_underlying_decimals(w3: Web3, underlying: Optional[str], is_native: bool) -> int:
    if is_native:
        # Flare native token (FLR) behaves like ETH in Compound v2
        return 18
    t = w3.eth.contract(address=Web3.to_checksum_address(underlying), abi=ERC20_ABI_MIN)
    return int(t.functions.decimals().call())


def compute_totals_underlying(state: Dict, underlying_decimals: int) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Compute (supply, borrows, reserves) in underlying token units (NOT raw base units).

    Many Compound-v2 forks follow the canonical scaling:
        exchangeRateStored scaled by 1e(18 + underlyingDecimals - cTokenDecimals)

    However some forks (including some on smaller chains) deviate.

    To be robust, when `cash` is available we infer the correct scale by matching the
    accounting identity (in underlying base units):
        totalUnderlyingBase = getCash + totalBorrows - totalReserves

    Then we choose the candidate scale that makes:
        totalSupply * exchangeRateStored / scale  ~= totalUnderlyingBase

    Finally we convert base units -> token units by dividing by 10^underlyingDecimals.
    """

    total_supply = Decimal(state["totalSupply"])          # cToken base units
    exchange_rate = Decimal(state["exchangeRateStored"])  # scaled exchange rate
    market_decimals = int(state["marketDecimals"])

    # Raw (base-unit) quantities for the underlying token
    borrows_base = Decimal(state["totalBorrows"])
    reserves_base = Decimal(state["totalReserves"])
    cash_base = Decimal(state["cash"]) if state.get("cash") is not None else None

    # Borrow/reserve token-units are always just base / 10^underlyingDecimals
    borrows_underlying = borrows_base / (Decimal(10) ** Decimal(underlying_decimals))
    reserves_underlying = reserves_base / (Decimal(10) ** Decimal(underlying_decimals))

    # Candidate exchange-rate scales we may see in the wild.
    # 1) Canonical Compound v2
    # 2) exchangeRate scaled by 1e(18 + underlyingDecimals)
    # 3) exchangeRate scaled by 1e18 (rare, but appears in some forks)
    candidates = [
        Decimal(10) ** Decimal(18 + underlying_decimals - market_decimals),
        Decimal(10) ** Decimal(18 + underlying_decimals),
        Decimal(10) ** Decimal(18),
    ]

    # Default to canonical
    chosen_scale = candidates[0]

    if cash_base is not None:
        total_underlying_base = cash_base + borrows_base - reserves_base
        if total_underlying_base > 0:
            # Pick the scale that best matches the accounting identity
            best_err = None
            for s in candidates:
                supply_base = (total_supply * exchange_rate) / s
                err = abs(supply_base - total_underlying_base) / total_underlying_base
                if best_err is None or err < best_err:
                    best_err = err
                    chosen_scale = s

    supply_base = (total_supply * exchange_rate) / chosen_scale
    supply_underlying = supply_base / (Decimal(10) ** Decimal(underlying_decimals))

    return supply_underlying, borrows_underlying, reserves_underlying


class KineticTVLAdapter:
    def __init__(self, rpc_url: str, unitroller: str, chain: str = "flare"):
        self.rpc_url = rpc_url
        self.unitroller = unitroller
        self.chain = chain

    def fetch(self, max_markets: Optional[int] = None, sleep_s: float = 0.15) -> List[Dict]:
        return get_kinetic_tvl_raw(
            rpc_url=self.rpc_url,
            unitroller=self.unitroller,
            chain=self.chain,
            max_markets=max_markets,
            sleep_s=sleep_s,
        )


def get_kinetic_tvl_raw(
    rpc_url: str,
    unitroller: str,
    chain: str = "flare",
    max_markets: Optional[int] = None,
    sleep_s: float = 0.15,
) -> List[Dict]:
    """
    Returns per-market rows in the same shape you’ve been using for Tectonic:
    includes market, underlying, decimals, supply/borrows/reserves in underlying units.
    """
    import time

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))

    markets = discover_markets(w3, unitroller)
    if max_markets is not None:
        markets = markets[:max_markets]

    rows: List[Dict] = []

    for m in markets:
        if sleep_s > 0:
            time.sleep(sleep_s)

        st = read_market_state(w3, m)
        udec = read_underlying_decimals(w3, st["underlying"], st["isNative"])
        supply_u, borrows_u, reserves_u = compute_totals_underlying(st, udec)

        rows.append(
            {
                "protocol": "kinetic",
                "chain": chain,
                "market": st["market"],
                "market_symbol": st.get("marketSymbol"),
                "underlying": st["underlying"],  # None if native
                "underlying_decimals": udec,
                "is_native": bool(st["isNative"]),
                "supply_underlying": str(supply_u),
                "borrows_underlying": str(borrows_u),
                "reserves_underlying": str(reserves_u),
            }
        )

    return rows