from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from decimal import Decimal
from web3 import Web3
from web3._utils.events import get_event_data


# Minimal ERC20 ABI for decimals/symbol
ERC20_MIN_ABI = [
    {"name": "decimals", "outputs": [{"type": "uint8"}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "symbol", "outputs": [{"type": "string"}], "inputs": [], "stateMutability": "view", "type": "function"},
]

# Comptroller minimal ABI
COMPTROLLER_MIN_ABI = [
    {"name": "getAllMarkets", "outputs": [{"type": "address[]"}], "inputs": [], "stateMutability": "view", "type": "function"},
]

# Some Comptrollers also expose allMarkets(uint256) but not getAllMarkets()
COMPTROLLER_ALT_ABI = [
    {"name": "allMarkets", "outputs": [{"type": "address"}], "inputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]

# CToken minimal ABI: decimals + underlying + LiquidateBorrow event
CTOKEN_MIN_ABI = [
    {"name": "decimals", "outputs": [{"type": "uint8"}], "inputs": [], "stateMutability": "view", "type": "function"},
    {"name": "underlying", "outputs": [{"type": "address"}], "inputs": [], "stateMutability": "view", "type": "function"},
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "address", "name": "liquidator", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "borrower", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "repayAmount", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "cTokenCollateral", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "seizeTokens", "type": "uint256"},
        ],
        "name": "LiquidateBorrow",
        "type": "event",
    },
]


def _topic0(sig: str) -> str:
    # you explicitly want the 0x prefix every time
    return "0x" + Web3.keccak(text=sig).hex()


def _scale(amount: int, decimals: int) -> Decimal:
    # keep full precision; caller can stringify/quantize if needed
    return Decimal(amount) / (Decimal(10) ** int(decimals))


