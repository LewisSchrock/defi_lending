#!/usr/bin/env python3
"""
Enrich Liquidation Events - Receipt Token Resolution

For Compound V2-style protocols (Venus, Benqi, Mendi, LayerBank), liquidation events
record the collateral as receipt tokens (vToken, qiToken, meToken, lToken).

The getUnderlyingPrice() oracle function returns the UNDERLYING asset price, but the
amount in the event is in cToken units. This script converts cToken amounts to underlying
amounts using exchangeRateStored() at the event's block.

Formula:
    underlying_amount = cToken_amount * exchangeRate / 10^(18 + underlying_decimals - 8)

Usage:
    python scripts/enrich_with_receipt_tokens.py --chain bsc
    python scripts/enrich_with_receipt_tokens.py --chain avalanche
    python scripts/enrich_with_receipt_tokens.py --chain linea
    python scripts/enrich_with_receipt_tokens.py --chain scroll
    python scripts/enrich_with_receipt_tokens.py --chain all
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

try:
    from web3 import Web3
except ImportError:
    print("[error] pip install web3")
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

INPUT_DIR = Path("data/bronze/liquidations")
OUTPUT_DIR = Path("data/silver/liquidations")

# Protocol configurations
PROTOCOLS = {
    "bsc": {
        "venus": {
            "comptroller": "0xfD36E2c2a6789Db23113685031d7F16329158384",
            "prefixes": ["v"],
        },
        "filda": {
            "comptroller": None,
            "prefixes": ["f"],
        },
        "cream": {
            "comptroller": None,
            "prefixes": ["cr"],
        },
    },
    "avalanche": {
        "benqi": {
            "comptroller": "0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4",
            "prefixes": ["qi"],
        },
    },
    "linea": {
        "mendi": {
            "comptroller": "0x1b4d3b0421dDc1eB216D230Bc01527422Fb93103",
            "prefixes": ["me"],
        },
    },
    "scroll": {
        "layerbank": {
            "comptroller": "0xEC53c830f4444a8A56455c6836b5D2aA794289Aa",
            "prefixes": ["l", "i"],
            "price_scale": "1e18",
        },
    },
    "polygon": {
        "0vix": {
            "comptroller": "0x20CA53E2395FA571798623F1cFBD11Fe2C114c24",
            "prefixes": ["o"],
        },
    },
    "arbitrum": {
        "sonne": {
            "comptroller": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
            "prefixes": ["so"],
        },
    },
    "optimism": {
        "sonne": {
            "comptroller": "0x60CF091cD3f50420090480a388DA7E8bEb66f2Ec",
            "prefixes": ["so"],
        },
    },
}

# dRPC network slugs
DRPC_NETWORKS = {
    "bsc": "bsc",
    "avalanche": "avalanche",
    "linea": "linea",
    "scroll": "scroll",
    "polygon": "polygon",
    "arbitrum": "arbitrum",
    "optimism": "optimism",
}

# Known stablecoins
STABLECOINS = {
    "usdc", "usdt", "dai", "frax", "lusd", "gusd", "tusd", "usdp", "busd",
    "usdc.e", "usdt.e", "dai.e", "fdusd", "usdt0", "usd1", "mai", "gho",
}

# Excluded receipt tokens (data quality issues)
# vTHE: Exchange rate ~1.008 (should be 0.02-0.05). On-chain contract returns
#       10.08e27 for exchangeRateStored(), resulting in 1:1 vTHE:THE conversion.
#       This produces quadrillion-token debt amounts. Root cause unclear - may be
#       inverted semantics, double-wrapped token, or broken Venus market.
#       Contract: 0x86e06eafa6a1ea631eab51de500e3d474933739f
EXCLUDED_RECEIPT_TOKENS = {
    "vTHE",
}

# Native tokens by chain
NATIVE_TOKENS = {
    "bsc": {"symbol": "BNB", "decimals": 18},
    "avalanche": {"symbol": "AVAX", "decimals": 18},
    "linea": {"symbol": "ETH", "decimals": 18},
    "scroll": {"symbol": "ETH", "decimals": 18},
    "polygon": {"symbol": "MATIC", "decimals": 18},
    "arbitrum": {"symbol": "ETH", "decimals": 18},
    "optimism": {"symbol": "ETH", "decimals": 18},
}

# ABIs
CTOKEN_ABI = [
    {"inputs": [], "name": "underlying", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "exchangeRateStored", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]

ERC20_ABI = [
    {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
]

COMPTROLLER_ABI = [
    {"inputs": [], "name": "getAllMarkets", "outputs": [{"type": "address[]"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "oracle", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "priceCalculator", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
]

ORACLE_ABI = [
    {"inputs": [{"type": "address", "name": "cToken"}], "name": "getUnderlyingPrice", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]


# ============================================================================
# Helpers
# ============================================================================

def get_drpc_url(chain: str) -> Optional[str]:
    """Get dRPC URL from environment."""
    url = os.environ.get(f"DRPC_KEY_{chain.upper()}")
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


# ============================================================================
# Receipt Token Resolver
# ============================================================================

class ReceiptTokenResolver:
    """Resolves receipt token amounts to underlying values."""

    def __init__(self, w3: Web3, chain: str):
        self.w3 = w3
        self.chain = chain
        self.config = PROTOCOLS.get(chain, {})

        # Caches
        self.underlying_cache: Dict[str, Optional[str]] = {}
        self.decimals_cache: Dict[str, int] = {}
        self.symbol_cache: Dict[str, str] = {}
        self.exchange_rate_cache: Dict[Tuple[str, int], int] = {}
        self.price_cache: Dict[Tuple[str, int], Optional[int]] = {}

        # Load markets and initialize oracles
        self.markets = set()
        self.oracles = {}
        self.price_scales = {}
        self._init_protocols()

    def _init_protocols(self):
        """Initialize protocol oracles and load markets."""
        for protocol_name, protocol_config in self.config.items():
            comptroller_addr = protocol_config.get("comptroller")
            if not comptroller_addr:
                continue

            try:
                comptroller = self.w3.eth.contract(
                    address=Web3.to_checksum_address(comptroller_addr),
                    abi=COMPTROLLER_ABI
                )

                # Load markets
                try:
                    markets = comptroller.functions.getAllMarkets().call()
                    for m in markets:
                        self.markets.add(m.lower())
                    print(f"    {protocol_name}: {len(markets)} markets")
                except:
                    pass

                # Get oracle
                oracle_addr = None
                try:
                    oracle_addr = comptroller.functions.oracle().call()
                except:
                    pass
                if not oracle_addr or oracle_addr == "0x" + "0" * 40:
                    try:
                        oracle_addr = comptroller.functions.priceCalculator().call()
                    except:
                        pass

                if oracle_addr and oracle_addr != "0x" + "0" * 40:
                    self.oracles[protocol_name] = self.w3.eth.contract(
                        address=oracle_addr,
                        abi=ORACLE_ABI
                    )
                    self.price_scales[protocol_name] = protocol_config.get("price_scale")
                    print(f"    {protocol_name} oracle: {oracle_addr}")

            except Exception as e:
                print(f"    [warn] {protocol_name} init failed: {e}")

    def is_receipt_token(self, symbol: Optional[str], address: str) -> bool:
        """Check if token is a receipt token."""
        # Check exclusion list first
        if symbol and symbol in EXCLUDED_RECEIPT_TOKENS:
            return False

        if address.lower() in self.markets:
            return True

        if symbol:
            symbol_lower = symbol.lower()
            for protocol_config in self.config.values():
                for prefix in protocol_config.get("prefixes", []):
                    if symbol_lower.startswith(prefix) and len(symbol_lower) > len(prefix):
                        # Avoid false positives like "LINK" matching "l"
                        remaining = symbol_lower[len(prefix):]
                        if remaining and remaining[0].isupper() or remaining.upper() in STABLECOINS:
                            return True
        return False

    def get_underlying(self, ctoken_addr: str, block_num: int) -> Optional[str]:
        """Get underlying asset address."""
        cache_key = ctoken_addr.lower()
        if cache_key in self.underlying_cache:
            return self.underlying_cache[cache_key]

        try:
            ctoken = self.w3.eth.contract(
                address=Web3.to_checksum_address(ctoken_addr),
                abi=CTOKEN_ABI
            )
            underlying = ctoken.functions.underlying().call(block_identifier=block_num)
            self.underlying_cache[cache_key] = underlying
            return underlying
        except:
            # Native token wrapper
            self.underlying_cache[cache_key] = None
            return None

    def get_exchange_rate(self, ctoken_addr: str, block_num: int) -> Optional[int]:
        """Get exchange rate at block."""
        cache_key = (ctoken_addr.lower(), block_num)
        if cache_key in self.exchange_rate_cache:
            return self.exchange_rate_cache[cache_key]

        try:
            ctoken = self.w3.eth.contract(
                address=Web3.to_checksum_address(ctoken_addr),
                abi=CTOKEN_ABI
            )
            rate = ctoken.functions.exchangeRateStored().call(block_identifier=block_num)
            self.exchange_rate_cache[cache_key] = rate
            return rate
        except:
            return None

    def get_token_info(self, token_addr: str) -> Tuple[Optional[int], Optional[str]]:
        """Get token decimals and symbol."""
        cache_key = token_addr.lower()
        if cache_key in self.decimals_cache:
            return self.decimals_cache[cache_key], self.symbol_cache.get(cache_key)

        try:
            token = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_addr),
                abi=ERC20_ABI
            )
            decimals = token.functions.decimals().call()
            try:
                symbol = token.functions.symbol().call()
                if isinstance(symbol, bytes):
                    symbol = symbol.decode(errors="ignore").strip()
            except:
                symbol = None

            self.decimals_cache[cache_key] = decimals
            self.symbol_cache[cache_key] = symbol
            return decimals, symbol
        except:
            return None, None

    def get_underlying_price(self, ctoken_addr: str, block_num: int) -> Optional[int]:
        """Get underlying price from oracle (8 decimals)."""
        cache_key = (ctoken_addr.lower(), block_num)
        if cache_key in self.price_cache:
            return self.price_cache[cache_key]

        for protocol_name, oracle in self.oracles.items():
            try:
                price = oracle.functions.getUnderlyingPrice(
                    Web3.to_checksum_address(ctoken_addr)
                ).call(block_identifier=block_num)

                if price == 0:
                    continue

                # Normalize to 8 decimals
                price_scale = self.price_scales.get(protocol_name)
                if price_scale == "1e18":
                    # LayerBank: all prices in 1e18
                    price_8 = price // (10 ** 10)
                else:
                    # Standard Compound V2: price scaled by 10^(36 - underlying_decimals)
                    underlying_addr = self.get_underlying(ctoken_addr, block_num)
                    if underlying_addr:
                        underlying_decimals, _ = self.get_token_info(underlying_addr)
                    else:
                        underlying_decimals = NATIVE_TOKENS.get(self.chain, {}).get("decimals", 18)
                    if underlying_decimals is None:
                        underlying_decimals = 18
                    scale_factor = 10 ** (28 - underlying_decimals)
                    price_8 = price // scale_factor if scale_factor > 0 else price

                self.price_cache[cache_key] = price_8
                return price_8

            except:
                continue

        self.price_cache[cache_key] = None
        return None

    def resolve(self, ctoken_addr: str, ctoken_amount_raw: int,
                ctoken_decimals: int, block_num: int) -> Dict:
        """Resolve receipt token to underlying value.

        Returns:
            {
                "underlying_address": str or None,
                "underlying_symbol": str or None,
                "underlying_decimals": int,
                "underlying_amount": float,
                "underlying_price_usd": float or None,
                "underlying_value_usd": float or None,
            }
        """
        result = {
            "underlying_address": None,
            "underlying_symbol": None,
            "underlying_decimals": None,
            "underlying_amount": None,
            "underlying_price_usd": None,
            "underlying_value_usd": None,
        }

        # Get exchange rate
        exchange_rate = self.get_exchange_rate(ctoken_addr, block_num)
        if not exchange_rate:
            return result

        # Get underlying
        underlying_addr = self.get_underlying(ctoken_addr, block_num)
        if underlying_addr:
            underlying_decimals, underlying_symbol = self.get_token_info(underlying_addr)
            result["underlying_address"] = underlying_addr
        else:
            # Native token
            native = NATIVE_TOKENS.get(self.chain)
            underlying_decimals = native["decimals"] if native else 18
            underlying_symbol = native["symbol"] if native else None

        if underlying_decimals is None:
            underlying_decimals = 18

        result["underlying_decimals"] = underlying_decimals
        result["underlying_symbol"] = underlying_symbol

        # Convert cToken amount to underlying
        # Compound V2/Venus exchangeRate is scaled by 10^(18 - cTokenDecimals + underlyingDecimals)
        # For cToken with 8 decimals and underlying with 18 decimals: scaled by 10^28
        # Formula: underlying = cToken_raw * exchangeRate / 10^(18 + underlyingDecimals)
        # This gives underlying in human-readable units
        mantissa = 18 + underlying_decimals
        underlying_amount = (ctoken_amount_raw * exchange_rate) / (10 ** mantissa)
        result["underlying_amount"] = underlying_amount

        # Get price
        if underlying_symbol and underlying_symbol.lower() in STABLECOINS:
            price_8 = 10 ** 8
        else:
            price_8 = self.get_underlying_price(ctoken_addr, block_num)

        if price_8:
            price_usd = price_8 / (10 ** 8)
            result["underlying_price_usd"] = price_usd
            result["underlying_value_usd"] = underlying_amount * price_usd

        return result


# ============================================================================
# Main Processing
# ============================================================================

def process_chain(chain: str, dry_run: bool = False) -> Dict:
    """Process chain with receipt token resolution."""
    input_file = INPUT_DIR / chain / "events.jsonl"
    output_file = OUTPUT_DIR / chain / "events_enriched_receipt_v2.jsonl"

    if not input_file.exists():
        return {"chain": chain, "status": "error", "error": "input not found"}

    print(f"\n{'='*60}")
    print(f"Processing {chain}")
    print(f"{'='*60}")

    w3 = get_web3(chain)
    if not w3:
        return {"chain": chain, "status": "error", "error": "no RPC connection"}

    resolver = ReceiptTokenResolver(w3, chain)

    # Read events
    events = []
    with open(input_file) as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    print(f"  Total events: {len(events):,}")

    # Stats
    total = 0
    resolved = 0
    priced = 0
    already_priced = 0

    if not dry_run:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        out_f = open(output_file, 'w')

    for i, event in enumerate(events):
        total += 1
        block_num = event.get("block_number")
        protocol = event.get("protocol", "")

        # Skip non-compound-v2 protocols (already priced correctly)
        if protocol not in ("compound_v2", "benqi", "venus"):
            if not dry_run:
                out_f.write(json.dumps(event) + "\n")
            if event.get("collateral_value_usd"):
                already_priced += 1
                priced += 1
            continue

        enriched = dict(event)

        # Check collateral
        coll_addr = event.get("collateral_asset")
        coll_symbol = event.get("collateral_symbol")
        coll_decimals = event.get("collateral_decimals")
        coll_amount_raw = event.get("collateral_seized_raw", 0)

        # Get symbol/decimals from contract if missing
        if coll_addr and (not coll_symbol or coll_decimals is None):
            dec, sym = resolver.get_token_info(coll_addr)
            if not coll_symbol:
                coll_symbol = sym
                enriched["collateral_symbol"] = sym
            if coll_decimals is None:
                coll_decimals = dec
                enriched["collateral_decimals"] = dec

        if coll_addr and coll_decimals is not None and block_num:
            if resolver.is_receipt_token(coll_symbol, coll_addr):
                res = resolver.resolve(coll_addr, coll_amount_raw, coll_decimals, block_num)
                if res["underlying_amount"] is not None:
                    resolved += 1
                    enriched["collateral_underlying_address"] = res["underlying_address"]
                    enriched["collateral_underlying_symbol"] = res["underlying_symbol"]
                    enriched["collateral_underlying_decimals"] = res["underlying_decimals"]
                    enriched["collateral_amount"] = res["underlying_amount"]
                    if res["underlying_value_usd"] is not None:
                        enriched["collateral_price_usd"] = res["underlying_price_usd"]
                        enriched["collateral_value_usd"] = res["underlying_value_usd"]

        # Check debt
        debt_addr = event.get("debt_asset")
        debt_symbol = event.get("debt_symbol")
        debt_decimals = event.get("debt_decimals")
        debt_amount_raw = event.get("debt_repaid_raw", 0)

        # Get symbol/decimals from contract if missing
        if debt_addr and (not debt_symbol or debt_decimals is None):
            dec, sym = resolver.get_token_info(debt_addr)
            if not debt_symbol:
                debt_symbol = sym
                enriched["debt_symbol"] = sym
            if debt_decimals is None:
                debt_decimals = dec
                enriched["debt_decimals"] = dec

        if debt_addr and debt_decimals is not None and block_num:
            if resolver.is_receipt_token(debt_symbol, debt_addr):
                res = resolver.resolve(debt_addr, debt_amount_raw, debt_decimals, block_num)
                if res["underlying_amount"] is not None:
                    enriched["debt_underlying_address"] = res["underlying_address"]
                    enriched["debt_underlying_symbol"] = res["underlying_symbol"]
                    enriched["debt_underlying_decimals"] = res["underlying_decimals"]
                    enriched["debt_amount"] = res["underlying_amount"]
                    if res["underlying_value_usd"] is not None:
                        enriched["debt_price_usd"] = res["underlying_price_usd"]
                        enriched["debt_value_usd"] = res["underlying_value_usd"]

        if enriched.get("collateral_value_usd"):
            priced += 1

        if not dry_run:
            out_f.write(json.dumps(enriched) + "\n")

        if (i + 1) % 1000 == 0:
            pct = 100 * priced / total if total > 0 else 0
            print(f"  Processed {i+1:,}/{len(events):,} - {resolved:,} resolved, {pct:.1f}% priced")

    if not dry_run:
        out_f.close()

        # Replace original
        import shutil
        shutil.move(str(output_file), str(input_file))
        print(f"  Updated: {input_file}")

    pct = 100 * priced / total if total > 0 else 0
    print(f"\n  DONE: {total:,} total, {resolved:,} resolved, {priced:,} priced ({pct:.1f}%)")

    return {
        "chain": chain,
        "status": "success",
        "total": total,
        "resolved": resolved,
        "priced": priced,
        "already_priced": already_priced,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chain", required=True, help="Chain or 'all'")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("RECEIPT TOKEN RESOLUTION")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    target_chains = ["bsc", "avalanche", "linea", "scroll", "polygon", "arbitrum", "optimism"]

    if args.chain == "all":
        chains = target_chains
    elif args.chain in target_chains:
        chains = [args.chain]
    else:
        print(f"[error] Use: {', '.join(target_chains)} or 'all'")
        sys.exit(1)

    results = []
    for chain in chains:
        result = process_chain(chain, args.dry_run)
        results.append(result)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for r in results:
        if r["status"] == "success":
            pct = 100 * r["priced"] / r["total"] if r["total"] > 0 else 0
            print(f"  {r['chain']}: {r['total']:,} events, {r['resolved']:,} resolved, {pct:.1f}% priced")
        else:
            print(f"  {r['chain']}: ERROR - {r.get('error')}")


if __name__ == "__main__":
    main()
