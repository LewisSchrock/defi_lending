from typing import Dict, Any, Iterable
from web3 import Web3
from web3._utils.events import get_event_data
from .base import LiquidationAdapter
import os
import time
from eth_utils import keccak

ADDRESSES_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

POOL_LIQUIDATION_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True,  "name": "collateralAsset", "type": "address"},
        {"indexed": True,  "name": "debtAsset",       "type": "address"},
        {"indexed": True, "name": "user",            "type": "address"},
        {"indexed": False, "name": "debtToCover",     "type": "uint256"},
        {"indexed": False, "name": "liquidatedCollateralAmount", "type": "uint256"},
        {"indexed": False, "name": "liquidator",      "type": "address"},
        {"indexed": False, "name": "receiveAToken",   "type": "bool"},
    ],
    "name": "LiquidationCall",
    "type": "event",
}

PACE_S = float(os.environ.get("PACE_S", "0"))
EVENT_SIG = "LiquidationCall(address,address,address,uint256,uint256,address,bool)"
TOPIC0 = keccak(text=EVENT_SIG).hex()

class AaveV3Adapter(LiquidationAdapter):
    protocol = "aave"
    version = "v3"

    def resolve_market(self) -> Dict[str, Any]:
        reg = self.config["registry"]
        contract = self.web3.eth.contract(address=Web3.to_checksum_address(reg), abi=ADDRESSES_PROVIDER_ABI)
        pool = contract.functions.getPool().call()
        pool = Web3.to_checksum_address(pool)
        return {"pool": pool}

    def fetch_events(self, market: Dict[str, Any], from_block: int, to_block: int, chunk: int = 10):
        """
        Fetch raw LiquidationCall logs from Aave v3 Pool via eth_getLogs, chunked to
        obey Alchemy Free tier limits (<=10-block ranges) and handle 'too many requests'
        / compute-unit errors without crashing.
        """
        w3 = self.web3
        pool = Web3.to_checksum_address(market["pool"])

        start = from_block
        while start <= to_block:
            end = min(start + chunk - 1, to_block)

            flt = {
                "fromBlock": hex(int(start)),
                "toBlock":   hex(int(end)),
                "address":   pool,
                "topics":    [TOPIC0],
            }

            r = w3.provider.make_request("eth_getLogs", [flt])
            if "error" in r:
                msg = r["error"].get("message", "")
                print(f"[warn] getLogs error on {start}-{end}: {msg}")
                # Enforce 10-block maximum per request (Alchemy Free)
                if (end - start + 1) > 10:
                    end = start + 9
                    continue
                # Already at 10-block window and still failing: advance and continue
                start = end + 1
                if PACE_S > 0:
                    time.sleep(PACE_S)
                continue

            res = r.get("result", [])
            for L in res:
                # Yield raw logs; normalize() will decode them via get_event_data
                yield L

            # Advance window
            start = end + 1
            # Optional pacing
            if PACE_S > 0:
                time.sleep(PACE_S)

    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        # Convert common hex fields to ints if needed
        raw_block = raw_event.get("blockNumber")
        if isinstance(raw_block, str):
            block = int(raw_block, 16)
        else:
            block = int(raw_block)

        raw_log_index = raw_event.get("logIndex")
        if isinstance(raw_log_index, str):
            log_index = int(raw_log_index, 16)
        else:
            log_index = int(raw_log_index)

        raw_tx_index = raw_event.get("transactionIndex")
        if isinstance(raw_tx_index, str):
            tx_index = int(raw_tx_index, 16)
        else:
            tx_index = raw_tx_index

        tx_hash = raw_event.get("transactionHash")

        # Build a log dict suitable for get_event_data, similar to the standalone script
        log_for_decode = {
            "address": Web3.to_checksum_address(raw_event.get("address")),
            "data": raw_event.get("data", "0x"),
            "topics": raw_event.get("topics", []),
            "blockNumber": block,
            "logIndex": log_index,
            "transactionIndex": tx_index,
            "blockHash": raw_event.get("blockHash"),
            "transactionHash": tx_hash,
            "removed": raw_event.get("removed", False),
        }

        try:
            decoded = get_event_data(self.web3.codec, POOL_LIQUIDATION_EVENT_ABI, log_for_decode)
            args = decoded["args"]

            ts = int(self.web3.eth.get_block(block)["timestamp"])
            return {
                "protocol": self.protocol,
                "version": self.version,
                "chain": self.chain,
                "tx_hash": tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash),
                "log_index": log_index,
                "block_number": block,
                "timestamp": ts,
                "borrower": str(args["user"]),
                "liquidator": str(args["liquidator"]),
                "collateral_token": Web3.to_checksum_address(args["collateralAsset"]),
                "debt_token": Web3.to_checksum_address(args["debtAsset"]),
                "collateral_amount": str(int(args["liquidatedCollateralAmount"])),
                "debt_repaid": str(int(args["debtToCover"])),
                "receive_a_token": bool(args["receiveAToken"]),
                "usd_value": None,
            }
        except Exception as e:
            # If decoding fails for any reason, log a warning and return a minimal row
            print(f"[warn] decode failed at block {block} logIndex {log_index}: {e}")
            ts = int(self.web3.eth.get_block(block)["timestamp"])
            return {
                "protocol": self.protocol,
                "version": self.version,
                "chain": self.chain,
                "tx_hash": tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash),
                "log_index": log_index,
                "block_number": block,
                "timestamp": ts,
                "borrower": None,
                "liquidator": None,
                "collateral_token": None,
                "debt_token": None,
                "collateral_amount": None,
                "debt_repaid": None,
                "receive_a_token": None,
                "usd_value": None,
            }
