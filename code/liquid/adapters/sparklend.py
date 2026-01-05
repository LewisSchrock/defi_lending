# liquid/adapters/sparklend_liquidations.py

from typing import Any, Dict, Iterable, List

from eth_utils import keccak
from web3 import Web3
from web3._utils.events import get_event_data
from web3._utils.filters import construct_event_topic_set

from .base import LiquidationAdapter

# --- Minimal ABIs we need ---

ADDRESSES_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# SparkLend is an Aave v3 fork, so LiquidationCall layout matches Aave v3
POOL_LIQUIDATION_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "internalType": "address", "name": "collateralAsset", "type": "address"},
        {"indexed": True, "internalType": "address", "name": "debtAsset", "type": "address"},
        {"indexed": True, "internalType": "address", "name": "user", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "debtToCover", "type": "uint256"},
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "liquidatedCollateralAmount",
            "type": "uint256",
        },
        {"indexed": False, "internalType": "address", "name": "liquidator", "type": "address"},
        {"indexed": False, "internalType": "bool", "name": "receiveAToken", "type": "bool"},
    ],
    "name": "LiquidationCall",
    "type": "event",
}

# Signature: LiquidationCall(address,address,address,uint256,uint256,address,bool)
EVENT_SIG = "LiquidationCall(address,address,address,uint256,uint256,address,bool)"
TOPIC0 = keccak(text=EVENT_SIG).hex()


def _to_int(x: Any) -> int:
    if isinstance(x, int):
        return x
    if isinstance(x, str) and x.startswith("0x"):
        return int(x, 16)
    return int(x)


class SparkLendLiquidationAdapter(LiquidationAdapter):
    """
    Liquidation adapter for SparkLend on Ethereum.
    Uses the PoolAddressesProvider (registry) to resolve the Pool,
    then scans for LiquidationCall events on the Pool.
    """

    protocol = "sparklend"
    version = "v1"

    def resolve_market(self) -> Dict[str, Any]:
        """
        Use the AddressesProvider (registry) to get the Pool address.
        Expects config["registry"] to be the SparkLend PoolAddressesProvider.
        """
        registry = self.config["registry"]
        provider = self.web3.eth.contract(
            address=self.web3.to_checksum_address(registry),
            abi=ADDRESSES_PROVIDER_ABI,
        )
        pool_addr = provider.functions.getPool().call()
        pool_addr = self.web3.to_checksum_address(pool_addr)
        return {"pool": pool_addr}

    def fetch_events(
        self,
        market: Dict[str, Any],
        from_block: int,
        to_block: int,
        chunk: int = 10,
    ) -> Iterable[Dict[str, Any]]:
        """
        Scan LiquidationCall logs on the Pool between from_block and to_block.
        Yields raw log dicts suitable for normalize().
        """
        pool = market["pool"]

        start = from_block
        while start <= to_block:
            end = min(start + chunk - 1, to_block)

            filter_params = {
                "fromBlock": start,
                "toBlock": end,
                "address": pool,
                "topics": [TOPIC0],
            }

            logs: List[Dict[str, Any]] = self.web3.eth.get_logs(filter_params)

            for log in logs:
                yield log

            start = end + 1

    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        """
        Decode a LiquidationCall log into the unified liquidation schema.
        """
        log = dict(raw_event)

        block_number = _to_int(log["blockNumber"])
        log_index = _to_int(log["logIndex"])
        tx_hash = log["transactionHash"].hex()

        # Decode event using ABI
        decoded = get_event_data(self.web3.codec, POOL_LIQUIDATION_EVENT_ABI, log)
        args = decoded["args"]

        collateral_asset = self.web3.to_checksum_address(args["collateralAsset"])
        debt_asset = self.web3.to_checksum_address(args["debtAsset"])
        user = self.web3.to_checksum_address(args["user"])
        liquidator = self.web3.to_checksum_address(args["liquidator"])
        debt_to_cover = int(args["debtToCover"])
        liquidated_collateral = int(args["liquidatedCollateralAmount"])
        receive_a_token = bool(args["receiveAToken"])

        ts = self.get_block_timestamp(block_number)

        extra = {
            "receive_a_token": receive_a_token,
            "usd_value": None,  # pricing layer will fill this later
        }

        return self.make_liquidation_record(
            tx_hash=tx_hash,
            log_index=log_index,
            block_number=block_number,
            timestamp=ts,
            borrower=user,
            liquidator=liquidator,
            repay_asset=debt_asset,
            repay_amount=str(debt_to_cover),
            collateral_asset=collateral_asset,
            collateral_amount=str(liquidated_collateral),
            extra=extra,
        )