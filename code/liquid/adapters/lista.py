# liquid/adapters/lista.py

from typing import Dict, Any, Iterable, List
from web3 import Web3
from web3.types import LogReceipt

from .base import LiquidationAdapter


DEFAULT_MOOLAH_ADDR = "0x8F73b65B4caAf64FBA2aF91cC5D4a2A1318E5D8C"

# Liquidate(bytes32 id, address caller, address borrower,
#           uint256 repaidAssets, uint256 repaidShares,
#           uint256 seizedAssets, uint256 badDebtAssets, uint256 badDebtShares)
LISTA_LIQUIDATE_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {
            "indexed": True,
            "internalType": "bytes32",
            "name": "id",
            "type": "bytes32",
        },
        {
            "indexed": True,
            "internalType": "address",
            "name": "caller",
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
            "name": "repaidAssets",
            "type": "uint256",
        },
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "repaidShares",
            "type": "uint256",
        },
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "seizedAssets",
            "type": "uint256",
        },
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "badDebtAssets",
            "type": "uint256",
        },
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "badDebtShares",
            "type": "uint256",
        },
    ],
    "name": "Liquidate",
    "type": "event",
}

# view: idToMarketParams(Id id) → (loanToken, collateralToken, oracle, irm, lltv)
MOOLAH_ID_TO_MARKET_PARAMS_ABI = {
    "inputs": [
        {
            "internalType": "bytes32",
            "name": "id",
            "type": "bytes32",
        }
    ],
    "name": "idToMarketParams",
    "outputs": [
        {
            "internalType": "address",
            "name": "loanToken",
            "type": "address",
        },
        {
            "internalType": "address",
            "name": "collateralToken",
            "type": "address",
        },
        {
            "internalType": "address",
            "name": "oracle",
            "type": "address",
        },
        {
            "internalType": "address",
            "name": "irm",
            "type": "address",
        },
        {
            "internalType": "uint256",
            "name": "lltv",
            "type": "uint256",
        },
    ],
    "stateMutability": "view",
    "type": "function",
}

# keccak256("Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)")
LISTA_LIQUIDATE_TOPIC0 = (
    "0xa4946ede45d0c6f06a0f5ce92c9ad3b4751452d2fe0e25010783bcab57a67e41"
)


