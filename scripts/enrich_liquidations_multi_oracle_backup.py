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

def process_chain(chain: str, dry_run: bool = False) -> Dict:
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
    price_cache: Dict[str, Optional[int]] = {}  # "protocol|addr|block" -> price
    price_cache_file.parent.mkdir(parents=True, exist_ok=True)
    if price_cache_file.exists():
        try:
            with open(price_cache_file) as f:
                price_cache = json.load(f)
            print(f"  Loaded {len(price_cache):,} prices from cache")
        except:
            print(f"  Warning: Could not load price cache, starting fresh")
            price_cache = {}

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

    for i, event in enumerate(events):
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
    args = parser.parse_args()

    print("=" * 60)
    print("MULTI-PROTOCOL LIQUIDATION ENRICHMENT")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    if args.chain == "all":
        chains = [d.name for d in INPUT_DIR.iterdir() if d.is_dir() and (d / "events.jsonl").exists()]
    else:
        chains = [args.chain]

    results = []
    for chain in chains:
        result = process_chain(chain, args.dry_run)
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
