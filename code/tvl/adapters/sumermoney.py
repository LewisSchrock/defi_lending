

"""Sumer Money TVL adapter.

Sumer (Sumer.Money) is Compound-like: a Comptroller lists cToken markets.
For each cToken, we compute a simple on-chain TVL proxy in underlying units:

    total_assets_underlying = cash + totalBorrows - totalReserves

Notes:
- This is *not* a USD TVL unless you multiply by a price oracle.
- Some markets may be "native" cTokens (no `underlying()`); we handle this.
- This adapter is intentionally minimal and consistent with the rest of your pipeline:
  it exposes `iter_reserve_tvl()` and `get_tvl_rows()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional

from web3 import Web3


# --- Minimal ABIs (only what we call) ----------------------------------------

_COMPTROLLER_ABI = [
    {
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

_CTOKEN_ABI = [
    {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "name", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "underlying", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getCash", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalBorrows", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalReserves", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]

_ERC20_ABI = [
    {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "name", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
]


def _to_decimal(raw: int, decimals: int) -> float:
    # Avoid importing Decimal everywhere; float is fine for quick sanity.
    return raw / (10 ** decimals) if decimals >= 0 else float(raw)


def _safe_call(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


@dataclass(frozen=True)
class MarketInfo:
    ctoken: str
    ctoken_symbol: str
    ctoken_decimals: int
    underlying: Optional[str]
    underlying_symbol: Optional[str]
    underlying_decimals: Optional[int]


class SumerTVLAdapter:
    """Compute per-market TVL-like balances from Sumer/Compound-style markets."""

    def __init__(
        self,
        web3: Web3,
        chain: str,
        config: Dict,
        outputs_dir: str,
    ):
        self.w3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir

        comptroller = (config or {}).get("comptroller")
        if not comptroller:
            raise ValueError("Missing `comptroller` in CSU config for SumerTVLAdapter")
        if not Web3.is_address(comptroller):
            raise ValueError(f"Invalid comptroller address: {comptroller}")

        self.comptroller_addr = Web3.to_checksum_address(comptroller)
        self.comptroller = self.w3.eth.contract(address=self.comptroller_addr, abi=_COMPTROLLER_ABI)

    # ---- Market discovery -------------------------------------------------

    def get_markets(self) -> List[str]:
        markets = self.comptroller.functions.getAllMarkets().call()
        # Normalize / checksum
        out: List[str] = []
        for m in markets:
            if Web3.is_address(m):
                out.append(Web3.to_checksum_address(m))
        return out

    def _load_market_info(self, ctoken_addr: str) -> MarketInfo:
        c = self.w3.eth.contract(address=ctoken_addr, abi=_CTOKEN_ABI)

        ctoken_symbol = _safe_call(c.functions.symbol().call, default="") or ""
        ctoken_decimals = int(_safe_call(c.functions.decimals().call, default=8) or 8)

        # Some cTokens (native) may revert on `underlying()`
        underlying = _safe_call(c.functions.underlying().call, default=None)
        if underlying and Web3.is_address(underlying):
            underlying = Web3.to_checksum_address(underlying)
            u = self.w3.eth.contract(address=underlying, abi=_ERC20_ABI)
            u_symbol = _safe_call(u.functions.symbol().call, default=None)
            u_decimals = _safe_call(u.functions.decimals().call, default=None)
            return MarketInfo(
                ctoken=ctoken_addr,
                ctoken_symbol=ctoken_symbol,
                ctoken_decimals=ctoken_decimals,
                underlying=underlying,
                underlying_symbol=u_symbol,
                underlying_decimals=int(u_decimals) if u_decimals is not None else None,
            )

        return MarketInfo(
            ctoken=ctoken_addr,
            ctoken_symbol=ctoken_symbol,
            ctoken_decimals=ctoken_decimals,
            underlying=None,
            underlying_symbol=None,
            underlying_decimals=None,
        )

    # ---- TVL computation --------------------------------------------------

    def iter_reserve_tvl(self, market: Optional[Dict] = None) -> Iterator[Dict]:
        """Yield per-market rows.

        `market` is accepted for interface consistency with other adapters.
        This adapter uses `self.config["comptroller"]` and ignores `market`.
        """

        for ctoken in self.get_markets():
            c = self.w3.eth.contract(address=ctoken, abi=_CTOKEN_ABI)
            info = self._load_market_info(ctoken)

            cash = int(_safe_call(c.functions.getCash().call, default=0) or 0)
            borrows = int(_safe_call(c.functions.totalBorrows().call, default=0) or 0)
            reserves = int(_safe_call(c.functions.totalReserves().call, default=0) or 0)

            # TVL proxy: assets = cash + borrows - reserves
            total_assets = cash + borrows - reserves

            # Use underlying decimals if known, otherwise fall back to cToken decimals
            decimals = info.underlying_decimals if info.underlying_decimals is not None else info.ctoken_decimals

            yield {
                "chain": self.chain,
                "protocol": self.config.get("protocol", "sumermoney"),
                "comptroller": self.comptroller_addr,
                "ctoken": info.ctoken,
                "ctoken_symbol": info.ctoken_symbol,
                "underlying": info.underlying,
                "underlying_symbol": info.underlying_symbol,
                "decimals": int(decimals),
                "cash_raw": cash,
                "total_borrows_raw": borrows,
                "total_reserves_raw": reserves,
                "total_assets_raw": total_assets,
                "cash": _to_decimal(cash, int(decimals)),
                "total_borrows": _to_decimal(borrows, int(decimals)),
                "total_reserves": _to_decimal(reserves, int(decimals)),
                "total_assets": _to_decimal(total_assets, int(decimals)),
            }

    def get_tvl_rows(self, market: Optional[Dict] = None) -> List[Dict]:
        """Materialize `iter_reserve_tvl()` into a list."""
        return list(self.iter_reserve_tvl(market=market))


# Backwards-compatible alias if your pipeline expects `Adapter` naming.
Adapter = SumerTVLAdapter