class ListaLiquidationAdapter(LiquidationAdapter):
    """
    Liquidation adapter for Lista Lending on BNB, via Moolah core.

    - Listens to Moolah's `Liquidate` event on the core contract.
    - Filters to only those market_ids we already know about (from config["market_ids"]).
    - Tracks any *unknown* market_ids it encounters so you can decide whether to
      add them to TVL + CSU definitions later.
    """

    protocol: str = "lista"
    version: str = "lending"

    def __init__(self, web3: Web3, chain: str, config: Dict[str, Any], outputs_dir: str):
        super().__init__(web3, chain, config, outputs_dir)

        # --- core address ---
        moolah_addr = config.get("moolah", DEFAULT_MOOLAH_ADDR)
        self.moolah_address = Web3.to_checksum_address(moolah_addr)

        # --- event + view function handle ---
        self._moolah = self.web3.eth.contract(
            address=self.moolah_address,
            abi=[LISTA_LIQUIDATE_EVENT_ABI, MOOLAH_ID_TO_MARKET_PARAMS_ABI],
        )
        self._liq_event = self._moolah.events.Liquidate
        self._liq_topic0 = LISTA_LIQUIDATE_TOPIC0
        self._id_to_market_params = self._moolah.functions.idToMarketParams

        # --- allowed market IDs (for TVL / liquidation consistency) ---
        # Expecting config["market_ids"] as list of hex strings "0x..."
        raw_ids = config.get("market_ids", [])
        self._allowed_market_ids_bytes = {
            self._to_bytes32(mid) for mid in raw_ids if mid is not None
        }

        # Track any market IDs seen in liquidate events that are NOT in allowed set.
        # This lets you inspect & decide whether to add them later.
        self._unknown_market_ids: set[bytes] = set()

        # Optional: cached token addresses per market_id for pricing
        # Expecting config["market_tokens"] as mapping:
        #   {"<market_id_hex>": {"debt_token": "0x...", "collateral_token": "0x..."}, ...}
        self._market_tokens_by_id: Dict[bytes, Dict[str, str]] = {}
        raw_market_tokens = config.get("market_tokens", {}) or {}
        for mid_hex, tokinfo in raw_market_tokens.items():
            try:
                mid_bytes = self._to_bytes32(mid_hex)
            except Exception:
                continue
            entry: Dict[str, str] = {}
            debt = tokinfo.get("debt_token") or tokinfo.get("debt")
            coll = tokinfo.get("collateral_token") or tokinfo.get("collateral")
            if debt:
                try:
                    entry["debt_token"] = Web3.to_checksum_address(debt)
                except Exception:
                    pass
            if coll:
                try:
                    entry["collateral_token"] = Web3.to_checksum_address(coll)
                except Exception:
                    pass
            if entry:
                self._market_tokens_by_id[mid_bytes] = entry

        self._block_ts_cache: Dict[int, int] = {}

    # -------- public helper --------

    def get_unknown_market_ids_hex(self) -> List[str]:
        """
        Return all market IDs (bytes32) that were seen in Liquidate events
        but are not in config['market_ids'].

        You can call this from sandbox after a scan to see what you're missing.
        """
        return [Web3.to_hex(mid) for mid in sorted(self._unknown_market_ids)]

    def get_market_tokens(self, market_id: str) -> Dict[str, Any]:
        """
        Return token info for a given market_id hex string.

        If not yet cached, this will query Moolah.idToMarketParams(id),
        cache the result, and then return it.
        """
        try:
            mid_bytes = self._to_bytes32(market_id)
        except Exception:
            return {}

        info = self._market_tokens_by_id.get(mid_bytes)
        if info is None:
            info = self.fetch_and_cache_market_tokens(market_id)
        return dict(info) if info else {}

    # -------- required interface methods --------

    def resolve_market(self) -> Dict[str, Any]:
        """
        For Lista, the "market" is:
          - Moolah core address
          - The allowed market IDs (for filtering)
        """
        return {
            "moolah": self.moolah_address,
            "market_ids": list(self._allowed_market_ids_bytes),
        }

    def fetch_events(
        self,
        market: Dict[str, Any],
        from_block: int,
        to_block: int,
    ) -> Iterable[LogReceipt]:
        """
        Fetch & filter Liquidate logs for [from_block, to_block].

        - Query Moolah core with topic0 = Liquidate
        - Decode each log to get `id`
        - If no allowed IDs configured → return all logs (no filter)
        - If allowed IDs configured:
            - keep logs where id ∈ allowed
            - record logs where id ∉ allowed into self._unknown_market_ids
        """
        fb = int(from_block)
        tb = int(to_block)
        if fb > tb:
            return []

        filter_params = {
            "fromBlock": fb,
            "toBlock": tb,
            "address": self.moolah_address,
            "topics": [self._liq_topic0],
        }

        try:
            logs: List[LogReceipt] = self.web3.eth.get_logs(filter_params)
        except Exception as e:
            print(
                f"[ListaLiquidationAdapter] get_logs error in "
                f"[{fb}, {tb}]: {e}"
            )
            return []

        # If there is no whitelist, take all logs as-is.
        if not self._allowed_market_ids_bytes:
            return logs

        allowed_ids = self._allowed_market_ids_bytes
        filtered_logs: List[LogReceipt] = []

        for log in logs:
            try:
                decoded = self._liq_event().process_log(log)
                market_id_bytes: bytes = decoded["args"]["id"]
            except Exception as e:
                print(
                    "[ListaLiquidationAdapter] Failed to decode Liquidate log "
                    f"at block {log.get('blockNumber')} index {log.get('logIndex')}: {e}"
                )
                continue

            if market_id_bytes in allowed_ids:
                filtered_logs.append(log)
            else:
                # Track unknown IDs for later inspection
                if market_id_bytes not in self._unknown_market_ids:
                    self._unknown_market_ids.add(market_id_bytes)
                    print(
                        "[ListaLiquidationAdapter] Saw liquidation for UNKNOWN market_id "
                        f"{Web3.to_hex(market_id_bytes)}; not included in results. "
                        "Consider adding this to TVL + CSU if you want it in-panel."
                    )

        return filtered_logs

    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        log: LogReceipt = raw_event
        decoded = self._liq_event().process_log(log)
        args = decoded["args"]

        block_number: int = log["blockNumber"]
        ts = self._get_block_timestamp(block_number)

        market_id_hex = Web3.to_hex(args["id"])

        # Optional token metadata for pricing (lazy load via idToMarketParams)
        try:
            mid_bytes = self._to_bytes32(market_id_hex)
        except Exception:
            mid_bytes = None

        debt_token = None
        collateral_token = None
        if mid_bytes is not None:
            tokinfo = self._market_tokens_by_id.get(mid_bytes)
            if tokinfo is None:
                tokinfo = self.fetch_and_cache_market_tokens(market_id_hex)
            if tokinfo:
                debt_token = tokinfo.get("debt_token")
                collateral_token = tokinfo.get("collateral_token")

        return {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,
            "event_name": "Liquidate",
            "moolah": self.moolah_address,
            "market_id": market_id_hex,
            "caller": Web3.to_checksum_address(args["caller"]),
            "borrower": Web3.to_checksum_address(args["borrower"]),
            "repaid_assets": int(args["repaidAssets"]),
            "repaid_shares": int(args["repaidShares"]),
            "seized_assets": int(args["seizedAssets"]),
            "bad_debt_assets": int(args["badDebtAssets"]),
            "bad_debt_shares": int(args["badDebtShares"]),
            "block_number": block_number,
            "block_timestamp": ts,
            "tx_hash": log["transactionHash"].hex(),
            "log_index": log["logIndex"],
            "debt_token": debt_token,
            "collateral_token": collateral_token,
        }

    # -------- helpers --------

    def fetch_and_cache_market_tokens(self, market_id_hex: str) -> Dict[str, Any]:
        """
        Call Moolah.idToMarketParams(id) to discover the loan/collateral tokens
        for a given market id, cache the result, and return it.

        market_id_hex: hex string like '0x....' (same format as normalize() returns)
        """
        try:
            mid_bytes = self._to_bytes32(market_id_hex)
        except Exception:
            print(f"[ListaLiquidationAdapter] invalid market_id: {market_id_hex}")
            return {}

        # already cached?
        if mid_bytes in self._market_tokens_by_id:
            return dict(self._market_tokens_by_id[mid_bytes])

        try:
            loan_token, collateral_token, oracle, irm, lltv = (
                self._id_to_market_params(mid_bytes).call()
            )
        except Exception as e:
            print(
                "[ListaLiquidationAdapter] idToMarketParams() call failed for "
                f"{market_id_hex}: {e}"
            )
            return {}

        info = {
            "debt_token": Web3.to_checksum_address(loan_token),
            "collateral_token": Web3.to_checksum_address(collateral_token),
            "oracle": Web3.to_checksum_address(oracle),
            "irm": Web3.to_checksum_address(irm),
            "lltv": int(lltv),
        }

        self._market_tokens_by_id[mid_bytes] = info
        return dict(info)

    def _get_block_timestamp(self, block_number: int) -> int:
        if block_number in self._block_ts_cache:
            return self._block_ts_cache[block_number]

        block = self.web3.eth.get_block(block_number)
        ts = int(block["timestamp"])
        self._block_ts_cache[block_number] = ts
        return ts

    @staticmethod
    def _to_bytes32(x: Any) -> bytes:
        """
        Normalize config market_ids (likely hex strings) into 32-byte values.
        """
        if isinstance(x, bytes):
            if len(x) == 32:
                return x
            # If it's shorter, left-pad; if longer, slice (paranoid)
            return x.rjust(32, b"\x00")[:32]

        if isinstance(x, str):
            # Expect "0x..." hex string for ids coming from TVL adapter
            if x.startswith("0x"):
                raw = bytes.fromhex(x[2:])
            else:
                raw = bytes.fromhex(x)
            if len(raw) == 32:
                return raw
            return raw.rjust(32, b"\x00")[:32]

        raise TypeError(f"Cannot convert {x!r} to bytes32")