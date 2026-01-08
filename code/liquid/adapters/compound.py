# liquid/adapters/compound_v2.py

from typing import Dict, Any, Iterable, List, Tuple
from pathlib import Path

from web3 import Web3
from web3.types import LogReceipt

from liquid.adapters.base import LiquidationAdapter
from tvl.config import COMPTROLLER_ABI  # we added this to tvl/config.py


# Mainnet Comptroller address (Compound v2)
COMPOUND_COMPTROLLER_MAINNET = "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"


# ABI for the LiquidateBorrow event on each cToken
LIQUIDATE_BORROW_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {
            "indexed": True,
            "internalType": "address",
            "name": "liquidator",
            "type": "address",
        },
        {
            "indexed": True,
            "internalType": "address",
            "name": "borrower",
            "type": "address",
        },
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "repayAmount",
            "type": "uint256",
        },
        {
            "indexed": False,
            "internalType": "address",
            "name": "cTokenCollateral",
            "type": "address",
        },
        {
            "indexed": False,
            "internalType": "address",
            "name": "cTokenBorrowed",
            "type": "address",
        },
    ],
    "name": "LiquidateBorrow",
    "type": "event",
}


class CompoundV2LiquidationAdapter(LiquidationAdapter):
    """
    Liquidation adapter for Compound v2 on EVM chains (Ethereum mainnet to start).

    It:
      - resolves all cToken markets via Comptroller.getAllMarkets()
      - scans each cToken for LiquidateBorrow events
      - decodes & normalizes events to a standard schema
    """

    protocol: str = "compound_v2"
    version: str = "v2"

    def __init__(self, web3: Web3, chain: str, config: Dict[str, Any], outputs_dir: str):
        super().__init__(web3, chain, config, outputs_dir)

        # Comptroller address: from config if present, else mainnet default
        self.comptroller_address = Web3.to_checksum_address(
            config.get("comptroller", COMPOUND_COMPTROLLER_MAINNET)
        )
        self._comptroller = self.web3.eth.contract(
            address=self.comptroller_address, abi=COMPTROLLER_ABI
        )

        # Event decoder (no address needed for decoding logs)
        self._liq_event_contract = self.web3.eth.contract(
            abi=[LIQUIDATE_BORROW_EVENT_ABI]
        )
        self._liq_event = self._liq_event_contract.events.LiquidateBorrow

        # Topic0 for filtering logs cheaply
        self._liq_topic0 = self.web3.keccak(
            text="LiquidateBorrow(address,address,uint256,address,address)"
        ).hex()

        # Simple block timestamp cache to avoid repeated RPC calls
        self._block_ts_cache: Dict[int, int] = {}

    # ----------------- required interface methods -----------------

    def resolve_market(self) -> Dict[str, Any]:
        """
        Resolve the Comptroller and all cToken markets (cTokens) for this CSU.
        """
        markets: List[str] = self._comptroller.functions.getAllMarkets().call()
        markets = [Web3.to_checksum_address(m) for m in markets]

        return {
            "comptroller": self.comptroller_address,
            "markets": markets,
        }

    def fetch_events(
        self,
        market: Dict[str, Any],
        from_block: int,
        to_block: int,
    ) -> Iterable[Tuple[str, LogReceipt]]:
        """
        Yield raw log objects for all LiquidateBorrow events across all cTokens
        in the market, within the given block window.

        We yield (ctoken_address, log) so normalize has both.
        """
        markets: List[str] = market["markets"]

        for ctoken in markets:
            # Filter logs by cToken address + LiquidateBorrow topic
            filter_params = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": ctoken,
                "topics": [self._liq_topic0],
            }
            try:
                logs: List[LogReceipt] = self.web3.eth.get_logs(filter_params)
            except Exception as e:
                # You can choose to log and continue, or re-raise; for now we continue
                # print(f"Warning: failed to fetch logs for {ctoken} in [{from_block}, {to_block}]: {e}")
                continue

            for log in logs:
                yield (ctoken, log)

    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        """
        Normalize a (ctoken_address, log) pair into the standard liquidation schema.

        Returns something like:
          {
            "protocol": "compound_v2",
            "version": "v2",
            "chain": "ethereum",
            "ctoken_emitter": ...,
            "block_number": ...,
            "timestamp": ...,
            "tx_hash": ...,
            "log_index": ...,
            "liquidator": ...,
            "borrower": ...,
            "repay_amount": ...,
            "cToken_borrowed": ...,
            "cToken_collateral": ...,
          }
        """
        ctoken_address, log = raw_event
        decoded = self._liq_event().process_log(log)
        args = decoded["args"]

        block_number: int = log["blockNumber"]
        ts = self._get_block_timestamp(block_number)

        return {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,
            "ctoken_emitter": Web3.to_checksum_address(ctoken_address),
            "block_number": block_number,
            "timestamp": ts,
            "tx_hash": log["transactionHash"].hex(),
            "log_index": log["logIndex"],
            "liquidator": Web3.to_checksum_address(args["liquidator"]),
            "borrower": Web3.to_checksum_address(args["borrower"]),
            "repay_amount": int(args["repayAmount"]),
            "cToken_collateral": Web3.to_checksum_address(args["cTokenCollateral"]),
            "cToken_borrowed": Web3.to_checksum_address(args["cTokenBorrowed"]),
        }

    # ----------------- helpers -----------------

    def _get_block_timestamp(self, block_number: int) -> int:
        """
        Cached block timestamp lookup to avoid hitting RPC for every event.
        """
        if block_number in self._block_ts_cache:
            return self._block_ts_cache[block_number]

        block = self.web3.eth.get_block(block_number)
        ts = int(block["timestamp"])
        self._block_ts_cache[block_number] = ts
        return ts