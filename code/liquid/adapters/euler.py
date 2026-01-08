from typing import Dict, Any, Iterable, List, Tuple

from web3 import Web3
from web3.types import LogReceipt

from .base import LiquidationAdapter


# Minimal ABI for the Euler v2 EVault Liquidate event (from EVK Events.sol)
LIQUIDATE_EVENT_ABI = {
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
            "name": "violator",
            "type": "address",
        },
        {
            "indexed": False,
            "internalType": "address",
            "name": "collateral",
            "type": "address",
        },
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "repayAssets",
            "type": "uint256",
        },
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "yieldBalance",
            "type": "uint256",
        },
    ],
    "name": "Liquidate",
    "type": "event",
}


class EulerV2LiquidationAdapter(LiquidationAdapter):
    """Liquidation adapter for Euler v2 EVaults on Ethereum.

    Assumptions / requirements:
      * config["vaults"] is a list of EVault token addresses (ERC-4626-like vaults)
        that we want to scan for liquidation events.
      * We only support the v2 EVault architecture (event signature below).

    This mirrors the Moonwell/Venus pattern:
      * resolve_market() returns the vault universe to scan.
      * fetch_events() scans per-vault, per-block-range with a small window to
        respect RPC eth_getLogs limits.
      * normalize() decodes the Liquidate event and returns a standardized dict
        suitable for downstream panel construction.
    """

    protocol: str = "euler"
    version: str = "v2"

    def __init__(self, web3: Web3, chain: str, config: Dict[str, Any], outputs_dir: str):
        super().__init__(web3, chain, config, outputs_dir)

        # Pre-bind an ABI-only contract for decoding the Liquidate event
        self._liq_event_contract = self.web3.eth.contract(abi=[LIQUIDATE_EVENT_ABI])
        self._liq_event = self._liq_event_contract.events.Liquidate

        # topic0 = keccak("Liquidate(address,address,address,uint256,uint256)")
        self._liq_topic0 = self.web3.keccak(
            text="Liquidate(address,address,address,uint256,uint256)"
        ).hex()

        # Cache for block timestamps so we don't spam RPC
        self._block_ts_cache: Dict[int, int] = {}

    # -------- required interface methods --------

    def resolve_market(self) -> Dict[str, Any]:
        """Return the universe of EVaults to scan for liquidations.

        Expects the CSU config to provide a `vaults` list, e.g.:

            euler_v2_ethereum:
              protocol: euler
              version: v2
              chain: ethereum
              rpc: ...
              vaults:
                - 0x...
                - 0x...

        Returns
        -------
        dict with at least:
          - vaults: list[str] of EVault addresses (checksummed)
        """
        raw_vaults = self.config.get("vaults", [])

        vaults: List[str] = []
        for addr in raw_vaults:
            if not isinstance(addr, str):
                continue
            if not addr.startswith("0x") or len(addr) != 42:
                continue
            try:
                vaults.append(Web3.to_checksum_address(addr))
            except Exception:
                continue

        return {"vaults": vaults}

    def fetch_events(
        self,
        market: Dict[str, Any],
        from_block: int,
        to_block: int,
    ) -> Iterable[Tuple[str, LogReceipt]]:
        """Fetch Liquidate logs across all EVaults for [from_block, to_block].

        Parameters
        ----------
        market : dict
            Output of resolve_market(), containing "vaults".
        from_block, to_block : int
            Inclusive block range. Callers should keep this window small
            (e.g. 10 blocks) to respect RPC eth_getLogs limits on free tiers.

        Yields
        ------
        (vault_address, LogReceipt) tuples for each Liquidate event.
        """
        w3 = self.web3
        vaults: List[str] = market.get("vaults", [])

        if not vaults:
            return []

        fb = int(from_block)
        tb = int(to_block)

        for vault_addr in vaults:
            try:
                addr = Web3.to_checksum_address(vault_addr)
            except Exception:
                # Skip malformed addresses defensively
                continue

            filter_params = {
                "fromBlock": fb,
                "toBlock": tb,
                "address": addr,
                "topics": [self._liq_topic0],
            }

            try:
                logs: List[LogReceipt] = w3.eth.get_logs(filter_params)
            except Exception:
                # Skip ranges that hit provider limits or transient errors
                continue

            for log in logs:
                yield (addr, log)

    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        """Decode a Liquidate log into a standardized dict.

        Input
        -----
        raw_event : tuple
            (vault_address, LogReceipt)

        Output schema
        -------------
        {
            "protocol": "euler",
            "version": "v2",
            "chain": self.chain,
            "event_name": "Liquidate",
            "vault": <EVault address>,
            "block_number": int,
            "timestamp": int,
            "tx_hash": str,
            "log_index": int,
            "liquidator": str,
            "violator": str,
            "collateral": str,
            "repay_assets": int,
            "yield_balance": int,
        }
        """
        vault_addr, log = raw_event

        decoded = self._liq_event().process_log(log)
        args = decoded["args"]

        block_number: int = log["blockNumber"]
        ts = self._get_block_timestamp(block_number)

        return {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,
            "event_name": "Liquidate",
            "vault": Web3.to_checksum_address(vault_addr),
            "block_number": block_number,
            "timestamp": ts,
            "tx_hash": log["transactionHash"].hex(),
            "log_index": log["logIndex"],
            "liquidator": Web3.to_checksum_address(args["liquidator"]),
            "violator": Web3.to_checksum_address(args["violator"]),
            "collateral": Web3.to_checksum_address(args["collateral"]),
            "repay_assets": int(args["repayAssets"]),
            "yield_balance": int(args["yieldBalance"]),
        }

    # -------- helpers --------

    def _get_block_timestamp(self, block_number: int) -> int:
        """Return the block timestamp, caching results to avoid repeat RPC calls."""
        if block_number in self._block_ts_cache:
            return self._block_ts_cache[block_number]

        block = self.web3.eth.get_block(block_number)
        ts = int(block["timestamp"])
        self._block_ts_cache[block_number] = ts
        return ts
