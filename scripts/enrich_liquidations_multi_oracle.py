#!/usr/bin/env python3
"""
Enrich Liquidation Events with USD Values - Multi-Protocol Oracle Support

Supports:
- Aave V3: PoolAddressesProvider.getPriceOracle() -> getAssetPrice()
- Compound V3: Comet.getPrice(priceFeed)
- Compound V2 / Venus / Benqi: Comptroller.oracle() -> getUnderlyingPrice()

Usage:
    python scripts/enrich_liquidations_multi_oracle.py --chain ethereum
    python scripts/enrich_liquidations_multi_oracle.py --chain all
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dotenv import load_dotenv

load_dotenv()

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, BadFunctionCallOutput
except ImportError:
    print("[error] pip install web3")
    sys.exit(1)

# DefiLlama price fallback
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from adapters.prices.defillama import get_token_price_defillama, STABLECOINS as DL_STABLECOINS
    HAS_DEFILLAMA = True
except ImportError:
    HAS_DEFILLAMA = False
    def get_token_price_defillama(*a, **kw): return None

# DefiLlama chain name mapping for address-based lookups
DEFILLAMA_CHAINS = {
    "ethereum": "ethereum",
    "polygon": "polygon",
    "avalanche": "avax",
    "arbitrum": "arbitrum",
    "optimism": "optimism",
    "base": "base",
    "gnosis": "gnosis",
    "linea": "linea",
    "scroll": "scroll",
    "bsc": "bsc",
    "ink": "ink",
    "sonic": "sonic",
    "celo": "celo",
    "fantom": "fantom",
    "blast": "blast",
    "zksync": "era",
}

# Native token wrapped addresses by chain (for cETH/cAVAX/etc that have no underlying())
NATIVE_WRAPPED = {
    "ethereum": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
    "linea": "0xe5d7c2a44ffddf6b295a15c148167daaaf5cf34f",      # WETH on Linea
    "scroll": "0x5300000000000000000000000000000000000004",        # WETH on Scroll
    "avalanche": "0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7",   # WAVAX
    "arbitrum": "0x82af49447d8a07e3bd95bd0d56f35241523fbab1",    # WETH on Arbitrum
    "base": "0x4200000000000000000000000000000000000006",          # WETH on Base
    "optimism": "0x4200000000000000000000000000000000000006",      # WETH on Optimism
    "bsc": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",         # WBNB
    "polygon": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",     # WMATIC
    "sonic": "0x039e2fb66102314ce7b64ce5ce3e5183bc94ad38",        # wS (Wrapped Sonic)
    "blast": "0x4300000000000000000000000000000000000004",         # WETH on Blast
    "fantom": "0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83",      # WFTM
}

import requests as _requests
from threading import Lock as _DLLock

_dl_rate_lock = _DLLock()
_dl_last_call = 0.0
_dl_cache: Dict[str, Optional[float]] = {}  # "chain|addr|date" -> price
_dl_cache_lock = _DLLock()

def _defillama_price_by_address(chain: str, token_addr: str, date_str: str) -> Optional[float]:
    """Get historical price from DefiLlama using chain:address format.
    Thread-safe with rate limiting and date-based caching."""
    global _dl_last_call
    dl_chain = DEFILLAMA_CHAINS.get(chain)
    if not dl_chain or not token_addr:
        return None

    # Check date-based cache first (same token + date = same price)
    cache_key = f"{dl_chain}|{token_addr}|{date_str}"
    with _dl_cache_lock:
        if cache_key in _dl_cache:
            return _dl_cache[cache_key]

    try:
        # Rate limit: max 4 req/sec
        with _dl_rate_lock:
            now = time.time()
            elapsed = now - _dl_last_call
            if elapsed < 0.25:
                time.sleep(0.25 - elapsed)
            _dl_last_call = time.time()

        dt = datetime.strptime(date_str, '%Y-%m-%d')
        ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
        coin_id = f"{dl_chain}:{token_addr}"
        url = f"https://coins.llama.fi/prices/historical/{ts}/{coin_id}"
        resp = _requests.get(url, timeout=15)
        price = None
        if resp.status_code == 200:
            data = resp.json()
            coin_data = data.get("coins", {}).get(coin_id)
            if coin_data:
                price = coin_data.get("price")
        # Cache result (including None to avoid retrying)
        with _dl_cache_lock:
            _dl_cache[cache_key] = price
        return price
    except Exception:
        with _dl_cache_lock:
            _dl_cache[cache_key] = None
        return None

# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """Token bucket rate limiter for dRPC requests."""
    def __init__(self, requests_per_second=100):
        self.rate = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()
        self.lock = Lock()

    def acquire(self):
        """Acquire a token, blocking if necessary."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            # Refill tokens based on elapsed time
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return

            # Need to wait
            sleep_time = (1 - self.tokens) / self.rate

        time.sleep(sleep_time)
        with self.lock:
            self.tokens = 0

# ============================================================================
# Configuration
# ============================================================================

INPUT_DIR = Path("data/bronze/liquidations")
OUTPUT_DIR = Path("data/silver/liquidations")

