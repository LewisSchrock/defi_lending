from typing import Any, Dict, List, Set

from web3 import Web3


# --- Minimal ABIs ---------------------------------------------------------

# Moolah TVL ABI: we only need idToMarketParams + market
MOOLAH_TVL_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "id", "type": "bytes32"},
        ],
        "name": "idToMarketParams",
        "outputs": [
            {
                "components": [
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
                "internalType": "struct MarketParams",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "id", "type": "bytes32"},
        ],
        "name": "market",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "uint128",
                        "name": "totalSupplyAssets",
                        "type": "uint128",
                    },
                    {
                        "internalType": "uint128",
                        "name": "totalSupplyShares",
                        "type": "uint128",
                    },
                    {
                        "internalType": "uint128",
                        "name": "totalBorrowAssets",
                        "type": "uint128",
                    },
                    {
                        "internalType": "uint128",
                        "name": "totalBorrowShares",
                        "type": "uint128",
                    },
                    {
                        "internalType": "uint128",
                        "name": "lastUpdate",
                        "type": "uint128",
                    },
                    {
                        "internalType": "uint128",
                        "name": "fee",
                        "type": "uint128",
                    },
                ],
                "internalType": "struct Market",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# Vault ABI: enough to walk withdrawQueue + get totalAssets if we want it
