from __future__ import annotations

import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Iterable, Iterator, List, Optional

from web3 import Web3
from web3._utils.events import get_event_data
from web3.exceptions import LogTopicError


# --- Minimal ABIs ---

ERC20_DECIMALS_ABI = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    }
]

LIQUIDATION_CALL_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "internalType": "address", "name": "collateralAsset", "type": "address"},
        {"indexed": True, "internalType": "address", "name": "debtAsset", "type": "address"},
        {"indexed": True, "internalType": "address", "name": "user", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "debtToCover", "type": "uint256"},
        {"indexed": False, "internalType": "uint256", "name": "liquidatedCollateralAmount", "type": "uint256"},
        {"indexed": False, "internalType": "address", "name": "liquidator", "type": "address"},
        {"indexed": False, "internalType": "bool", "name": "receiveAToken", "type": "bool"},
    ],
    "name": "LiquidationCall",
    "type": "event",
}

LIQUIDATION_CALL_SIG = "LiquidationCall(address,address,address,uint256,uint256,address,bool)"


@dataclass
class ScanParams:
    from_block: int
    to_block: int
    window: int = 10_000
    sleep_s: float = 0.15
    max_retries: int = 5
    backoff_base_s: float = 1.0


class TydroLiquidationAdapter:
    """
    Aave-v3 style liquidation scanner for Tydro.

    Emits Pool::LiquidationCall events. Decimals are fetched via ERC20.decimals().
    """

    def __init__(
        self,
        web3: Web3,
        chain: str,
        config: Dict[str, Any],
        outputs_dir: str,
        protocol: str = "tydro",
        version: str = "v1",
    ):
        self.w3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir
        self.protocol = protocol
        self.version = version

        pool = config.get("Pool") or config.get("pool")
        if not pool:
            raise ValueError("TydroLiquidationAdapter requires Pool address in CSU config (key: 'Pool').")

        self.pool = Web3.to_checksum_address(pool)

        # Important: "0x" prefix so you don't have to fix it every time.
        self.topic0 = "0x" + Web3.keccak(text=LIQUIDATION_CALL_SIG).hex()

        self._event_abi = LIQUIDATION_CALL_EVENT_ABI
        self._ts_cache: Dict[int, int] = {}
        self._decimals_cache: Dict[str, int] = {}

    def resolve_market(self) -> Dict[str, str]:
        # Keep the same “market dict” pattern you use elsewhere.
        return {"pool": self.pool}

    def _get_block_ts(self, block_number: int) -> int:
        if block_number in self._ts_cache:
            return self._ts_cache[block_number]
        blk = self.w3.eth.get_block(block_number)
        ts = int(blk["timestamp"])
        self._ts_cache[block_number] = ts
        return ts

    def _get_decimals(self, token: str) -> int:
        token = Web3.to_checksum_address(token)
        if token in self._decimals_cache:
            return self._decimals_cache[token]
        c = self.w3.eth.contract(address=token, abi=ERC20_DECIMALS_ABI)
        dec = int(c.functions.decimals().call())
        self._decimals_cache[token] = dec
        return dec

    def _get_logs_with_retry(self, params: Dict[str, Any], scan: ScanParams) -> List[Dict[str, Any]]:
        last_err: Optional[Exception] = None
        for i in range(scan.max_retries):
            try:
                return self.w3.eth.get_logs(params)
            except Exception as e:
                last_err = e
                time.sleep(scan.backoff_base_s * (2 ** i))
        raise last_err  # type: ignore[misc]

    def fetch_events(self, market: Dict[str, str], from_block: int, to_block: int) -> Iterable[Dict[str, Any]]:
        # Minimal wrapper for your existing adapter patterns.
        params = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": market["pool"],
            "topics": [self.topic0],
        }
        # Use a dummy ScanParams for retry controls; real scan logic uses iter_liquidations().
        dummy = ScanParams(from_block=from_block, to_block=to_block)
        return self._get_logs_with_retry(params, dummy)

    def normalize(self, log: Dict[str, Any]) -> Dict[str, Any]:
        decoded = get_event_data(self.w3.codec, self._event_abi, log)
        args = decoded["args"]

        collateral = Web3.to_checksum_address(args["collateralAsset"])
        debt = Web3.to_checksum_address(args["debtAsset"])

        collateral_dec = self._get_decimals(collateral)
        debt_dec = self._get_decimals(debt)

        debt_raw = int(args["debtToCover"])
        coll_raw = int(args["liquidatedCollateralAmount"])

        # Scaled human units (as strings to avoid float issues)
        debt_scaled = str(Decimal(debt_raw) / (Decimal(10) ** debt_dec))
        coll_scaled = str(Decimal(coll_raw) / (Decimal(10) ** collateral_dec))

        block_number = int(log["blockNumber"])

        txh = log["transactionHash"]
        tx_hash = txh.hex() if hasattr(txh, "hex") else str(txh)

        return {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,
            "market": "pool",  # Aave-style: single pool address
            "pool": Web3.to_checksum_address(log["address"]),
            "block_number": block_number,
            "timestamp": self._get_block_ts(block_number),
            "tx_hash": tx_hash,
            "log_index": int(log["logIndex"]),
            "collateral_asset": collateral,
            "debt_asset": debt,
            "user": Web3.to_checksum_address(args["user"]),
            "liquidator": Web3.to_checksum_address(args["liquidator"]),
            "receive_a_token": bool(args["receiveAToken"]),
            "debt_to_cover_raw": str(debt_raw),
            "liquidated_collateral_amount_raw": str(coll_raw),
            "debt_asset_decimals": debt_dec,
            "collateral_asset_decimals": collateral_dec,
            "debt_to_cover": debt_scaled,
            "liquidated_collateral_amount": coll_scaled,
        }

    def iter_liquidations(self, scan: ScanParams) -> Iterator[Dict[str, Any]]:
        market = self.resolve_market()

        cur = scan.from_block
        end = scan.to_block

        while cur <= end:
            to_blk = min(cur + scan.window - 1, end)
            params = {
                "fromBlock": cur,
                "toBlock": to_blk,
                "address": market["pool"],
                "topics": [self.topic0],
            }

            raw_logs = self._get_logs_with_retry(params, scan)

            for lg in raw_logs:
                try:
                    yield self.normalize(lg)
                except (LogTopicError, ValueError):
                    continue

            cur = to_blk + 1
            if scan.sleep_s:
                time.sleep(scan.sleep_s)