# adapters/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Iterable

class LiquidationAdapter(ABC):
    """
    Base interface for liquidation adapters.
    Implementations should be chain-agnostic; chain specifics come from config (RPC, registry, etc.).
    """
    protocol: str = ""
    version: str = ""

    def __init__(self, web3, chain: str, config: Dict[str, Any], outputs_dir: str):
        self.web3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir

    @abstractmethod
    def resolve_market(self) -> Dict[str, Any]:
        """Return dict with at least the resolved contract address(es) needed (e.g., pool)."""
        ...

    @abstractmethod
    def fetch_events(self, market: Dict[str, Any], from_block: int, to_block: int) -> Iterable[Any]:
        """Yield raw log/event objects for the chain + market within the block window."""
        ...

    @abstractmethod
    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        """Map raw event/log into standardized schema dict."""
        ...

    def get_block_timestamp(self, block_number: int) -> int:
        """
        Unified helper for timestamp lookup.
        Non-EVM chains can override this method.
        """
        try:
            block = self.web3.eth.get_block(block_number)
            return block["timestamp"]
        except Exception:
            return None

    def make_liquidation_record(
        self,
        *,
        tx_hash: str,
        log_index: int,
        block_number: int,
        timestamp: int,
        borrower: str,
        liquidator: str,
        repay_asset: str,
        repay_amount: str,
        collateral_asset: str,
        collateral_amount: str,
        extra: dict = None,
    ) -> dict:
        """
        Helper for adapter authors: standardized liquidation record schema.
        """
        base = {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,
            "tx_hash": tx_hash,
            "log_index": log_index,
            "block_number": block_number,
            "timestamp": timestamp,
            "borrower": borrower,
            "liquidator": liquidator,
            "repay_asset": repay_asset,
            "repay_amount": repay_amount,
            "collateral_asset": collateral_asset,
            "collateral_amount": collateral_amount,
        }
        if extra:
            base.update(extra)
        return base