VAULT_ABI = [
    {
        "inputs": [],
        "name": "withdrawQueueLength",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "withdrawQueue",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Minimal ERC20 ABI for metadata
ERC20_MIN_ABI = [
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


class ListaMoolahTVLAdapter:
    """
    TVL adapter for Lista Lending (Moolah) on BNB.

    Discovery flow:

      1. CSU config provides a list of vault addresses under `vaults: [...]`.
      2. For each vault:
           - call withdrawQueueLength()
           - for i in [0, n-1]: withdrawQueue(i) -> bytes32 market Id
      3. Deduplicate market Ids across all vaults.
      4. For each Id:
           - idToMarketParams(Id) -> loanToken, collateralToken, oracle, irm, lltv
           - market(Id) -> totalSupplyAssets, totalBorrowAssets, etc.
      5. Emit one row per (protocol, chain, market_id).

    We do NOT attempt to aggregate across vaults here; this is a market-level
    snapshot. Vault-level accounting (how much each vault allocates to each
    market) is a separate layer.
    """

    protocol: str = "lista"
    version: str = "v1"

    def __init__(
        self,
        web3: Web3,
        chain: str,
        config: Dict[str, Any],
        outputs_dir: str,
    ) -> None:
        self.web3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir

        # Moolah proxy (EIP-1967 Transparent Proxy)
        self.moolah_address = Web3.to_checksum_address(config["registry"])
        self._moolah = self.web3.eth.contract(
            address=self.moolah_address,
            abi=MOOLAH_TVL_ABI,
        )

        self._erc20_meta: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def resolve_market(self) -> Dict[str, Any]:
        """
        Use the configured Lista vaults to discover all referenced market Ids.

        CSU config must supply:

          lista_lending_binance:
            ...
            vaults:
              - "0x834e8641d7422fe7c19a56d05516ed877b3d01e0"
              - "0x3036929665c69358fc092ee726448ed9c096014f"
              ...

        Returns:
          {
            "moolah": <moolah_address>,
            "vaults": [<vault addresses>],
            "market_ids": [<bytes32 Ids>],
          }
        """
        raw_vaults = self.config.get("vaults", []) or []
        vault_addrs: List[str] = []
        for v in raw_vaults:
            if isinstance(v, str) and v.startswith("0x") and len(v) == 42:
                vault_addrs.append(Web3.to_checksum_address(v))

        market_ids: Set[bytes] = set()

        for vaddr in vault_addrs:
            vault = self.web3.eth.contract(address=vaddr, abi=VAULT_ABI)
            try:
                qlen = vault.functions.withdrawQueueLength().call()
            except Exception:
                # If a vault doesn't conform (or proxy issue), just skip it
                continue

            for i in range(int(qlen)):
                try:
                    mid = vault.functions.withdrawQueue(i).call()
                except Exception:
                    continue

                # mid is bytes32; store raw bytes in the set for dedupe
                if isinstance(mid, (bytes, bytearray)) and len(mid) == 32:
                    market_ids.add(bytes(mid))

        # Convert bytes -> 0x hex for nicer printing / JSON later
        market_ids_hex = ["0x" + mid.hex() for mid in sorted(market_ids)]

        return {
            "moolah": self.moolah_address,
            "vaults": vault_addrs,
            "market_ids": market_ids_hex,
        }

    def get_tvl_raw(
        self,
        market: Dict[str, Any],
        block_number: int,
    ) -> List[Dict[str, Any]]:
        """
        Pull MarketParams + Market state for each discovered market Id.

        Returns a list of dicts, one per market Id.
        """
        rows: List[Dict[str, Any]] = []
        ids: List[str] = market.get("market_ids", [])

        for mid_hex in ids:
            try:
                # Web3 can accept a 0x-hex string as bytes32
                params = self._moolah.functions.idToMarketParams(mid_hex).call(
                    block_identifier=block_number
                )
                state = self._moolah.functions.market(mid_hex).call(
                    block_identifier=block_number
                )
            except Exception:
                # Bad id for this deployment, or proxy wiring issue
                continue

            # Unpack MarketParams
            loan_token = Web3.to_checksum_address(params[0])
            collateral_token = Web3.to_checksum_address(params[1])
            oracle = params[2]
            irm = params[3]
            lltv = int(params[4])

            # Unpack Market
            (
                total_supply_assets,
                total_supply_shares,
                total_borrow_assets,
                total_borrow_shares,
                last_update,
                fee,
            ) = state

            loan_meta = self._get_erc20_meta(loan_token)
            collateral_meta = self._get_erc20_meta(collateral_token)

            tvl_assets = int(total_supply_assets) - int(total_borrow_assets)

            row: Dict[str, Any] = {
                "protocol": self.protocol,
                "version": self.version,
                "chain": self.chain,
                "block_number": int(block_number),
                "moolah": self.moolah_address,
                "market_id": mid_hex,
                # Market params
                "loan_token": loan_token,
                "loan_symbol": loan_meta.get("symbol"),
                "loan_decimals": loan_meta.get("decimals"),
                "collateral_token": collateral_token,
                "collateral_symbol": collateral_meta.get("symbol"),
                "collateral_decimals": collateral_meta.get("decimals"),
                "oracle": oracle,
                "irm": irm,
                "lltv": lltv,
                # Market state
                "total_supply_assets": int(total_supply_assets),
                "total_supply_shares": int(total_supply_shares),
                "total_borrow_assets": int(total_borrow_assets),
                "total_borrow_shares": int(total_borrow_shares),
                "last_update": int(last_update),
                "fee": int(fee),
                # Simple net TVL in loan-token units
                "tvl_assets": tvl_assets,
            }

            rows.append(row)

        return rows

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_erc20_meta(self, token_addr: str) -> Dict[str, Any]:
        """
        Fetch and cache ERC-20 symbol/decimals for the given token.
        """
        if token_addr == "0x0000000000000000000000000000000000000000":
            return {"symbol": None, "decimals": None}

        token_addr = Web3.to_checksum_address(token_addr)
        if token_addr in self._erc20_meta:
            return self._erc20_meta[token_addr]

        contract = self.web3.eth.contract(address=token_addr, abi=ERC20_MIN_ABI)

        symbol = None
        decimals = None

        try:
            symbol = contract.functions.symbol().call()
        except Exception:
            pass

        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            pass

        meta = {"symbol": symbol, "decimals": decimals}
        self._erc20_meta[token_addr] = meta
        return meta