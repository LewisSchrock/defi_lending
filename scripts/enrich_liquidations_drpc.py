#!/usr/bin/env python3
"""
Enrich Liquidation Events with USD Values via dRPC

Uses Aave V3's price oracle (or fallback to Chainlink) to get USD prices
at the exact block number when liquidations occurred.

Usage:
    python scripts/enrich_liquidations_drpc.py --chain ethereum
    python scripts/enrich_liquidations_drpc.py --chain all
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
from dotenv import load_dotenv

load_dotenv()

# Try to import web3
try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, BadFunctionCallOutput
except ImportError:
    print("[error] pip install web3")
    sys.exit(1)

# ============================================================================
# Configuration
# ============================================================================

INPUT_DIR = Path("data/bronze/liquidations")
OUTPUT_DIR = Path("data/silver/liquidations")

# Aave V3 PoolAddressesProvider per chain (from csu_config.yaml)
AAVE_PROVIDERS = {
    "ethereum": "0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e",
    "polygon": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    "avalanche": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    "arbitrum": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    "optimism": "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    "base": "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D",
    "gnosis": "0x36616cf17557639614c1cdDb356b1B83fc0B2132",
    "linea": "0x89502c3731F69DDC95B65753708A07F8Cd0373F4",
    "scroll": "0x69850D0B276776781C063771b161bd8894BCdD04",
    "bsc": "0xff75B6da14FfbbfD355Daf7a2731456b3562Ba6D",
    "ink": "0x4172E6aAEC070ACB31aaCE343A58c93E4C70f44D",  # Tydro (Aave V3 fork)
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
    # Common patterns
    "usdc", "usdt", "dai", "frax", "lusd", "gusd", "tusd", "usdp", "busd",
    "usdc.e", "usdt.e", "dai.e", "usdbc", "mai", "gho", "crvusd", "usde",
    "pyusd", "usds", "susd", "eurc", "eurs", "wxdai", "ageur",
}

# ABIs
PROVIDER_ABI = [
    {"inputs": [], "name": "getPriceOracle", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
]

ORACLE_ABI = [
    {"inputs": [{"type": "address", "name": "asset"}], "name": "getAssetPrice", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
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
    # Try chain-specific key first
    url = os.environ.get(f"DRPC_KEY_{chain.upper()}")
    if not url:
        # Fallback to generic key
        url = os.environ.get("DRPC_KEY_1")

    if not url:
        return None

    # If it's already a URL, use it directly
    if url.startswith("http"):
        return url

    # Otherwise, build the URL
    network = DRPC_NETWORKS.get(chain)
    if not network:
        return None
    return f"https://lb.drpc.org/ogrpc?network={network}&dkey={url}"


def get_web3(chain: str) -> Optional[Web3]:
    """Create Web3 instance for chain."""
    rpc_url = get_drpc_url(chain)
    if not rpc_url:
        print(f"  [warn] No dRPC key for {chain}")
        return None

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        print(f"  [warn] Could not connect to {chain}")
        return None

    return w3


def get_oracle_address(w3: Web3, provider_addr: str) -> Optional[str]:
    """Get Aave oracle address from provider."""
    try:
        provider = w3.eth.contract(
            address=Web3.to_checksum_address(provider_addr),
            abi=PROVIDER_ABI
        )
        return provider.functions.getPriceOracle().call()
    except Exception as e:
        print(f"  [warn] Failed to get oracle: {e}")
        return None


def get_token_info(w3: Web3, token_addr: str) -> Tuple[Optional[int], Optional[str]]:
    """Get token decimals and symbol."""
    try:
        token = w3.eth.contract(
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
        return decimals, symbol
    except Exception:
        return None, None


def get_price_at_block(w3: Web3, oracle_addr: str, token_addr: str, block_num: int) -> Optional[int]:
    """Get token price from Aave oracle at specific block."""
    try:
        oracle = w3.eth.contract(
            address=Web3.to_checksum_address(oracle_addr),
            abi=ORACLE_ABI
        )
        # Call at historical block
        price = oracle.functions.getAssetPrice(
            Web3.to_checksum_address(token_addr)
        ).call(block_identifier=block_num)
        return price
    except (ContractLogicError, BadFunctionCallOutput):
        return None
    except Exception as e:
        # Rate limit or other error
        if "429" in str(e) or "rate" in str(e).lower():
            time.sleep(1)
            return get_price_at_block(w3, oracle_addr, token_addr, block_num)
        return None


def is_stablecoin(symbol: Optional[str]) -> bool:
    """Check if token is a known stablecoin."""
    if not symbol:
        return False
    return symbol.lower().strip() in STABLECOINS


# ============================================================================
# Main Processing
# ============================================================================

def process_chain(chain: str, batch_size: int = 100, dry_run: bool = False) -> Dict:
    """Process all liquidations for a chain."""
    input_file = INPUT_DIR / chain / "events.jsonl"
    output_file = OUTPUT_DIR / chain / "events_enriched.jsonl"
    checkpoint_file = OUTPUT_DIR / chain / ".checkpoint"

    if not input_file.exists():
        return {"chain": chain, "status": "error", "error": "input not found"}

    print(f"\n{'='*60}")
    print(f"Processing {chain}")
    print(f"{'='*60}")

    # Connect to chain
    w3 = get_web3(chain)
    if not w3:
        return {"chain": chain, "status": "error", "error": "no RPC connection"}

    # Get oracle address
    provider_addr = AAVE_PROVIDERS.get(chain)
    if not provider_addr:
        return {"chain": chain, "status": "error", "error": "no provider address"}

    oracle_addr = get_oracle_address(w3, provider_addr)
    if not oracle_addr:
        return {"chain": chain, "status": "error", "error": "could not get oracle"}

    print(f"  Oracle: {oracle_addr}")

    # Load checkpoint if exists
    processed_keys = set()
    if checkpoint_file.exists() and not dry_run:
        with open(checkpoint_file) as f:
            processed_keys = set(line.strip() for line in f)
        print(f"  Resuming from checkpoint ({len(processed_keys):,} already processed)")

    # Cache for token info and prices
    token_cache: Dict[str, Tuple[int, str]] = {}  # addr -> (decimals, symbol)
    price_cache: Dict[Tuple[str, int], Optional[int]] = {}  # (addr, block) -> price

    # Read all events
    events = []
    with open(input_file) as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    print(f"  Total events: {len(events):,}")

    # Prepare output
    if not dry_run:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        # Append mode if resuming
        mode = 'a' if processed_keys else 'w'
        out_f = open(output_file, mode)
        checkpoint_f = open(checkpoint_file, 'a')

    enriched_count = 0
    price_found = 0
    price_missing = 0
    errors = 0

    for i, event in enumerate(events):
        # Create unique key
        key = f"{event.get('tx_hash', '')}_{event.get('log_index', 0)}"

        # Skip if already processed
        if key in processed_keys:
            continue

        block_num = event.get("block_number")
        if not block_num:
            errors += 1
            continue

        # Get token addresses
        coll_addr = event.get("collateral_asset")
        debt_addr = event.get("debt_asset")

        # Get token info (cached)
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
            cache_key = (coll_addr, block_num)
            if cache_key not in price_cache:
                if is_stablecoin(coll_symbol):
                    price_cache[cache_key] = 10**8  # $1.00 with 8 decimals
                else:
                    price_cache[cache_key] = get_price_at_block(w3, oracle_addr, coll_addr, block_num)
            coll_price = price_cache[cache_key]

        # Debt price
        if debt_addr:
            cache_key = (debt_addr, block_num)
            if cache_key not in price_cache:
                if is_stablecoin(debt_symbol):
                    price_cache[cache_key] = 10**8  # $1.00 with 8 decimals
                else:
                    price_cache[cache_key] = get_price_at_block(w3, oracle_addr, debt_addr, block_num)
            debt_price = price_cache[cache_key]

        # Calculate USD values
        coll_amount_raw = event.get("collateral_seized_raw", 0)
        debt_amount_raw = event.get("debt_repaid_raw", 0)

        coll_usd = None
        debt_usd = None

        if coll_price and coll_decimals is not None and coll_amount_raw:
            # price is in USD with 8 decimals
            # amount is in token units with `decimals` decimals
            coll_usd = (coll_amount_raw * coll_price) / (10 ** (coll_decimals + 8))

        if debt_price and debt_decimals is not None and debt_amount_raw:
            debt_usd = (debt_amount_raw * debt_price) / (10 ** (debt_decimals + 8))

        # Track stats
        if coll_usd is not None or debt_usd is not None:
            price_found += 1
        else:
            price_missing += 1

        # Build enriched event
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

            # Flush periodically
            if (i + 1) % 1000 == 0:
                out_f.flush()
                checkpoint_f.flush()

        # Add to processed set to handle duplicates within single run
        processed_keys.add(key)

        enriched_count += 1

        # Progress
        if (i + 1) % 500 == 0:
            pct_priced = 100 * price_found / (price_found + price_missing) if (price_found + price_missing) > 0 else 0
            print(f"  Processed {i+1:,}/{len(events):,} ({pct_priced:.1f}% priced)")

    if not dry_run:
        out_f.close()
        checkpoint_f.close()

    pct_priced = 100 * price_found / (price_found + price_missing) if (price_found + price_missing) > 0 else 0
    print(f"  DONE: {enriched_count:,} enriched, {pct_priced:.1f}% priced")

    return {
        "chain": chain,
        "status": "success",
        "enriched": enriched_count,
        "priced": price_found,
        "unpriced": price_missing,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Enrich liquidations with USD values via dRPC")
    parser.add_argument("--chain", required=True, help="Chain to process (or 'all')")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for RPC calls")
    parser.add_argument("--dry-run", action="store_true", help="Don't write output")
    args = parser.parse_args()

    print("=" * 60)
    print("LIQUIDATION USD ENRICHMENT (dRPC)")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Get chains
    if args.chain == "all":
        chains = [d.name for d in INPUT_DIR.iterdir() if d.is_dir() and (d / "events.jsonl").exists()]
        print(f"Found {len(chains)} chains: {', '.join(chains)}")
    else:
        chains = [args.chain]

    results = []
    for chain in chains:
        result = process_chain(chain, args.batch_size, args.dry_run)
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_enriched = 0
    total_priced = 0
    total_unpriced = 0

    for r in results:
        status = r["status"]
        if status == "success":
            total_enriched += r["enriched"]
            total_priced += r["priced"]
            total_unpriced += r["unpriced"]
            pct = 100 * r["priced"] / (r["priced"] + r["unpriced"]) if (r["priced"] + r["unpriced"]) > 0 else 0
            print(f"  {r['chain']}: {r['enriched']:,} events, {pct:.1f}% priced")
        else:
            print(f"  {r['chain']}: ERROR - {r.get('error', 'unknown')}")

    total_pct = 100 * total_priced / (total_priced + total_unpriced) if (total_priced + total_unpriced) > 0 else 0
    print(f"\nTotal: {total_enriched:,} events enriched, {total_pct:.1f}% USD coverage")


if __name__ == "__main__":
    main()
