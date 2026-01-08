

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional

from web3 import Web3
from web3.exceptions import LogTopicError
from web3._utils.events import get_event_data


# ---- Minimal ABIs ----

UNITROLLER_ABI_MIN = [
    {
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# Kinetic cToken ABI (minimal event)
LIQUIDATE_BORROW_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": False, "internalType": "address", "name": "liquidator", "type": "address"},
        {"indexed": False, "internalType": "address", "name": "borrower", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "repayAmount", "type": "uint256"},
        {"indexed": False, "internalType": "address", "name": "cTokenCollateral", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "seizeTokens", "type": "uint256"},
    ],
    "name": "LiquidateBorrow",
    "type": "event",
}

LIQUIDATE_BORROW_SIG = "LiquidateBorrow(address,address,uint256,address,uint256)"


@dataclass
class ScanParams:
    from_block: int
    to_block: int
    window: int = 10_000  # conservative default; can tune per RPC
    sleep_s: float = 0.15
    max_retries: int = 5
    backoff_base_s: float = 1.0


class KineticLiquidationAdapter:
    """Compound-v2 style liquidation scanner for Kinetic on Flare.

    Main-market-only: pass the main Unitroller (Comptroller proxy) address.

    Emits decoded LiquidateBorrow events from each cToken market returned by getAllMarkets().
    """

    def __init__(
        self,
        rpc_url: str,
        unitroller: str,
        chain: str = "flare",
        protocol: str = "kinetic",
        version: str = "v1",
    ):
        self.rpc_url = rpc_url
        self.unitroller = Web3.to_checksum_address(unitroller)
        self.chain = chain
        self.protocol = protocol
        self.version = version

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 30}))

        # Precompute topic0
        self.topic0 = "0x" + Web3.keccak(text=LIQUIDATE_BORROW_SIG).hex()

        # Cache block timestamps to avoid repeated getBlock calls
        self._ts_cache: Dict[int, int] = {}

        # Build an event ABI to decode with get_event_data
        self._event_abi = LIQUIDATE_BORROW_EVENT_ABI

    def discover_markets(self) -> List[str]:
        comp = self.w3.eth.contract(address=self.unitroller, abi=UNITROLLER_ABI_MIN)
        markets = comp.functions.getAllMarkets().call()
        return [Web3.to_checksum_address(m) for m in markets]

    def _get_block_ts(self, block_number: int) -> int:
        if block_number in self._ts_cache:
            return self._ts_cache[block_number]
        blk = self.w3.eth.get_block(block_number)
        ts = int(blk["timestamp"])
        self._ts_cache[block_number] = ts
        return ts

    def _get_logs_with_retry(self, params: Dict) -> List[Dict]:
        last_err: Optional[Exception] = None
        for i in range(self._scan.max_retries):
            try:
                return self.w3.eth.get_logs(params)
            except Exception as e:
                last_err = e
                # Backoff for rate limits / transient timeouts
                time.sleep(self._scan.backoff_base_s * (2 ** i))
        raise last_err  # type: ignore[misc]

    def iter_liquidations(self, scan: ScanParams) -> Iterator[Dict]:
        """Yield decoded liquidation events across the block range."""

        self._scan = scan  # stash for retry helper

        markets = self.discover_markets()
        if not markets:
            return

        start = scan.from_block
        end = scan.to_block

        # Decode helper (web3 event decoder expects HexBytes topics)
        codec = self.w3.codec

        # Windowed scan
        cur = start
        while cur <= end:
            to_blk = min(cur + scan.window - 1, end)

            # Some nodes accept a list of addresses; if not, fall back to per-market scanning.
            log_params = {
                "fromBlock": cur,
                "toBlock": to_blk,
                "address": markets,
                "topics": [self.topic0],
            }

            try:
                raw_logs = self._get_logs_with_retry(log_params)
            except Exception:
                # Fallback: scan each market individually in the same window.
                raw_logs = []
                for m in markets:
                    per_params = {
                        "fromBlock": cur,
                        "toBlock": to_blk,
                        "address": m,
                        "topics": [self.topic0],
                    }
                    raw_logs.extend(self._get_logs_with_retry(per_params))
                    if scan.sleep_s:
                        time.sleep(scan.sleep_s)

            for lg in raw_logs:
                try:
                    decoded = get_event_data(codec, self._event_abi, lg)
                except (LogTopicError, ValueError):
                    # Skip malformed/unexpected logs
                    continue

                args = decoded["args"]
                block_number = int(lg["blockNumber"])

                yield {
                    "protocol": self.protocol,
                    "version": self.version,
                    "chain": self.chain,
                    "pool": "main",
                    "market": Web3.to_checksum_address(lg["address"]),
                    "block_number": block_number,
                    "tx_hash": lg["transactionHash"].hex() if hasattr(lg["transactionHash"], "hex") else str(lg["transactionHash"]),
                    "log_index": int(lg["logIndex"]),
                    "timestamp": self._get_block_ts(block_number),
                    "liquidator": Web3.to_checksum_address(args["liquidator"]),
                    "borrower": Web3.to_checksum_address(args["borrower"]),
                    "repay_amount": str(int(args["repayAmount"])),
                    "cTokenCollateral": Web3.to_checksum_address(args["cTokenCollateral"]),
                    "seize_tokens": str(int(args["seizeTokens"])),
                }

            cur = to_blk + 1
            if scan.sleep_s:
                time.sleep(scan.sleep_s)


def scan_kinetic_main_liquidations(
    rpc_url: str,
    unitroller: str,
    from_block: int,
    to_block: int,
    window: int = 30,
    sleep_s: float = 0.15,
) -> List[Dict]:
    """Convenience helper returning a list; the adapter's iterator is preferred for big scans."""
    adapter = KineticLiquidationAdapter(rpc_url=rpc_url, unitroller=unitroller)
    scan = ScanParams(from_block=from_block, to_block=to_block, window=window, sleep_s=sleep_s)
    return list(adapter.iter_liquidations(scan))