class SumerLiquidationAdapter:
    """
    Compound-style liquidation adapter (Sumer):
    - markets discovered from Comptroller.getAllMarkets()
    - liquidation logs read from each cToken market address
    """

    LIQ_EVENT_SIG = "LiquidateBorrow(address,address,uint256,address,uint256)"
    LIQ_TOPIC0 = _topic0(LIQ_EVENT_SIG)

    def __init__(self, web3: Web3, chain: str, config: Dict, outputs_dir: str):
        self.web3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir
        self._decimals_cache: Dict[str, int] = {}
        self._symbol_cache: Dict[str, str] = {}

        # pre-build event decoder (ABI fragment)
        self._liq_event_abi = next(x for x in CTOKEN_MIN_ABI if x.get("type") == "event" and x.get("name") == "LiquidateBorrow")

    def _erc20(self, addr: str):
        return self.web3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_MIN_ABI)

    def _ctoken(self, addr: str):
        return self.web3.eth.contract(address=Web3.to_checksum_address(addr), abi=CTOKEN_MIN_ABI)

    def _comptroller(self, addr: str, abi: Optional[list] = None):
        return self.web3.eth.contract(
            address=Web3.to_checksum_address(addr),
            abi=abi if abi is not None else COMPTROLLER_MIN_ABI,
        )

    def _require_contract(self, addr: str, label: str) -> None:
        code = self.web3.eth.get_code(Web3.to_checksum_address(addr))
        if code in (b"", b"\x00"):
            raise ValueError(
                f"{label} address has no contract code on-chain: {addr}. "
                f"Check RPC/chain mismatch or wrong address in config."
            )

    def _decimals(self, token_addr: str) -> int:
        token_addr = Web3.to_checksum_address(token_addr)
        if token_addr in self._decimals_cache:
            return self._decimals_cache[token_addr]
        d = int(self._erc20(token_addr).functions.decimals().call())
        self._decimals_cache[token_addr] = d
        return d

    def _symbol(self, token_addr: str) -> str:
        token_addr = Web3.to_checksum_address(token_addr)
        if token_addr in self._symbol_cache:
            return self._symbol_cache[token_addr]
        try:
            s = self._erc20(token_addr).functions.symbol().call()
        except Exception:
            s = ""
        self._symbol_cache[token_addr] = s
        return s

    def get_markets(self) -> List[str]:
        # Preferred: allow config to pin markets to avoid on-chain discovery issues
        cfg_markets = self.config.get("markets")
        if isinstance(cfg_markets, list) and cfg_markets:
            return [Web3.to_checksum_address(x) for x in cfg_markets]

        comptroller_addr = self.config["comptroller"]
        self._require_contract(comptroller_addr, "Comptroller")

        try:
            c = self._comptroller(comptroller_addr)
            mkts = c.functions.getAllMarkets().call()
            return [Web3.to_checksum_address(x) for x in mkts]
        except Exception as e:
            rpc = self.config.get("rpc") or self.config.get("rpc_url") or ""
            raise ValueError(
                "Failed to call Comptroller.getAllMarkets(). "
                f"chain={self.chain} rpc={rpc} comptroller={comptroller_addr}. "
                "Most likely: wrong comptroller address for this chain, wrong RPC endpoint, "
                "or the comptroller is behind a proxy that doesn't expose this selector. "
                f"Original error: {type(e).__name__}: {e}"
            )

    def iter_liquidations(
        self,
        from_block: int,
        to_block: int,
        chunk_size: int = 5_000,
    ) -> Iterable[Dict]:
        """
        Yield decoded liquidation rows for [from_block, to_block] inclusive.
        """
        markets = self.get_markets()

        for ctoken_addr in markets:
            # borrowed market metadata (repayAmount decimals)
            ctoken = self._ctoken(ctoken_addr)
            try:
                borrowed_underlying = ctoken.functions.underlying().call()
                borrowed_underlying = Web3.to_checksum_address(borrowed_underlying)
                borrowed_underlying_dec = self._decimals(borrowed_underlying)
                borrowed_underlying_sym = self._symbol(borrowed_underlying)
            except Exception:
                # some markets can be "cETH-like" (no underlying()) — handle if needed
                borrowed_underlying = None
                borrowed_underlying_dec = None
                borrowed_underlying_sym = ""

            # scan blocks in chunks
            start = from_block
            while start <= to_block:
                end = min(start + chunk_size - 1, to_block)

                logs = self.web3.eth.get_logs(
                    {
                        "fromBlock": start,
                        "toBlock": end,
                        "address": ctoken_addr,
                        "topics": [self.LIQ_TOPIC0],
                    }
                )

                for lg in logs:
                    # decode with ABI (no indexed fields, so everything is in data)
                    decoded = get_event_data(self.web3.codec, self._liq_event_abi, lg)["args"]

                    ctoken_collateral = Web3.to_checksum_address(decoded["cTokenCollateral"])
                    collateral_ctoken_dec = int(self._ctoken(ctoken_collateral).functions.decimals().call())
                    collateral_underlying = None
                    collateral_underlying_dec = None
                    collateral_underlying_sym = ""
                    try:
                        collateral_underlying = self._ctoken(ctoken_collateral).functions.underlying().call()
                        collateral_underlying = Web3.to_checksum_address(collateral_underlying)
                        collateral_underlying_dec = self._decimals(collateral_underlying)
                        collateral_underlying_sym = self._symbol(collateral_underlying)
                    except Exception:
                        pass

                    repay_raw = int(decoded["repayAmount"])
                    seize_raw = int(decoded["seizeTokens"])

                    row = {
                        "protocol": self.config.get("protocol", "sumermoney"),
                        "chain": self.chain,
                        "comptroller": Web3.to_checksum_address(self.config["comptroller"]),
                        "ctoken_borrowed": ctoken_addr,
                        "ctoken_collateral": ctoken_collateral,
                        "liquidator": Web3.to_checksum_address(decoded["liquidator"]),
                        "borrower": Web3.to_checksum_address(decoded["borrower"]),
                        "repay_amount_raw": repay_raw,
                        "repay_amount": _scale(repay_raw, borrowed_underlying_dec) if borrowed_underlying_dec is not None else None,
                        "repay_underlying": borrowed_underlying,
                        "repay_underlying_symbol": borrowed_underlying_sym,
                        "repay_underlying_decimals": borrowed_underlying_dec,
                        "seize_tokens_raw": seize_raw,
                        "seize_tokens": _scale(seize_raw, collateral_ctoken_dec),
                        "collateral_ctoken_decimals": collateral_ctoken_dec,
                        "collateral_underlying": collateral_underlying,
                        "collateral_underlying_symbol": collateral_underlying_sym,
                        "collateral_underlying_decimals": collateral_underlying_dec,
                        "block_number": int(lg["blockNumber"]),
                        "tx_hash": lg["transactionHash"].hex(),
                        "log_index": int(lg["logIndex"]),
                    }
                    yield row

                start = end + 1

    def get_liquidation_rows(
        self,
        from_block: int,
        to_block: int,
        chunk_size: int = 5_000,
    ) -> List[Dict]:
        return list(self.iter_liquidations(from_block, to_block, chunk_size=chunk_size))