from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, Iterator, List, Optional

from web3 import Web3


# -----------------------------
# Minimal ABIs (Aave v3-style)
# -----------------------------

POOL_ADDRESSES_PROVIDER_ABI_MIN = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getPoolDataProvider",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

POOL_ABI_MIN = [
    {
        "inputs": [],
        "name": "getReservesList",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

DATA_PROVIDER_ABI_MIN = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveTokensAddresses",
        "outputs": [
            {"internalType": "address", "name": "aTokenAddress", "type": "address"},
            {"internalType": "address", "name": "stableDebtTokenAddress", "type": "address"},
            {"internalType": "address", "name": "variableDebtTokenAddress", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

ERC20_ABI_MIN = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass
class TydroReserveTVL:
    """Token-unit TVL primitives for one reserve (underlying asset)."""

    underlying: str
    underlying_decimals: int
    a_token: str
    stable_debt_token: str
    variable_debt_token: str
    supply_underlying: Decimal
    borrows_underlying: Decimal


class TydroTVLAdapter:
    """TVL adapter for Tydro (Aave v3-style) on Ink.

    Strategy:
      - Resolve Pool (+ optionally DataProvider) from PoolAddressesProvider.
      - Enumerate reserves via Pool.getReservesList().
      - For each reserve, get aToken + debt token addresses from (Protocol)DataProvider.
      - Supply (token units) = aToken.totalSupply / 10^underlying_decimals
      - Borrows (token units) = (stableDebt.totalSupply + variableDebt.totalSupply) / 10^underlying_decimals

    Notes:
      - This returns token-unit quantities only (no USD). You can price later via your pricing cache.
      - We do NOT guess decimals: we call underlying.decimals() every time.
    """

    def __init__(
        self,
        web3: Web3,
        chain: str,
        config: Dict,
        outputs_dir: str,
        protocol: str = "tydro",
        version: str = "v3",
    ):
        self.w3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir
        self.protocol = protocol
        self.version = version

    # -----------------------------
    # Address resolution
    # -----------------------------

    def resolve_market(self) -> Dict[str, str]:
        """Resolve core addresses for this CSU."""

        # Prefer address provider, since it is upgrade-safe.
        provider = self.config.get("pool_addresses_provider") or self.config.get("PoolAddressesProvider")
        if not provider:
            raise KeyError(
                "Missing `pool_addresses_provider` in CSU config (or `PoolAddressesProvider`). "
                "Provide the PoolAddressesProvider address from the Tydro deployments table."
            )

        provider = Web3.to_checksum_address(provider)
        provider_contract = self.w3.eth.contract(address=provider, abi=POOL_ADDRESSES_PROVIDER_ABI_MIN)

        pool = provider_contract.functions.getPool().call()
        pool = Web3.to_checksum_address(pool)

        # Data provider: either explicitly configured or resolved from provider.
        data_provider = self.config.get("protocol_data_provider") or self.config.get("TydroProtocolDataProvider")
        if data_provider:
            data_provider = Web3.to_checksum_address(data_provider)
        else:
            try:
                data_provider = provider_contract.functions.getPoolDataProvider().call()
                data_provider = Web3.to_checksum_address(data_provider)
            except Exception:
                data_provider = None

        return {
            "addresses_provider": provider,
            "pool": pool,
            "data_provider": data_provider or "0x0000000000000000000000000000000000000000",
        }

    def _get_reserves_list(self, pool: str) -> List[str]:
        pool_contract = self.w3.eth.contract(address=Web3.to_checksum_address(pool), abi=POOL_ABI_MIN)
        reserves = pool_contract.functions.getReservesList().call()
        return [Web3.to_checksum_address(x) for x in reserves]

    def _get_reserve_tokens(self, data_provider: str, underlying: str) -> Dict[str, str]:
        dp = self.w3.eth.contract(address=Web3.to_checksum_address(data_provider), abi=DATA_PROVIDER_ABI_MIN)
        a_token, stable_debt, variable_debt = dp.functions.getReserveTokensAddresses(
            Web3.to_checksum_address(underlying)
        ).call()
        return {
            "a_token": Web3.to_checksum_address(a_token),
            "stable_debt": Web3.to_checksum_address(stable_debt),
            "variable_debt": Web3.to_checksum_address(variable_debt),
        }

    def _erc20_decimals(self, token: str) -> int:
        t = self.w3.eth.contract(address=Web3.to_checksum_address(token), abi=ERC20_ABI_MIN)
        return int(t.functions.decimals().call())

    def _erc20_total_supply(self, token: str) -> int:
        t = self.w3.eth.contract(address=Web3.to_checksum_address(token), abi=ERC20_ABI_MIN)
        return int(t.functions.totalSupply().call())

    def _is_contract(self, addr: str) -> bool:
        a = Web3.to_checksum_address(addr)
        if a.lower() == "0x0000000000000000000000000000000000000000":
            return False
        try:
            code = self.w3.eth.get_code(a)
            return bool(code) and code != b"\x00" and len(code) > 0
        except Exception:
            return False

    def _safe_total_supply(self, token: str) -> int:
        if not self._is_contract(token):
            return 0
        try:
            return self._erc20_total_supply(token)
        except Exception:
            return 0

    # -----------------------------
    # Public API
    # -----------------------------

    def iter_reserve_tvl(self) -> Iterator[Dict]:
        """Yield one record per reserve with token-unit supply/borrow metrics."""

        market = self.resolve_market()
        pool = market["pool"]
        data_provider = market["data_provider"]

        if not data_provider or data_provider.lower() == "0x0000000000000000000000000000000000000000":
            raise RuntimeError(
                "Could not resolve Tydro ProtocolDataProvider. Provide `protocol_data_provider` "
                "(aka TydroProtocolDataProvider) in the CSU YAML."
            )

        reserves = self._get_reserves_list(pool)

        for underlying in reserves:
            # Underlying decimals are required to express token units.
            u_dec = self._erc20_decimals(underlying)

            toks = self._get_reserve_tokens(data_provider, underlying)
            a_token = toks["a_token"]
            stable_debt = toks["stable_debt"]
            variable_debt = toks["variable_debt"]

            # aToken must exist for any listed reserve; if it's missing, skip.
            if not self._is_contract(a_token):
                continue

            a_supply_raw = self._safe_total_supply(a_token)
            sd_supply_raw = self._safe_total_supply(stable_debt)
            vd_supply_raw = self._safe_total_supply(variable_debt)

            denom = Decimal(10) ** Decimal(u_dec)
            supply_underlying = Decimal(a_supply_raw) / denom
            borrows_underlying = (Decimal(sd_supply_raw) + Decimal(vd_supply_raw)) / denom

            yield {
                "protocol": self.protocol,
                "version": self.version,
                "chain": self.chain,
                "market": pool,
                "underlying": underlying,
                "underlying_decimals": u_dec,
                "a_token": a_token,
                "stable_debt_token": stable_debt,
                "variable_debt_token": variable_debt,
                "supply_underlying": str(supply_underlying),
                "borrows_underlying": str(borrows_underlying),
            }

    def get_tvl_rows(self) -> List[Dict]:
        """Materialize `iter_reserve_tvl()` into a list."""
        return list(self.iter_reserve_tvl())
