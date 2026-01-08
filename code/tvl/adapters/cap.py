# tvl/adapters/cap.py

from typing import Dict, Any
from web3 import Web3

CAP_USDC_FR_VAULT = Web3.to_checksum_address("0x3Ed6aa32c930253fc990dE58fF882B9186cd0072")
DEBT_USDC_TOKEN   = Web3.to_checksum_address("0xfa8C6D0b95d9191B5A1D51C868Da2BDFd6C04Ff9")

# Minimal ERC20 ABI
ERC20_ABI = [
    {
        "name": "decimals",
        "inputs": [],
        "outputs": [{"type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "symbol",
        "inputs": [],
        "outputs": [{"type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "name",
        "inputs": [],
        "outputs": [{"type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "totalSupply",
        "inputs": [],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Vault ABI subset (only functions we need)
CAP_VAULT_ABI = [
    {"name": "totalAssets", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"name": "totalIdle",   "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"name": "totalDebt",   "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"name": "asset",       "inputs": [], "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"name": "decimals",    "inputs": [], "outputs": [{"type": "uint8"}],   "stateMutability": "view", "type": "function"},
    {"name": "name",        "inputs": [], "outputs": [{"type": "string"}],  "stateMutability": "view", "type": "function"},
    {"name": "symbol",      "inputs": [], "outputs": [{"type": "string"}],  "stateMutability": "view", "type": "function"},
]


class CapTVLAdapter:
    protocol = "cap"
    version = "v1"

    def __init__(self, web3: Web3, chain: str, config: Dict[str, Any], outputs_dir: str):
        self.web3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir

        self.vault_address = CAP_USDC_FR_VAULT
        self.debt_token_address = DEBT_USDC_TOKEN

        self._vault = self.web3.eth.contract(address=self.vault_address, abi=CAP_VAULT_ABI)
        self._debt_token = self.web3.eth.contract(address=self.debt_token_address, abi=ERC20_ABI)

        self._token_meta = {}   # cached metadata for underlying USDC

    # ---------------------------------------------------------
    # 1. RESOLVE MARKET
    # ---------------------------------------------------------
    def resolve_market(self) -> Dict[str, Any]:
        return {
            "vault": self.vault_address,
            "debt_token": self.debt_token_address,
        }

    # ---------------------------------------------------------
    # 2. FETCH RAW STATE
    # ---------------------------------------------------------
    def fetch_state(self, market: Dict[str, Any], block: int | None = None) -> Dict[str, Any]:
        block_id = block if block is not None else "latest"

        total_assets = self._vault.functions.totalAssets().call(block_identifier=block_id)
        total_idle   = self._vault.functions.totalIdle().call(block_identifier=block_id)
        total_debt   = self._vault.functions.totalDebt().call(block_identifier=block_id)

        debt_supply = self._debt_token.functions.totalSupply().call(block_identifier=block_id)

        # Lazy-load metadata once
        if not self._token_meta:
            try:
                asset_addr = self._vault.functions.asset().call()
                asset = self.web3.eth.contract(address=asset_addr, abi=ERC20_ABI)
                dec = asset.functions.decimals().call()
                sym = asset.functions.symbol().call()
                name = asset.functions.name().call()
            except:
                asset_addr, dec, sym, name = None, 18, "UNKNOWN", "Unknown"

            self._token_meta = {
                "underlying": asset_addr,
                "decimals": int(dec),
                "symbol": sym,
                "name": name,
            }

        return {
            "block": block_id,
            "total_assets": int(total_assets),
            "total_idle": int(total_idle),
            "total_debt_internal": int(total_debt),
            "debt_supply": int(debt_supply),
            "vault": self.vault_address,
            "debt_token": self.debt_token_address,
            "token_meta": dict(self._token_meta),
        }

    # ---------------------------------------------------------
    # 3. NORMALIZE INTO STANDARD TVL ROW
    # ---------------------------------------------------------
    def normalize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        meta = state["token_meta"]
        dec = meta.get("decimals", 18)

        return {
            "protocol": self.protocol,
            "version": self.version,
            "chain": self.chain,
            "block": state["block"],
            "vault": state["vault"],
            "debt_token": state["debt_token"],
            "underlying_token": meta.get("underlying"),
            "underlying_symbol": meta.get("symbol"),
            "underlying_name": meta.get("name"),
            "decimals": dec,
            "supplied_raw": state["total_assets"],
            "borrowed_raw": state["debt_supply"],
            "supplied": state["total_assets"] / (10 ** dec),
            "borrowed": state["debt_supply"] / (10 ** dec),
            "vault_total_idle": state["total_idle"],
            "vault_total_debt_internal": state["total_debt_internal"],
        }

    # ---------------------------------------------------------
    # 4. PUBLIC METHOD USED BY SANDBOX
    # ---------------------------------------------------------
    def get_tvl_raw(self, market: Dict[str, Any], block: int) -> list[Dict[str, Any]]:
        """
        Match Lista-style return type: a list of TVL rows.
        Cap has only one “market”, so return a list of length 1.
        """
        state = self.fetch_state(market, block)
        return [self.normalize(state)]