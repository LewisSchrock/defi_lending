# liquid/adapters/fluid.py

from typing import Dict, Any, Iterable, List
from web3 import Web3
from .base import LiquidationAdapter

FLUID_LIQUIDATION_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True,  "internalType": "address", "name": "liquidator",      "type": "address"},
        {"indexed": True,  "internalType": "address", "name": "user",            "type": "address"},
        {"indexed": True,  "internalType": "address", "name": "debtToken",       "type": "address"},
        {"indexed": False, "internalType": "address", "name": "collateralToken", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "debtRepaid",      "type": "uint256"},
        {"indexed": False, "internalType": "uint256", "name": "collateralSeized","type": "uint256"},
    ],
    "name": "Liquidation",
    "type": "event",
}


class FluidLiquidationAdapter(LiquidationAdapter):
    protocol = "fluid"
    version = "v1"

    def resolve_market(self):
        return {"liquidation_contract": self.config["registry"]}

    def fetch_events(self, market, from_block, to_block):
        contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(market["liquidation_contract"]),
            abi=[FLUID_LIQUIDATION_EVENT_ABI]
        )
        MAX_BLOCK_SPAN = 1

        if from_block > to_block:
            return []

        current = from_block
        while current <= to_block:
            end = min(current + MAX_BLOCK_SPAN - 1, to_block)

            logs = contract.events.Liquidation.get_logs(
                from_block=current,
                to_block=end,
            )

            for log in logs:
                yield log

            current = end + 1

        logs = contract.events.Liquidation.get_logs(
            from_block=from_block,
            to_block=to_block,
        )
        return logs

    def normalize(self, raw_event):
        args = raw_event["args"]

        return {
            "chain": self.chain,
            "protocol": self.protocol,
            "version": self.version,
            "liquidator": args["liquidator"],
            "user": args["user"],
            "debt_token": args["debtToken"],
            "collateral_token": args["collateralToken"],
            "debt_repaid": int(args["debtRepaid"]),
            "collateral_seized": int(args["collateralSeized"]),
            "block_number": raw_event["blockNumber"],
            "tx_hash": raw_event["transactionHash"].hex(),
        }

    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        """
        Normalize a Fluid Liquidation log into the standard schema used in your pipeline.

        Output fields:
          - protocol, version, chain
          - tx_hash, log_index, block_number
          - borrower, liquidator
          - debt_asset, collateral_asset
          - debt_repaid, collateral_seized
        """

        # Decode using the same ABI/event class
        contract = self.web3.eth.contract(
            address=raw_event["address"],
            abi=FLUID_LIQUIDATION_EVENT_ABI,
        )
        event_cls = contract.events.Liquidation
        decoded = event_cls().process_log(raw_event)

        args = decoded["args"]

        borrower = args.get("user")            # placeholder name
        liquidator = args.get("liquidator")    # placeholder name
        debt_asset = args.get("debtAsset")
        collateral_asset = args.get("collateralAsset")
        debt_repaid = args.get("debtRepaid")
        collateral_seized = args.get("collateralSeized")

        return {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,

            "tx_hash": decoded["transactionHash"].hex(),
            "log_index": decoded["logIndex"],
            "block_number": decoded["blockNumber"],

            "borrower": borrower,
            "liquidator": liquidator,
            "debt_asset": debt_asset,
            "collateral_asset": collateral_asset,
            "debt_repaid": int(debt_repaid) if debt_repaid is not None else None,
            "collateral_seized": int(collateral_seized) if collateral_seized is not None else None,

            "raw_event": raw_event,
        }