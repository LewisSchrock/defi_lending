
# liquid/adapters/benqi.py

from typing import Dict, Any, Iterable, List, Tuple

from web3 import Web3
from web3.types import LogReceipt

from .base import LiquidationAdapter
from tvl.config import COMPTROLLER_ABI

# Benqi Comptroller on Avalanche C-Chain
# Source: Benqi Lending docs / on-chain config
BENQI_COMPTROLLER = "0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4"


# ABI for the LiquidateBorrow event on Benqi qTokens (Compound-style)
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


class BenqiLiquidationAdapter(LiquidationAdapter):
    """
    Liquidation adapter for Benqi Lending on Avalanche C-Chain.

    Pattern is identical to Compound v2:
      - resolve all qToken markets via Comptroller.getAllMarkets()
      - scan each qToken for LiquidateBorrow events
      - decode & normalize to a standard schema
    """

    protocol: str = "benqi"
    version: str = "v1"

    def __init__(self, web3: Web3, chain: str, config: Dict[str, Any], outputs_dir: str):
        super().__init__(web3, chain, config, outputs_dir)

        # Comptroller address: from config if present, else Benqi mainnet default
        self.comptroller_address = Web3.to_checksum_address(
            config.get("comptroller", BENQI_COMPTROLLER)
        )
        self._comptroller = self.web3.eth.contract(
            address=self.comptroller_address,
            abi=COMPTROLLER_ABI,
        )

        # Event decoder
        self._liq_event_contract = self.web3.eth.contract(
            abi=[LIQUIDATE_BORROW_EVENT_ABI]
        )
        self._liq_event = self._liq_event_contract.events.LiquidateBorrow

        # Topic0 for filtering logs
        self._liq_topic0 = self.web3.keccak(
            text="LiquidateBorrow(address,address,uint256,address,address)"
        ).hex()

        # blockNumber -> timestamp cache
        self._block_ts_cache: Dict[int, int] = {}

    # ------------- required interface methods -------------

    def resolve_market(self) -> Dict[str, Any]:
        """
        Resolve the Benqi Comptroller and all qToken markets for this CSU.
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
        Yield (qtoken_address, log) for all LiquidateBorrow events
        across all Benqi markets in the block window.
        """
        markets: List[str] = market["markets"]

        for qtoken in markets:
            filter_params = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": qtoken,
                "topics": [self._liq_topic0],
            }
            try:
                logs: List[LogReceipt] = self.web3.eth.get_logs(filter_params)
            except Exception:
                # You can log this if you want; for now we just skip this market+range
                # print(f"Warning: failed to fetch logs for {qtoken} in [{from_block}, {to_block}]: {e}")
                continue

            for log in logs:
                yield (qtoken, log)

    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        """
        Normalize a (qtoken_address, log) pair into the standard liquidation schema.

        Output example:
          {
            "protocol": "benqi",
            "version": "v1",
            "chain": "avalanche",
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
        qtoken_address, log = raw_event
        decoded = self._liq_event().process_log(log)
        args = decoded["args"]

        block_number: int = log["blockNumber"]
        ts = self._get_block_timestamp(block_number)

        return {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,
            "ctoken_emitter": Web3.to_checksum_address(qtoken_address),
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

    # ------------- helpers -------------

    def _get_block_timestamp(self, block_number: int) -> int:
        """
        Cached block timestamp lookup (saves RPC calls).
        """
        if block_number in self._block_ts_cache:
            return self._block_ts_cache[block_number]

        block = self.web3.eth.get_block(block_number)
        ts = int(block["timestamp"])
        self._block_ts_cache[block_number] = ts
        return ts