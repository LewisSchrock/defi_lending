from typing import Dict, Any, Iterable, List
from web3 import Web3
from .base import LiquidationAdapter


# Minimal Venus Comptroller ABI: we only need getAllMarkets()
VENUS_COMPTROLLER_ABI = [
    {
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [
            {
                "internalType": "address[]",
                "name": "",
                "type": "address[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# vToken ABI with the LiquidateBorrow event and nothing extra
VENUS_VTOKEN_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "liquidator", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "borrower", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "repayAmount", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "vTokenCollateral", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "seizeTokens", "type": "uint256"},
        ],
        "name": "LiquidateBorrow",
        "type": "event",
    },
]

# Precomputed topic0 for LiquidateBorrow(address,address,uint256,address,uint256)
LIQUIDATE_BORROW_TOPIC = Web3.keccak(
    text="LiquidateBorrow(address,address,uint256,address,uint256)"
).hex()


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


class VenusLiquidationAdapter(LiquidationAdapter):
    """
    Liquidation adapter for Venus Core Pool (BNB Chain), Compound-style.

    Expects config to provide:
      - rpc: BNB Chain RPC URL
      - registry: Unitroller/Comptroller address for the core pool
    """

    protocol = "venus"
    version = "core"

    def resolve_market(self) -> Dict[str, Any]:
        """
        Use the Venus Comptroller/Unitroller (registry) to discover all vTokens.

        Returns
        -------
        dict with keys:
          - comptroller: registry address
          - markets: list[str] of vToken addresses
        """
        registry_addr = self.config["registry"]
        w3: Web3 = self.web3

        comptroller = w3.eth.contract(
            address=w3.to_checksum_address(registry_addr),
            abi=VENUS_COMPTROLLER_ABI,
        )

        vtoken_addrs: List[str] = _safe(
            lambda: comptroller.functions.getAllMarkets().call(), []
        ) or []

        vtoken_addrs = [w3.to_checksum_address(a) for a in vtoken_addrs]

        return {
            "comptroller": w3.to_checksum_address(registry_addr),
            "markets": vtoken_addrs,
        }

    def fetch_events(self, market, from_block, to_block):
        """Fetch LiquidateBorrow logs across all vTokens for [from_block, to_block].

        Uses per-address queries with integer block numbers, mirroring the
        behavior that works for other Compound-style adapters.
        """
        w3 = self.web3
        raw_addrs = market["markets"]

        # Sanitize vToken addresses
        vtoken_addrs = [
            Web3.to_checksum_address(a)
            for a in raw_addrs
            if isinstance(a, str) and a.startswith("0x") and len(a) == 42
        ]

        if not vtoken_addrs:
            return []

        fb = int(from_block)
        tb = int(to_block)

        all_logs = []
        for addr in vtoken_addrs:
            try:
                logs = w3.eth.get_logs(
                    {
                        "fromBlock": fb,
                        "toBlock": tb,
                        "address": addr,
                        "topics": [LIQUIDATE_BORROW_TOPIC],
                    }
                )
            except Exception:
                # Skip bad ranges or transient RPC errors
                continue

            all_logs.extend(logs)

        return all_logs

    def normalize(self, raw_event: Any) -> Dict[str, Any]:
        """
        Decode a LiquidateBorrow log into a standardized dict.

        Output schema (all ints are Python ints):

            {
                'protocol': 'venus',
                'version': 'core',
                'chain': self.chain,
                'event_name': 'LiquidateBorrow',
                'tx_hash': str,
                'log_index': int,
                'block_number': int,
                'block_timestamp': int,
                'market': vToken_address,
                'liquidator': address,
                'borrower': address,
                'repay_amount': int,
                'vtoken_collateral': address,
                'seize_tokens': int,
            }
        """
        w3: Web3 = self.web3

        # Bind a minimal contract at the emitting vToken so we can use the event ABI
        vtoken_addr = raw_event["address"]
        vtoken = w3.eth.contract(address=vtoken_addr, abi=VENUS_VTOKEN_ABI)

        decoded = vtoken.events.LiquidateBorrow().process_log(raw_event)

        tx_hash = decoded["transactionHash"].hex()
        block_number = decoded["blockNumber"]
        log_index = decoded["logIndex"]

        # This is one extra RPC per event; you can memoize or strip it out later if needed
        block = w3.eth.get_block(block_number)
        block_timestamp = block["timestamp"]

        args = decoded["args"]

        return {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,
            "event_name": "LiquidateBorrow",
            "tx_hash": tx_hash,
            "log_index": log_index,
            "block_number": block_number,
            "block_timestamp": int(block_timestamp),
            "market": vtoken_addr,
            "liquidator": args["liquidator"],
            "borrower": args["borrower"],
            "repay_amount": int(args["repayAmount"]),
            "vtoken_collateral": args["vTokenCollateral"],
            "seize_tokens": int(args["seizeTokens"]),
        }