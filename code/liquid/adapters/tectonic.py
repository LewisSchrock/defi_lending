

"""Tectonic (Cronos) liquidation adapter.

Tectonic is a Compound-v2-style money market. Liquidations emit `LiquidateBorrow` events
from the *borrowed market* (tToken) contract.

CSU expectation (your config):
- protocol: tectonic
- chain: cronos
- version/pool: main | veno | defi
- TectonicSocket: per-pool Unitroller/Comptroller proxy

This adapter:
- Discovers all markets for the pool via `getAllMarkets()` on the pool socket
- Scans each market for LiquidateBorrow logs in block chunks
- Decodes logs into a standardized dict row

Notes:
- repayAmount is denominated in the borrowed underlying token base units.
- seizeTokens is denominated in collateral tToken units (NOT underlying).
  You can enrich later by converting seizeTokens -> collateral underlying using exchangeRate.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from web3 import Web3
from web3.contract import Contract
from web3.exceptions import LogTopicError

# Low-level event decoding
from web3._utils.events import get_event_data


# -----------------------------
# Event identity
# -----------------------------

LIQUIDATE_SIGNATURE = "LiquidateBorrow(address,address,uint256,address,uint256)"
LIQUIDATE_TOPIC0 = "0x"+ (Web3.keccak(text=LIQUIDATE_SIGNATURE).hex())

LIQUIDATE_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": False, "internalType": "address", "name": "liquidator", "type": "address"},
        {"indexed": False, "internalType": "address", "name": "borrower", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "repayAmount", "type": "uint256"},
        {"indexed": False, "internalType": "address", "name": "tTokenCollateral", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "seizeTokens", "type": "uint256"},
    ],
    "name": "LiquidateBorrow",
    "type": "event",
}


# -----------------------------
# Minimal ABIs
# -----------------------------

COMPTROLLER_ABI = [
    {
        "type": "function",
        "name": "getAllMarkets",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address[]"}],
    }
]

TTOKEN_ABI = [
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

NATIVE_ADDR = "0x0000000000000000000000000000000000000000"


# -----------------------------
# Helpers
# -----------------------------


def to_checksum(w3: Web3, addr: str) -> str:
    """Normalize and checksum an EVM address.

    We fail loudly if invalid; otherwise Web3 may treat it as ENS and error confusingly.
    """

    if not isinstance(addr, str):
        raise TypeError(f"Address must be a str, got {type(addr)}")
    a = addr.strip()
    if a.startswith("0x"):
        a = "0x" + a[2:].lower()
    if not Web3.is_address(a):
        raise ValueError(f"Invalid hex address: {a!r} (len={len(a)})")
    try:
        return w3.to_checksum_address(a)
    except Exception:
        return Web3.to_checksum_address(a)


def discover_markets(w3: Web3, socket: str) -> List[str]:
    """Discover all tToken markets registered in the pool socket."""

    c = w3.eth.contract(address=to_checksum(w3, socket), abi=COMPTROLLER_ABI)
    mkts = c.functions.getAllMarkets().call()
    return [to_checksum(w3, m) for m in mkts]


def read_underlying_and_decimals(w3: Web3, ttoken: str) -> Tuple[str, int]:
    """Return (underlying_address, underlying_decimals) for a tToken market.

    - For native CRO market, underlying() may revert; we return (NATIVE_ADDR, 18).
    """

    m = w3.eth.contract(address=to_checksum(w3, ttoken), abi=TTOKEN_ABI)

    # underlying()
    try:
        underlying = to_checksum(w3, m.functions.underlying().call())
    except Exception:
        underlying = NATIVE_ADDR

    # decimals of underlying
    if underlying.lower() == NATIVE_ADDR:
        udec = 18
    else:
        erc20 = w3.eth.contract(address=underlying, abi=ERC20_DECIMALS_ABI)
        try:
            udec = int(erc20.functions.decimals().call())
        except Exception:
            udec = 18

    return underlying, udec


def decode_liquidate_log(w3: Web3, log: Dict) -> Dict:
    """Decode a LiquidateBorrow log into args using the minimal event ABI."""

    try:
        decoded = get_event_data(w3.codec, LIQUIDATE_EVENT_ABI, log)
    except (LogTopicError, ValueError) as e:
        raise ValueError(f"Failed to decode LiquidateBorrow log: {e}")

    # decoded['args'] is AttributeDict
    args = dict(decoded["args"])
    return {
        "liquidator": args["liquidator"],
        "borrower": args["borrower"],
        "repayAmount": int(args["repayAmount"]),
        "tTokenCollateral": args["tTokenCollateral"],
        "seizeTokens": int(args["seizeTokens"]),
    }


def iter_logs_chunked(
    w3: Web3,
    address: str,
    topic0: str,
    from_block: int,
    to_block: int,
    chunk: int = 10_000,        # Cronos block-range-cap
    min_chunk: int = 1_000,     # fallback
    sleep_s: float = 0.25,      # ~240 req/min worst-case
) -> Iterator[Dict]:
    """Yield logs for (address, topic0) between from_block and to_block in chunks.

    Designed for Cronos public RPC constraints:
      - eth_getLogs block-range-cap is typically ~10k blocks
      - public RPC is rate limited (~300 req/min); we sleep between requests

    Strategy:
      - Scan forward in <=chunk block windows
      - Sleep briefly after each successful eth_getLogs
      - On error, shrink window and back off
    """
    import time

    a = to_checksum(w3, address)

    start = int(from_block)
    end = int(to_block)
    step = int(chunk)

    while start <= end:
        this_to = min(end, start + step - 1)

        try:
            logs = w3.eth.get_logs(
                {
                    "fromBlock": start,
                    "toBlock": this_to,
                    "address": a,
                    "topics": [topic0],
                }
            )

            for lg in logs:
                yield dict(lg)

            start = this_to + 1

            # Rate-limit protection
            if sleep_s and sleep_s > 0:
                time.sleep(sleep_s)

        except Exception as e:
            # Back off + retry smaller range
            if step <= min_chunk:
                raise RuntimeError(
                    f"eth_getLogs failed even at min_chunk={min_chunk} for [{start}, {this_to}]: {e}"
                )

            step = max(min_chunk, step // 2)
            time.sleep(max(0.5, float(sleep_s) if sleep_s else 0.5))


# -----------------------------
# Adapter
# -----------------------------


@dataclass
class TectonicLiquidationAdapter:
    """Liquidation adapter for a single Tectonic pool (CSU)."""

    rpc: str
    chain: str
    pool: str
    socket: str
    protocol: str = "tectonic"

    # behavior knobs
    log_chunk: int = 2_000
    min_log_chunk: int = 50
    sleep_s: float = 0.0

    def build_w3(self) -> Web3:
        return Web3(Web3.HTTPProvider(self.rpc, request_kwargs={"timeout": 30}))

    @classmethod
    def from_csu(cls, csu: Dict) -> "TectonicLiquidationAdapter":
        """Create adapter from a CSU dict (parsed YAML)."""

        rpc = csu["rpc"]
        chain = csu.get("chain", "cronos")

        # Your CSU keys encode the pool, but also store it explicitly when convenient.
        pool = csu.get("version") or csu.get("pool") or "main"

        socket = csu.get("TectonicSocket")
        if not socket:
            # Backward compatible with older naming
            socket = csu.get("TectonicSocket_Main") or csu.get("TectonicSocket_Veno") or csu.get("TectonicSocket_DeFi")

        if not socket:
            raise KeyError("Tectonic liquidation adapter requires 'TectonicSocket' in CSU config")

        return cls(
            rpc=rpc,
            chain=chain,
            pool=pool,
            socket=socket,
            log_chunk=int(csu.get("liq_log_chunk", 2000)),
            min_log_chunk=int(csu.get("liq_min_log_chunk", 50)),
            sleep_s=float(csu.get("liq_sleep_s", 0.0)),
        )

    def get_markets(self, w3: Web3) -> List[str]:
        return discover_markets(w3, self.socket)

    def build_market_metadata(self, w3: Web3, markets: List[str]) -> Dict[str, Dict[str, object]]:
        """Build a mapping: ttoken -> {underlying, underlying_decimals}."""

        meta: Dict[str, Dict[str, object]] = {}
        for m in markets:
            u, udec = read_underlying_and_decimals(w3, m)
            meta[to_checksum(w3, m)] = {"underlying": u, "underlying_decimals": int(udec)}
        return meta

    def fetch_events(
        self,
        from_block: int,
        to_block: int,
        markets: Optional[List[str]] = None,
        include_timestamp: bool = True,
        max_markets: Optional[int] = None,
    ) -> Iterator[Dict[str, object]]:
        """Yield decoded liquidation events for the CSU between from_block and to_block.

        Args:
            from_block: inclusive
            to_block: inclusive
            markets: optional explicit list of markets; otherwise discovered from socket
            include_timestamp: whether to attach block timestamp (costs an extra RPC call per unique block)
            max_markets: optional cap for testing
        """

        w3 = self.build_w3()

        if not w3.is_connected():
            raise RuntimeError(f"Failed to connect Web3 to {self.rpc}")

        mkts = markets or self.get_markets(w3)
        if max_markets is not None:
            mkts = mkts[: int(max_markets)]

        # Precompute borrow-market underlying/decimals (repayAmount units).
        meta = self.build_market_metadata(w3, mkts)

        # Cache block timestamps to avoid repeated calls.
        ts_cache: Dict[int, int] = {}

        def get_ts(bn: int) -> int:
            if bn in ts_cache:
                return ts_cache[bn]
            blk = w3.eth.get_block(bn)
            ts_cache[bn] = int(blk["timestamp"])
            return ts_cache[bn]

        seen = set()  # (tx_hash, log_index)

        for borrow_market in mkts:
            borrow_market = to_checksum(w3, borrow_market)

            for log in iter_logs_chunked(
                w3,
                address=borrow_market,
                topic0=LIQUIDATE_TOPIC0,
                from_block=int(from_block),
                to_block=int(to_block),
                chunk=self.log_chunk,
                min_chunk=self.min_log_chunk,
                sleep_s=self.sleep_s,
            ):
                txh = log.get("transactionHash")
                tx_hash = txh.hex() if hasattr(txh, "hex") else str(txh)
                log_index = int(log.get("logIndex"))

                key = (tx_hash, log_index)
                if key in seen:
                    continue
                seen.add(key)

                decoded = decode_liquidate_log(w3, log)

                # Borrow-side units
                u = meta[borrow_market]["underlying"]
                udec = int(meta[borrow_market]["underlying_decimals"])

                repay_raw = int(decoded["repayAmount"])
                repay_underlying = Decimal(repay_raw) / (Decimal(10) ** Decimal(udec))

                bn = int(log.get("blockNumber"))

                row: Dict[str, object] = {
                    "protocol": self.protocol,
                    "chain": self.chain,
                    "pool": self.pool,
                    "borrow_market": borrow_market,
                    "borrow_underlying": u,
                    "borrow_underlying_decimals": udec,
                    "collateral_market": to_checksum(w3, decoded["tTokenCollateral"]),
                    "borrower": to_checksum(w3, decoded["borrower"]),
                    "liquidator": to_checksum(w3, decoded["liquidator"]),
                    "repay_amount_raw": repay_raw,
                    "repay_amount_underlying": str(repay_underlying),
                    "seize_tokens_raw": int(decoded["seizeTokens"]),
                    "tx_hash": tx_hash,
                    "log_index": log_index,
                    "block_number": bn,
                }

                if include_timestamp:
                    row["timestamp"] = get_ts(bn)

                yield row


# -----------------------------
# Convenience entrypoint for sandbox/testing
# -----------------------------


def run_quick_test(csu: Dict, from_block: int, to_block: int, max_markets: int = 3, max_events: int = 10) -> List[Dict[str, object]]:
    """Quick test helper: fetch a small number of events and return them as a list."""

    ad = TectonicLiquidationAdapter.from_csu(csu)
    out: List[Dict[str, object]] = []
    for i, ev in enumerate(ad.fetch_events(from_block, to_block, max_markets=max_markets), start=1):
        out.append(ev)
        if i >= max_events:
            break
    return out