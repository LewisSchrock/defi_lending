# tvl/adapters/euler_v2.py

from typing import Dict, Any, List
from web3 import Web3


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


# Minimal factory ABI for on-chain vault discovery (optional)
EULER_EVAULT_FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "creator",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "asset",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "dToken",
                "type": "address",
            },
        ],
        "name": "EVaultCreated",
        "type": "event",
    },
]

# topic0 for EVaultCreated(address,address,address)
EULER_EVAULT_CREATED_TOPIC = Web3.keccak(
    text="EVaultCreated(address,address,address)"
).hex()


# Minimal EVault ABI for TVL primitives
EULER_EVAULT_ABI = [
    # ERC-20-ish metadata for vault token
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    # Underlying asset
    {
        "inputs": [],
        "name": "asset",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    # Core TVL primitives
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalBorrows",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "cash",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "accumulatedFeesAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Minimal ERC-20 ABI for underlying token metadata
ERC20_METADATA_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class EulerV2TVLAdapter:
    """
    TVL adapter for Euler v2 (EVault architecture).

    Expected config keys (CSU-level):
      - rpc: EVM RPC URL
      - chain: chain slug (e.g. "ethereum")
      - outputs_dir: output path for downstream use

    Vault discovery:
      - If config["vaults"] is present: treat it as a static list of vault addresses.
      - Else, if config["factory"] and config["factory_start_block"] are present:
          - scan EVaultCreated events emitted by the factory
          - collect (vault, underlying) pairs from logs

    Per-vault snapshot:
      - Read TVL primitives from EVault:
          symbol, decimals, asset, totalAssets, totalBorrows, cash, accumulatedFeesAssets
      - Read metadata from underlying ERC-20:
          symbol, decimals
      - Emit a dict with all primitives plus block_number / block_timestamp.
    """

    protocol = "euler"
    version = "v2"

    def __init__(self, web3: Web3, chain: str, config: Dict[str, Any], outputs_dir: str):
        self.web3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir

    # ---------- market discovery ----------

    def resolve_market(self) -> Dict[str, Any]:
        """
        Resolve the set of EVaults to query for TVL.

        Returns
        -------
        dict with keys:
          - vaults: list of vault addresses (checksummed)
          - underlying_by_vault: dict[vault] -> underlying asset address
        """
        w3 = self.web3

        # Branch 1: static list from config
        raw_vaults = self.config.get("vaults")
        if raw_vaults:
            vaults = [
                w3.to_checksum_address(v)
                for v in raw_vaults
                if isinstance(v, str) and v.startswith("0x") and len(v) == 42
            ]

            # We can fetch underlying lazily later; just return vault list
            return {
                "vaults": vaults,
                "underlying_by_vault": {},  # will be populated lazily
            }

        # Branch 2: dynamic discovery via EVaultCreated events from factory
        factory_addr = self.config.get("factory")
        start_block = self.config.get("factory_start_block")

        if not factory_addr or start_block is None:
            # Nothing we can do; caller should have provided vaults.
            return {"vaults": [], "underlying_by_vault": {}}

        factory = w3.eth.contract(
            address=w3.to_checksum_address(factory_addr),
            abi=EULER_EVAULT_FACTORY_ABI,
        )

        latest = w3.eth.block_number
        fb = int(start_block)
        tb = int(latest)

        # NOTE: no tiny-windowing here; factory logs are relatively sparse.
        # If this ever hits provider limits you can window this like liquidations.
        logs = _safe(
            lambda: w3.eth.get_logs(
                {
                    "fromBlock": fb,
                    "toBlock": tb,
                    "address": w3.to_checksum_address(factory_addr),
                    "topics": [EULER_EVAULT_CREATED_TOPIC],
                }
            ),
            default=[],
        ) or []

        vaults: List[str] = []
        underlying_by_vault: Dict[str, str] = {}

        for log in logs:
            try:
                decoded = factory.events.EVaultCreated().process_log(log)
            except Exception:
                continue

            args = decoded["args"]
            vault_addr = w3.to_checksum_address(args["dToken"])
            asset_addr = w3.to_checksum_address(args["asset"])

            vaults.append(vault_addr)
            underlying_by_vault[vault_addr] = asset_addr

        # Deduplicate vaults
        vaults = list(dict.fromkeys(vaults))

        return {"vaults": vaults, "underlying_by_vault": underlying_by_vault}

    # ---------- TVL snapshot ----------

    def get_tvl_raw(self, market: Dict[str, Any], block_number: int) -> List[Dict[str, Any]]:
        """
        Snapshot TVL primitives for all vaults at a given block.

        Parameters
        ----------
        market : dict
            Output of resolve_market(), containing 'vaults' and optionally 'underlying_by_vault'.
        block_number : int
            Block height at which to read state.

        Returns
        -------
        list of dicts, one per vault, with TVL primitives.
        """
        w3 = self.web3
        vaults: List[str] = market.get("vaults", [])
        underlying_by_vault: Dict[str, str] = market.get("underlying_by_vault", {})

        if not vaults:
            return []

        block = w3.eth.get_block(block_number)
        ts = int(block["timestamp"])

        rows: List[Dict[str, Any]] = []

        for vault_addr in vaults:
            vault_addr = w3.to_checksum_address(vault_addr)
            vault = w3.eth.contract(address=vault_addr, abi=EULER_EVAULT_ABI)

            # Vault metadata
            vault_symbol = _safe(lambda: vault.functions.symbol().call(), "")
            vault_decimals = _safe(lambda: vault.functions.decimals().call(), 18)

            # Underlying address: from precomputed mapping, or from vault.asset()
            underlying_addr = underlying_by_vault.get(vault_addr)
            if not underlying_addr:
                underlying_addr = _safe(
                    lambda: vault.functions.asset().call(), "0x0000000000000000000000000000000000000000"
                )
            try:
                underlying_addr = w3.to_checksum_address(underlying_addr)
            except Exception:
                # Leave as is if it's zero or invalid
                pass

            # Underlying metadata
            underlying_symbol = ""
            underlying_decimals = 18
            if underlying_addr and underlying_addr != "0x0000000000000000000000000000000000000000":
                underlying = w3.eth.contract(
                    address=underlying_addr,
                    abi=ERC20_METADATA_ABI,
                )
                underlying_symbol = _safe(lambda: underlying.functions.symbol().call(), "")
                underlying_decimals = _safe(lambda: underlying.functions.decimals().call(), 18)

            # TVL primitives
            total_assets = _safe(
                lambda: vault.functions.totalAssets().call(block_identifier=block_number), 0
            )
            total_borrows = _safe(
                lambda: vault.functions.totalBorrows().call(block_identifier=block_number), 0
            )
            cash = _safe(
                lambda: vault.functions.cash().call(block_identifier=block_number), 0
            )
            acc_fees = _safe(
                lambda: vault.functions.accumulatedFeesAssets().call(block_identifier=block_number), 0
            )

            row = {
                "protocol": self.protocol,
                "version": self.version,
                "chain": self.chain,
                "vault": vault_addr,
                "vault_symbol": vault_symbol,
                "vault_decimals": int(vault_decimals),
                "underlying": underlying_addr,
                "underlying_symbol": underlying_symbol,
                "underlying_decimals": int(underlying_decimals),
                "total_assets": int(total_assets),
                "total_borrows": int(total_borrows),
                "cash": int(cash),
                "accumulated_fees_assets": int(acc_fees),
                "block_number": int(block_number),
                "block_timestamp": ts,
            }

            rows.append(row)

        return rows