# Protocol oracles by chain
PROTOCOL_ORACLES = {
    "ethereum": {
        "aave_v3": {"provider": "0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e"},
        "compound_v2": {"comptroller": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"},  # Compound V2
        "compound_v3": {
            "markets": {
                "0xc3d688B66703497DAA19211EEdff47f25384cdc3": "USDC",  # cUSDCv3
                "0xA17581A9E3356d9A858b789D68B4d866e593aE94": "WETH",  # cWETHv3
                "0x3Afdc9BCA9213A35503b077a6072F3D0d5AB0840": "USDT",  # cUSDTv3
            }
        },
        "gearbox": {"creditManager": "0x9ea7b04da02a5373317d745c1571c84aad03321d"},
    },
    "polygon": {
        "aave_v3": {"provider": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"},
        "compound_v2": {"comptroller": "0x20CA53E2395FA571798623F1cFBD11Fe2C114c24"},  # 0VIX
    },
    "avalanche": {
        "aave_v3": {"provider": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"},
        "compound_v2": {"comptroller": "0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4"},  # Benqi
    },
    "bsc": {
        "aave_v3": {"provider": "0xff75B6da14FfbbfD355Daf7a2731456b3562Ba6D"},
        "compound_v2": {"comptroller": "0xfd36e2c2a6789db23113685031d7f16329158384"},  # Venus
    },
    "arbitrum": {
        "aave_v3": {"provider": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"},
        "compound_v2": {"comptroller": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4"},  # Sonne Finance
        "compound_v3": {
            "markets": {
                "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf": "USDC",
                "0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA": "USDC.e",
                "0x6f7D514bbD4aFf3BcD1140B7344b32f063dEe486": "WETH",
            }
        },
    },
    "optimism": {
        "aave_v3": {"provider": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb"},
        "compound_v2": {"comptroller": "0x60CF091cD3f50420090480a388DA7E8bEb66f2Ec"},  # Sonne Finance
        "compound_v3": {
            "markets": {
                "0x2e44e174f7D53F0212823acC11C01A11d58c5bCB": "USDC",
            }
        },
    },
    "base": {
        "aave_v3": {"provider": "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D"},
        "compound_v2": {"comptroller": "0xfBb21d0380beE3312B33c4353c8936a0F13EF26C"},  # Moonwell
        "compound_v3": {
            "markets": {
                "0xb125E6687d4313864e53df431d5425969c15Eb2F": "USDC",
                "0x46e6b214b524310239732D51387075E0e70970bf": "WETH",
            }
        },
    },
    "gnosis": {
        "aave_v3": {"provider": "0x36616cf17557639614c1cdDb356b1B83fc0B2132"},
        # Note: Agave is Aave V2 fork, not Compound V2, so uses different oracle interface
    },
    "linea": {
        "aave_v3": {"provider": "0x89502c3731F69DDC95B65753708A07F8Cd0373F4"},
        "compound_v2": {"comptroller": "0x1b4d3b0421dDc1eB216D230Bc01527422Fb93103"},  # Mendi Finance
    },
    "scroll": {
        "aave_v3": {"provider": "0x69850D0B276776781C063771b161bd8894BCdD04"},
        "compound_v2": {"comptroller": "0xEC53c830f4444a8A56455c6836b5D2aA794289Aa", "price_scale": "1e18"},  # LayerBank
    },
    "ink": {
        "aave_v3": {"provider": "0x4172E6aAEC070ACB31aaCE343A58c93E4C70f44D"},  # Tydro (Aave V3 fork)
    },
    "sonic": {
        "aave_v3": {"provider": "0x5C2e738F6E27bCE0F7558051Bf90605dD6176900"},
    },
    "celo": {
        "aave_v3": {"provider": "0x9F7Cf9417D5251C59fE94fB9147feEe1aAd9Cea5"},
    },
    "fantom": {
        "compound_v2": {"comptroller": "0x4250A6D3BD57455d7C6821eECb6206F507576cD2"},  # Iron Bank
    },
    "blast": {
        "aave_v3": {"provider": "0xb0811a1FC9Fb9972ee683Ba04c32Cb828Bcf587B"},  # ZeroLend
        "aave_v3_pac": {"provider": "0x688B5fd3C3E3724b4De08C4BCB3A755F9b579c9a"},  # PAC Finance
    },
    "zksync": {
        "aave_v3": {"provider": "0x4f285Ea117eF0067B59853D6d16a5dE8088bA259"},  # ZeroLend
    },
}

# dRPC network slugs
DRPC_NETWORKS = {
    "ethereum": "ethereum",
    "polygon": "polygon",
    "avalanche": "avalanche",
    "arbitrum": "arbitrum",
    "optimism": "optimism",
    "base": "base",
    "gnosis": "gnosis",
    "linea": "linea",
    "scroll": "scroll",
    "bsc": "bsc",
    "ink": "ink",
    "sonic": "sonic",
    "celo": "celo",
    "fantom": "fantom",
    "blast": "blast",
    "zksync": "zksync-mainnet",
}

# Known stablecoins (assume $1.00)
STABLECOINS = {
    # USD stablecoins
    "usdc", "usdt", "dai", "frax", "lusd", "gusd", "tusd", "usdp", "busd",
    "usdc.e", "usdt.e", "dai.e", "usdbc", "mai", "gho", "crvusd", "usde",
    "pyusd", "usds", "susd", "usdcn", "usdtn", "usd1", "fdusd", "usdt0",
    "usd₮0", "usdc.eth", "usdt.eth", "usdtb", "deusd", "sdeusd", "ausd",
    "lisusd", "musd", "suusd", "syrupusdt", "dola", "wusdm", "rlusd", "susds",
    # Euro stablecoins (~$1.10, treat as $1 for simplicity)
    "eurc", "eurs", "wxdai", "ageur", "eura", "eure", "jeur", "eusde",
    # sDAI (wrapped DAI savings, ~$1.09)
    "sdai",
}

# ABIs
AAVE_PROVIDER_ABI = [
    {"inputs": [], "name": "getPriceOracle", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
]

AAVE_ORACLE_ABI = [
    {"inputs": [{"type": "address", "name": "asset"}], "name": "getAssetPrice", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]

# Compound V3 Comet ABI
COMPOUND_V3_ABI = [
    {"inputs": [{"type": "address", "name": "priceFeed"}], "name": "getPrice", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"type": "address", "name": "asset"}], "name": "getAssetInfoByAddress", "outputs": [{"components": [{"name": "offset", "type": "uint8"}, {"name": "asset", "type": "address"}, {"name": "priceFeed", "type": "address"}, {"name": "scale", "type": "uint64"}, {"name": "borrowCollateralFactor", "type": "uint64"}, {"name": "liquidateCollateralFactor", "type": "uint64"}, {"name": "liquidationFactor", "type": "uint64"}, {"name": "supplyCap", "type": "uint128"}], "type": "tuple"}], "stateMutability": "view", "type": "function"},
]

# Compound V2 / Venus / Benqi / Mendi / LayerBank ABIs
COMPTROLLER_ABI = [
    {"inputs": [], "name": "oracle", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "priceCalculator", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
]

COMPOUND_V2_ORACLE_ABI = [
    {"inputs": [{"type": "address", "name": "cToken"}], "name": "getUnderlyingPrice", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]

CTOKEN_ABI = [
    {"inputs": [], "name": "underlying", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
]

ERC20_ABI = [
    {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
]

# ============================================================================
# Helpers
# ============================================================================

def get_drpc_url(chain: str) -> Optional[str]:
    """Get dRPC URL from environment."""
    url = os.environ.get(f"DRPC_KEY_{chain.upper()}")
    # Skip placeholder URLs
    if url and ("YOUR_KEY" in url or "_KEY" in url):
        url = None
    if not url:
        url = os.environ.get("DRPC_KEY_1")
    if not url:
        url = os.environ.get("DRPC_KEY_2")
    if not url:
        url = os.environ.get("DRPC_KEY_3")
    if not url:
        return None
    if url.startswith("http"):
        return url
    network = DRPC_NETWORKS.get(chain)
    if not network:
        return None
    return f"https://lb.drpc.org/ogrpc?network={network}&dkey={url}"


def get_web3(chain: str) -> Optional[Web3]:
    """Create Web3 instance for chain."""
    rpc_url = get_drpc_url(chain)
    if not rpc_url:
        return None
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    return w3 if w3.is_connected() else None


def get_token_info(w3: Web3, token_addr: str) -> Tuple[Optional[int], Optional[str]]:
    """Get token decimals and symbol."""
    try:
        token = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
        decimals = token.functions.decimals().call()
        try:
            symbol = token.functions.symbol().call()
            if isinstance(symbol, bytes):
                symbol = symbol.decode(errors="ignore").strip()
        except:
            symbol = None
        return decimals, symbol
    except:
        return None, None


def is_stablecoin(symbol: Optional[str]) -> bool:
    """Check if token is a known stablecoin."""
    if not symbol:
        return False
    return symbol.lower().strip() in STABLECOINS


# ============================================================================
# Multi-Protocol Oracle
# ============================================================================

class MultiOracle:
    """Multi-protocol price oracle."""

    def __init__(self, w3: Web3, chain: str):
        self.w3 = w3
        self.chain = chain
        self.config = PROTOCOL_ORACLES.get(chain, {})

        # Cached oracle contracts
        self.aave_oracle = None
        self.compound_v2_oracle = None
        self.compound_v2_price_scale = None  # Custom price scale (e.g., "1e18" for LayerBank)
        self.compound_v3_markets = {}

        # Initialize oracles
        self._init_oracles()

    def _init_oracles(self):
        """Initialize protocol oracles."""
        # Aave V3
        if "aave_v3" in self.config:
            try:
                provider_addr = self.config["aave_v3"]["provider"]
                provider = self.w3.eth.contract(
                    address=Web3.to_checksum_address(provider_addr),
                    abi=AAVE_PROVIDER_ABI
                )
                oracle_addr = provider.functions.getPriceOracle().call()
                self.aave_oracle = self.w3.eth.contract(
                    address=oracle_addr,
                    abi=AAVE_ORACLE_ABI
                )
                print(f"    Aave V3 Oracle: {oracle_addr}")
            except Exception as e:
                print(f"    [warn] Aave V3 oracle init failed: {e}")

        # Compound V2 / Venus / Benqi / Mendi / LayerBank
        if "compound_v2" in self.config:
            try:
                comptroller_addr = self.config["compound_v2"]["comptroller"]
                comptroller = self.w3.eth.contract(
                    address=Web3.to_checksum_address(comptroller_addr),
                    abi=COMPTROLLER_ABI
                )
                # Try oracle() first, then priceCalculator() (LayerBank uses priceCalculator)
                oracle_addr = None
                try:
                    oracle_addr = comptroller.functions.oracle().call()
                except:
                    pass
                if not oracle_addr or oracle_addr == "0x0000000000000000000000000000000000000000":
                    try:
                        oracle_addr = comptroller.functions.priceCalculator().call()
                    except:
                        pass
                if oracle_addr and oracle_addr != "0x0000000000000000000000000000000000000000":
                    self.compound_v2_oracle = self.w3.eth.contract(
                        address=oracle_addr,
                        abi=COMPOUND_V2_ORACLE_ABI
                    )
                    # Store custom price scale if specified (e.g., LayerBank uses 1e18)
                    self.compound_v2_price_scale = self.config["compound_v2"].get("price_scale")
                    print(f"    Compound V2 Oracle: {oracle_addr}")
                else:
                    print(f"    [warn] Compound V2: No oracle found")
            except Exception as e:
                print(f"    [warn] Compound V2 oracle init failed: {e}")

        # Compound V3
        if "compound_v3" in self.config:
            for market_addr, name in self.config["compound_v3"].get("markets", {}).items():
                try:
                    self.compound_v3_markets[market_addr.lower()] = self.w3.eth.contract(
                        address=Web3.to_checksum_address(market_addr),
                        abi=COMPOUND_V3_ABI
                    )
                    print(f"    Compound V3 Market ({name}): {market_addr}")
                except Exception as e:
                    print(f"    [warn] Compound V3 market {name} init failed: {e}")

    def get_price(self, protocol: str, token_addr: str, block_num: int,
                  contract_addr: Optional[str] = None) -> Optional[int]:
        """Get price for token at block, returns price with 8 decimals."""

        if protocol == "aave_v3" and self.aave_oracle:
            return self._get_aave_price(token_addr, block_num)

        elif protocol in ("compound_v2", "benqi", "venus") and self.compound_v2_oracle:
            # For compound_v2, the collateral_asset IS the cToken
            return self._get_compound_v2_price(token_addr, block_num)

        elif protocol == "compound_v3" and contract_addr:
            return self._get_compound_v3_price(contract_addr, token_addr, block_num)

        # Fallback to Aave oracle for any token
        elif self.aave_oracle:
            return self._get_aave_price(token_addr, block_num)

        return None

    def _get_aave_price(self, token_addr: str, block_num: int) -> Optional[int]:
        """Get price from Aave oracle."""
        try:
            price = self.aave_oracle.functions.getAssetPrice(
                Web3.to_checksum_address(token_addr)
            ).call(block_identifier=block_num)
            return price  # Already in 8 decimals
        except:
            return None

    def _get_compound_v2_price(self, ctoken_addr: str, block_num: int) -> Optional[int]:
        """Get underlying price from Compound V2 oracle."""
        try:
            # getUnderlyingPrice returns price - scaling depends on protocol
            price = self.compound_v2_oracle.functions.getUnderlyingPrice(
                Web3.to_checksum_address(ctoken_addr)
            ).call(block_identifier=block_num)

            if price == 0:
                return None

            # Handle custom price scale (e.g., LayerBank uses 1e18 for all tokens)
            if self.compound_v2_price_scale == "1e18":
                # LayerBank: prices are in 1e18, convert to 8 decimals
                return price // (10 ** 10)

            # Standard Compound V2: prices scaled by 10^(36 - underlying_decimals)
            # Get underlying decimals to normalize
            try:
                ctoken = self.w3.eth.contract(
                    address=Web3.to_checksum_address(ctoken_addr),
                    abi=CTOKEN_ABI
                )
                underlying = ctoken.functions.underlying().call(block_identifier=block_num)
                underlying_decimals, _ = get_token_info(self.w3, underlying)
                if underlying_decimals is None:
                    underlying_decimals = 18  # Default
            except:
                underlying_decimals = 18

            # Price is scaled by 10^(36 - decimals), we want 10^8
            # So: price_8 = price / 10^(36 - decimals - 8) = price / 10^(28 - decimals)
            scale_factor = 10 ** (28 - underlying_decimals)
            return price // scale_factor if scale_factor > 0 else price

        except Exception as e:
            return None

    def _get_compound_v3_price(self, market_addr: str, token_addr: str, block_num: int) -> Optional[int]:
        """Get price from Compound V3 market."""
        market = self.compound_v3_markets.get(market_addr.lower())
        if not market:
            return None

        try:
            # Get asset info to find price feed
            asset_info = market.functions.getAssetInfoByAddress(
                Web3.to_checksum_address(token_addr)
            ).call(block_identifier=block_num)

            price_feed = asset_info[2]  # priceFeed address

            # Get price from feed (returns 8 decimals)
            price = market.functions.getPrice(price_feed).call(block_identifier=block_num)
            return price
        except:
            return None


# ============================================================================
# Main Processing
# ============================================================================

def process_single_event_wrapper(
    event: Dict,
    w3: Web3,
    oracle,
    token_cache: Dict,
    price_cache: Dict,
    rate_limiter: RateLimiter,
    cache_lock: Lock,
    token_lock: Lock
) -> Optional[Dict]:
    """Process a single liquidation event with rate limiting and caching."""
    key = f"{event.get('tx_hash', '')}_{event.get('log_index', 0)}"
    block_num = event.get("block_number")
    
    if not block_num:
        return None
    
    protocol = event.get("protocol", "unknown")
    contract = event.get("contract", "")
    coll_addr = event.get("collateral_asset")
    debt_addr = event.get("debt_asset")

    # Compound V2 forks: derive token addresses from cToken fields
    if protocol == "compound_v2" and not coll_addr:
        # market_token_collateral = collateral cToken, contract = debt cToken
        coll_addr = event.get("market_token_collateral")
        if not debt_addr:
            debt_addr = contract  # The contract IS the debt cToken

    # For Compound V3: use protocol-native usd_value_raw directly (8 decimals)
    # Compound V3's AbsorbDebt events don't emit individual asset addresses,
    # but provide the USD value calculated by the protocol itself
    if protocol == "compound_v3" and "usd_value_raw" in event and event["usd_value_raw"]:
        usd_value_raw = event["usd_value_raw"]
        collateral_value_usd = usd_value_raw / 1e8  # Convert from 8 decimals

        enriched = {
            **event,
            "collateral_symbol": None,
            "collateral_decimals": None,
            "collateral_price_usd": None,
            "collateral_amount": None,
            "collateral_value_usd": collateral_value_usd,
            "debt_symbol": None,
            "debt_decimals": None,
            "debt_price_usd": None,
            "debt_amount": None,
            "debt_value_usd": None,
            "_key": key,
            "_has_price": True,
        }
        return enriched

    # Morpho: resolve market_id → (loanToken, collateralToken)
    if protocol == "morpho" and not coll_addr and event.get("market_id"):
        try:
            morpho = w3.eth.contract(
                address=Web3.to_checksum_address(contract),
                abi=[{"inputs": [{"type": "bytes32"}], "name": "idToMarketParams",
                      "outputs": [{"components": [
                          {"name": "loanToken", "type": "address"},
                          {"name": "collateralToken", "type": "address"},
                          {"name": "oracle", "type": "address"},
                          {"name": "irm", "type": "address"},
                          {"name": "lltv", "type": "uint256"}
                      ], "type": "tuple"}], "stateMutability": "view", "type": "function"}]
            )
            market_id = bytes.fromhex(event["market_id"].replace("0x", ""))
            params = morpho.functions.idToMarketParams(market_id).call()
            debt_addr = params[0].lower()   # loanToken
            coll_addr = params[1].lower()   # collateralToken
        except Exception:
            pass

    # Euler V2: fix data misalignment — collector puts 'collateral' vault addr in repay_assets
    # repay_assets = collateral vault address (uint256), yield_balance = actual repay_assets
    if protocol == "euler_v2" and contract:
        raw_repay = event.get("repay_assets", 0)
        raw_yield = event.get("yield_balance", 0)
        # Extract collateral vault address from repay_assets (it's an address as uint256)
        coll_vault_hex = hex(raw_repay) if raw_repay else ""
        if len(coll_vault_hex) >= 42:  # Valid address
            coll_vault_addr = "0x" + coll_vault_hex[-40:]
            try:
                # Get collateral underlying token from the collateral vault
                coll_vault = w3.eth.contract(
                    address=Web3.to_checksum_address(coll_vault_addr),
                    abi=[{"inputs": [], "name": "asset", "outputs": [{"type": "address"}],
                          "stateMutability": "view", "type": "function"}]
                )
                coll_addr = coll_vault.functions.asset().call().lower()
            except Exception:
                pass
        # Resolve debt token from the debt vault (contract field)
        try:
            debt_vault = w3.eth.contract(
                address=Web3.to_checksum_address(contract),
                abi=[{"inputs": [], "name": "asset", "outputs": [{"type": "address"}],
                      "stateMutability": "view", "type": "function"}]
            )
            debt_addr = debt_vault.functions.asset().call().lower()
        except Exception:
            pass

    # Get token info (thread-safe)
    coll_decimals, coll_symbol = None, None
    debt_decimals, debt_symbol = None, None

    if coll_addr:
        with token_lock:
            if coll_addr not in token_cache:
                token_cache[coll_addr] = get_token_info(w3, coll_addr)
            coll_decimals, coll_symbol = token_cache[coll_addr]

    if debt_addr:
        with token_lock:
            if debt_addr not in token_cache:
                token_cache[debt_addr] = get_token_info(w3, debt_addr)
            debt_decimals, debt_symbol = token_cache[debt_addr]

    # Compound V2 forks: debt_repaid_raw is in UNDERLYING units, not cToken units.
    # Resolve underlying token to get correct decimals for USD calculation.
    # collateral_seized_raw IS in cToken units (8 dec) — use cToken decimals for that.
    if protocol == "compound_v2":
        # Resolve debt underlying decimals (repayAmount is in underlying units)
        if debt_addr:
            underlying_key = f"_underlying_{debt_addr}"
            with token_lock:
                if underlying_key not in token_cache:
                    try:
                        ct = w3.eth.contract(
                            address=Web3.to_checksum_address(debt_addr),
                            abi=CTOKEN_ABI)
                        u_addr = ct.functions.underlying().call().lower()
                        token_cache[underlying_key] = get_token_info(w3, u_addr)
                    except Exception:
                        # Could be cETH (no underlying()), use 18 decimals
                        if debt_symbol and "eth" in debt_symbol.lower():
                            token_cache[underlying_key] = (18, "ETH")
                        else:
                            token_cache[underlying_key] = (debt_decimals, debt_symbol)
                u_dec, u_sym = token_cache[underlying_key]
                if u_dec is not None:
                    debt_decimals = u_dec
                    debt_symbol = u_sym or debt_symbol
    
    # Get prices with rate limiting and caching
    # IMPORTANT: Normalize all cache keys to lowercase addresses to prevent duplicates
    coll_price = None
    debt_price = None

    if coll_addr:
        cache_key = f"{protocol}|{coll_addr.lower()}|{block_num}"
        with cache_lock:
            cached_price = price_cache.get(cache_key)

        if cached_price is not None:
            coll_price = cached_price
        else:
            if is_stablecoin(coll_symbol):
                coll_price = 10**8
            else:
                rate_limiter.acquire()
                coll_price = oracle.get_price(protocol, coll_addr, block_num, contract)

            with cache_lock:
                price_cache[cache_key] = coll_price

    if debt_addr:
        cache_key = f"{protocol}|{debt_addr.lower()}|{block_num}"
        with cache_lock:
            cached_price = price_cache.get(cache_key)

        if cached_price is not None:
            debt_price = cached_price
        else:
            if is_stablecoin(debt_symbol):
                debt_price = 10**8
            else:
                rate_limiter.acquire()
                debt_price = oracle.get_price(protocol, debt_addr, block_num, contract)

            with cache_lock:
                price_cache[cache_key] = debt_price

    # For Compound V2 forks: resolve cToken -> underlying for DefiLlama pricing
    # Use chain-specific native wrapped token addresses (not hardcoded Ethereum WETH)
    coll_underlying = None
    debt_underlying = None
    if protocol == "compound_v2":
        native_wrapped = NATIVE_WRAPPED.get(oracle.chain)
        if coll_addr and coll_price is None:
            underlying_cache_key = f"_ctoken_underlying_{coll_addr.lower()}"
            with token_lock:
                if underlying_cache_key not in token_cache:
                    try:
                        ct = w3.eth.contract(address=Web3.to_checksum_address(coll_addr), abi=CTOKEN_ABI)
                        token_cache[underlying_cache_key] = ct.functions.underlying().call().lower()
                    except Exception:
                        # Native token cToken (cETH, qiAVAX, etc.) — use chain wrapped native
                        sym_lower = (coll_symbol or "").lower()
                        if native_wrapped and any(h in sym_lower for h in ["eth", "avax", "bnb", "matic", "ftm"]):
                            token_cache[underlying_cache_key] = native_wrapped
                        else:
                            token_cache[underlying_cache_key] = None
                coll_underlying = token_cache[underlying_cache_key]
        if debt_addr and debt_price is None:
            underlying_cache_key = f"_ctoken_underlying_{debt_addr.lower()}"
            with token_lock:
                if underlying_cache_key not in token_cache:
                    try:
                        ct = w3.eth.contract(address=Web3.to_checksum_address(debt_addr), abi=CTOKEN_ABI)
                        token_cache[underlying_cache_key] = ct.functions.underlying().call().lower()
                    except Exception:
                        sym_lower = (debt_symbol or "").lower()
                        if native_wrapped and any(h in sym_lower for h in ["eth", "avax", "bnb", "matic", "ftm"]):
                            token_cache[underlying_cache_key] = native_wrapped
                        else:
                            token_cache[underlying_cache_key] = None
                debt_underlying = token_cache[underlying_cache_key]

    # DefiLlama fallback: try symbol-based, then address-based
    event_date = event.get("date")
    if event_date:
        if coll_price is None and coll_addr:
            # Try underlying symbol for cTokens first (strip prefix)
            dl_price = None
            if HAS_DEFILLAMA:
                # For cTokens, try underlying symbol (e.g. "qiAVAX" -> "AVAX", "lETH" -> "ETH")
                if protocol == "compound_v2" and coll_symbol and coll_underlying:
                    u_info = token_cache.get(coll_underlying)
                    u_sym = None
                    if isinstance(u_info, tuple) and len(u_info) == 2:
                        u_sym = u_info[1]
                    if u_sym:
                        dl_price = get_token_price_defillama(u_sym, event_date)
                if dl_price is None and coll_symbol:
                    dl_price = get_token_price_defillama(coll_symbol, event_date)
            # Fall back to address-based lookup (try underlying for cTokens first)
            if dl_price is None and coll_underlying:
                dl_price = _defillama_price_by_address(oracle.chain, coll_underlying, event_date)
            if dl_price is None:
                dl_price = _defillama_price_by_address(oracle.chain, coll_addr, event_date)
            if dl_price is not None:
                coll_price = int(dl_price * 10**8)
                with cache_lock:
                    price_cache[f"{protocol}|{coll_addr.lower()}|{block_num}"] = coll_price
        if debt_price is None and debt_addr:
            dl_price = None
            if HAS_DEFILLAMA:
                if protocol == "compound_v2" and debt_symbol and debt_underlying:
                    u_info = token_cache.get(debt_underlying)
                    u_sym = None
                    if isinstance(u_info, tuple) and len(u_info) == 2:
                        u_sym = u_info[1]
                    if u_sym:
                        dl_price = get_token_price_defillama(u_sym, event_date)
                if dl_price is None and debt_symbol:
                    dl_price = get_token_price_defillama(debt_symbol, event_date)
            if dl_price is None and debt_underlying:
                dl_price = _defillama_price_by_address(oracle.chain, debt_underlying, event_date)
            if dl_price is None:
                dl_price = _defillama_price_by_address(oracle.chain, debt_addr, event_date)
            if dl_price is not None:
                debt_price = int(dl_price * 10**8)
                with cache_lock:
                    price_cache[f"{protocol}|{debt_addr.lower()}|{block_num}"] = debt_price

    # Calculate USD — handle different amount field names per protocol
    coll_amount_raw = event.get("collateral_seized_raw") or event.get("seized_assets") or 0
    debt_amount_raw = event.get("debt_repaid_raw") or event.get("repaid_assets") or event.get("repay_amount_raw") or 0
    # Euler V2: due to collector data misalignment, yield_balance = actual debt repaid
    # Actual collateral seized amount was lost (3rd data field not read by collector)
    # We approximate collateral_usd from debt_usd * 1.05 (typical liquidation bonus)
    if protocol == "euler_v2":
        debt_amount_raw = event.get("yield_balance") or 0  # yield_balance is actually repay_assets
        coll_amount_raw = 0  # Not available due to data misalignment

    coll_usd = None
    debt_usd = None

    if coll_price and coll_decimals is not None and coll_amount_raw:
        coll_usd = (coll_amount_raw * coll_price) / (10 ** (coll_decimals + 8))

    if debt_price and debt_decimals is not None and debt_amount_raw:
        debt_usd = (debt_amount_raw * debt_price) / (10 ** (debt_decimals + 8))

    # Euler V2: approximate collateral from debt (collateral amount was lost in collector)
    if protocol == "euler_v2" and debt_usd and not coll_usd:
        coll_usd = debt_usd * 1.05  # ~5% liquidation bonus approximation

    enriched = {
        **event,
        "collateral_symbol": coll_symbol,
        "collateral_decimals": coll_decimals,
        "collateral_price_usd": coll_price / 10**8 if coll_price else None,
        "collateral_amount": coll_amount_raw / (10**coll_decimals) if coll_decimals else None,
        "collateral_value_usd": coll_usd,
        "debt_symbol": debt_symbol,
        "debt_decimals": debt_decimals,
        "debt_price_usd": debt_price / 10**8 if debt_price else None,
        "debt_amount": debt_amount_raw / (10**debt_decimals) if debt_decimals else None,
        "debt_value_usd": debt_usd,
        "_key": key,
        "_has_price": coll_usd is not None or debt_usd is not None,
    }
    
    return enriched


def process_chain(chain: str, dry_run: bool = False, workers: int = 50) -> Dict:
    """Process all liquidations for a chain with multi-protocol oracle."""
    input_file = INPUT_DIR / chain / "events.jsonl"
    output_file = OUTPUT_DIR / chain / "events_enriched.jsonl"
    checkpoint_file = OUTPUT_DIR / chain / ".checkpoint"
    price_cache_file = Path("data/reference") / f"price_cache_liquidations_{chain}.json"

    if not input_file.exists():
        return {"chain": chain, "status": "error", "error": "input not found"}

    print(f"\n{'='*60}")
    print(f"Processing {chain}")
    print(f"{'='*60}")

    w3 = get_web3(chain)
    if not w3:
        return {"chain": chain, "status": "error", "error": "no RPC connection"}

    # Initialize multi-oracle
    oracle = MultiOracle(w3, chain)

    # Load checkpoint
    processed_keys = set()
    if checkpoint_file.exists() and not dry_run:
        with open(checkpoint_file) as f:
            processed_keys = set(line.strip() for line in f)
        print(f"  Resuming from checkpoint ({len(processed_keys):,} already processed)")

    # Token cache
    token_cache: Dict[str, Tuple[int, str]] = {}

    # Load persistent price cache
    price_cache: Dict[str, Optional[int]] = {}  # "protocol|addr_lower|block" -> price
    price_cache_file.parent.mkdir(parents=True, exist_ok=True)
    if price_cache_file.exists():
        try:
            with open(price_cache_file) as f:
                raw_cache = json.load(f)
            # Normalize all cache keys to lowercase addresses.
            # If both mixed-case and lowercase keys exist, prefer the one with a non-None value.
            for k, v in raw_cache.items():
                parts = k.split("|")
                if len(parts) == 3:
                    normalized = f"{parts[0]}|{parts[1].lower()}|{parts[2]}"
                else:
                    normalized = k
                # Keep non-None values over None values
                if normalized not in price_cache or price_cache[normalized] is None:
                    price_cache[normalized] = v
            print(f"  Loaded {len(raw_cache):,} prices from cache -> {len(price_cache):,} after normalization")
        except:
            print(f"  Warning: Could not load price cache, starting fresh")
            price_cache = {}

    # Initialize rate limiter (100 requests/second for dRPC)
    rate_limiter = RateLimiter(requests_per_second=100)
    
    # Thread-safe locks
    cache_lock = Lock()
    token_lock = Lock()
    write_lock = Lock()
    
    print(f"  Using {workers} concurrent workers with 100 req/s rate limit")

    # Read events
    events = []
    with open(input_file) as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    print(f"  Total events: {len(events):,}")

    # Prepare output
    if not dry_run:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        mode = 'a' if processed_keys else 'w'
        out_f = open(output_file, mode)
        checkpoint_f = open(checkpoint_file, 'a')

    enriched_count = 0
    price_found = 0
    price_missing = 0
    
    # Filter out already processed events
    events_to_process = [e for e in events if f"{e.get('tx_hash','')}_{e.get('log_index',0)}" not in processed_keys]
    print(f"  Processing {len(events_to_process):,} new events (skipping {len(events)-len(events_to_process):,} already done)")
    
    # Process events concurrently
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all events for processing
        futures = {}
        for i, event in enumerate(events_to_process):
            future = executor.submit(
                process_single_event_wrapper,
                event, w3, oracle, token_cache, price_cache,
                rate_limiter, cache_lock, token_lock
            )
            futures[future] = i
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(futures):
            try:
                enriched = future.result()
                if enriched:
                    key = enriched.pop('_key')
                    has_price = enriched.pop('_has_price')
                    
                    if has_price:
                        price_found += 1
                    else:
                        price_missing += 1
                    
                    if not dry_run:
                        with write_lock:
                            out_f.write(json.dumps(enriched) + "\n")
                            checkpoint_f.write(key + "\n")
                            
                            # Flush and save cache periodically
                            if (completed + 1) % 1000 == 0:
                                out_f.flush()
                                checkpoint_f.flush()
                                with cache_lock:
                                    with open(price_cache_file, 'w') as cache_f:
                                        json.dump(price_cache, cache_f)
                    
                    processed_keys.add(key)
                    enriched_count += 1
                    completed += 1
                    
                    # Progress update
                    if completed % 500 == 0:
                        pct = 100 * price_found / (price_found + price_missing) if (price_found + price_missing) > 0 else 0
                        cache_size = len(price_cache)
                        print(f"  Processed {completed:,}/{len(events_to_process):,} ({pct:.1f}% priced, {cache_size:,} cached)")
                        
            except Exception as e:
                print(f"  Error processing event: {e}")
    
    # Dummy loop variable for compatibility with rest of code
    i = len(events) - 1
    for i, event in enumerate([]):  # Empty loop, all processing done above
        key = f"{event.get('tx_hash', '')}_{event.get('log_index', 0)}"

        if key in processed_keys:
            continue

        block_num = event.get("block_number")
        if not block_num:
            continue

        protocol = event.get("protocol", "unknown")
        contract = event.get("contract", "")
        coll_addr = event.get("collateral_asset")
        debt_addr = event.get("debt_asset")

        # Get token info
        coll_decimals, coll_symbol = None, None
        debt_decimals, debt_symbol = None, None

        if coll_addr:
            if coll_addr not in token_cache:
                token_cache[coll_addr] = get_token_info(w3, coll_addr)
            coll_decimals, coll_symbol = token_cache[coll_addr]

        if debt_addr:
            if debt_addr not in token_cache:
                token_cache[debt_addr] = get_token_info(w3, debt_addr)
            debt_decimals, debt_symbol = token_cache[debt_addr]

        # Get prices
        coll_price = None
        debt_price = None

        # Collateral price
        if coll_addr:
            cache_key = f"{protocol}|{coll_addr}|{block_num}"
            if cache_key not in price_cache:
                if is_stablecoin(coll_symbol):
                    price_cache[cache_key] = 10**8
                else:
                    price_cache[cache_key] = oracle.get_price(protocol, coll_addr, block_num, contract)
            coll_price = price_cache[cache_key]

        # Debt price
        if debt_addr:
            cache_key = f"{protocol}|{debt_addr}|{block_num}"
            if cache_key not in price_cache:
                if is_stablecoin(debt_symbol):
                    price_cache[cache_key] = 10**8
                else:
                    price_cache[cache_key] = oracle.get_price(protocol, debt_addr, block_num, contract)
            debt_price = price_cache[cache_key]

        # Calculate USD
        coll_amount_raw = event.get("collateral_seized_raw", 0)
        debt_amount_raw = event.get("debt_repaid_raw", 0)

        coll_usd = None
        debt_usd = None

        if coll_price and coll_decimals is not None and coll_amount_raw:
            coll_usd = (coll_amount_raw * coll_price) / (10 ** (coll_decimals + 8))

        if debt_price and debt_decimals is not None and debt_amount_raw:
            debt_usd = (debt_amount_raw * debt_price) / (10 ** (debt_decimals + 8))

        if coll_usd is not None or debt_usd is not None:
            price_found += 1
        else:
            price_missing += 1

        enriched = {
            **event,
            "collateral_symbol": coll_symbol,
            "collateral_decimals": coll_decimals,
            "collateral_price_usd": coll_price / 10**8 if coll_price else None,
            "collateral_amount": coll_amount_raw / (10**coll_decimals) if coll_decimals else None,
            "collateral_value_usd": coll_usd,
            "debt_symbol": debt_symbol,
            "debt_decimals": debt_decimals,
            "debt_price_usd": debt_price / 10**8 if debt_price else None,
            "debt_amount": debt_amount_raw / (10**debt_decimals) if debt_decimals else None,
            "debt_value_usd": debt_usd,
        }

        if not dry_run:
            out_f.write(json.dumps(enriched) + "\n")
            checkpoint_f.write(key + "\n")

            if (i + 1) % 1000 == 0:
                out_f.flush()
                checkpoint_f.flush()
                # Save price cache every 1000 events
                with open(price_cache_file, 'w') as cache_f:
                    json.dump(price_cache, cache_f)

        processed_keys.add(key)
        enriched_count += 1

        if (i + 1) % 500 == 0:
            pct = 100 * price_found / (price_found + price_missing) if (price_found + price_missing) > 0 else 0
            print(f"  Processed {i+1:,}/{len(events):,} ({pct:.1f}% priced, {len(price_cache):,} cached)")

    if not dry_run:
        out_f.close()
        checkpoint_f.close()
        # Save final price cache
        with open(price_cache_file, 'w') as cache_f:
            json.dump(price_cache, cache_f)
        print(f"  Saved {len(price_cache):,} prices to cache: {price_cache_file}")

    pct = 100 * price_found / (price_found + price_missing) if (price_found + price_missing) > 0 else 0
    print(f"  DONE: {enriched_count:,} enriched, {pct:.1f}% priced")

    return {
        "chain": chain,
        "status": "success",
        "enriched": enriched_count,
        "priced": price_found,
        "unpriced": price_missing,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chain", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workers", type=int, default=50, help="Number of concurrent workers (default: 50)")
    parser.add_argument("--force", action="store_true",
                        help="Clear checkpoint and reprocess all events from scratch (use after backfilling prices)")
    args = parser.parse_args()

    print("=" * 60)
    print("MULTI-PROTOCOL LIQUIDATION ENRICHMENT")
    print(f"Started: {datetime.now().isoformat()}")
    if args.force:
        print("MODE: FORCE REPROCESS (ignoring checkpoint)")
    print("=" * 60)

    if args.chain == "all":
        chains = [d.name for d in INPUT_DIR.iterdir() if d.is_dir() and (d / "events.jsonl").exists()]
    else:
        chains = [c.strip() for c in args.chain.split(",")]

    results = []
    for chain in chains:
        if args.force:
            # Clear checkpoint so all events are reprocessed
            checkpoint_file = OUTPUT_DIR / chain / ".checkpoint"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
                print(f"  Cleared checkpoint for {chain}")
        result = process_chain(chain, args.dry_run, workers=args.workers)
        results.append(result)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for r in results:
        if r["status"] == "success":
            pct = 100 * r["priced"] / (r["priced"] + r["unpriced"]) if (r["priced"] + r["unpriced"]) > 0 else 0
            print(f"  {r['chain']}: {r['enriched']:,} events, {pct:.1f}% priced")
        else:
            print(f"  {r['chain']}: ERROR - {r.get('error')}")


if __name__ == "__main__":
    main()
