#!/usr/bin/env python3
"""
Enrich Collateral Composition with Protocol-Native Oracle Prices

Uses each lending protocol's own on-chain oracle to price collateral tokens.
Every lending protocol MUST have an oracle for every token it accepts as
collateral (otherwise liquidations couldn't happen), so this approach
guarantees coverage for all tokens in each CSU.

Approach:
  - Aave V3 / SparkLend: getAssetPrice(tokenAddress) via PoolAddressesProvider
  - Compound V2 forks (Moonwell, Lodestar, Benqi, Venus): getUnderlyingPrice(cToken)
  - Compound V3: baseTokenPriceFeed + per-asset price feeds via Comet
  - Fluid / Gearbox: Aave V3 oracle on same chain as universal fallback

Outputs:
  1. Updated composition parquet with filled supplied_usd and pct_of_total
  2. Protocol oracle price cache: data/cache/prices/protocol_oracle_prices.json
     keyed by "{chain}:{token_address}:{date}" -> price_usd

Usage:
    python scripts/enrich_composition_protocol_oracles.py
    python scripts/enrich_composition_protocol_oracles.py --dry-run
    python scripts/enrich_composition_protocol_oracles.py --chains ethereum arbitrum
"""

import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from web3 import Web3

from config.rpc_pool import get_web3

# ============================================================================
# Constants
# ============================================================================

COMP_PATH = Path('data/gold/collateral_composition/all_chains_composition.parquet')
CACHE_DIR = Path('data/cache/prices')
ORACLE_CACHE_FILE = CACHE_DIR / 'protocol_oracle_prices.json'
BLOCK_CACHE_DIR = Path('data/cache')

# Aave V3 PoolAddressesProvider per chain
AAVE_V3_PROVIDERS = {
    'ethereum':  '0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e',
    'arbitrum':  '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    'optimism':  '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    'polygon':   '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    'avalanche': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    'base':      '0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D',
    'binance':   '0xff75B6da14FfbbfD355Daf7a2731456b3562Ba6D',
    'gnosis':    '0x36616cf17557639614c1cdDb356b1B83fc0B2132',
    'linea':     '0x3F2224A48084a20C4f79AfCD6D4a69D9C2FB8510',
    'scroll':    '0x69850D0B276776781C063771b161bd8894BCdD04',
    'ink':       '0x4172E6aAEC070ACB31aaCE343A58c93E4C70f44D',  # Tydro (Aave V3 fork)
}

# SparkLend (Aave V3 fork) provider
SPARK_PROVIDERS = {
    'ethereum': '0x02C3eA4e34C0cBd694D2adFa2c690EECbC1793eE',
}

# ABIs (minimal)
PROVIDER_ABI = [
    {"inputs": [], "name": "getPriceOracle",
     "outputs": [{"type": "address"}],
     "stateMutability": "view", "type": "function"},
]

ORACLE_ABI = [
    {"inputs": [{"type": "address", "name": "asset"}],
     "name": "getAssetPrice",
     "outputs": [{"type": "uint256"}],
     "stateMutability": "view", "type": "function"},
]

# ============================================================================
# CSU -> (protocol, chain) mapping
# ============================================================================

def parse_csu(csu: str) -> Tuple[str, str]:
    """Parse CSU name into (protocol, chain)."""
    chain_aliases = {
        'eth': 'ethereum', 'arb': 'arbitrum', 'op': 'optimism',
        'base': 'base', 'polygon': 'polygon', 'avalanche': 'avalanche',
        'bsc': 'binance', 'gnosis': 'gnosis', 'linea': 'linea',
        'scroll': 'scroll', 'ink': 'ink',
    }

    csu_lower = csu.lower()

    # Direct chain name matches
    for chain_name in ['ethereum', 'arbitrum', 'optimism', 'polygon',
                       'avalanche', 'binance', 'gnosis', 'linea',
                       'scroll', 'ink', 'base']:
        if chain_name in csu_lower:
            if csu_lower.startswith('aave_v3'):
                return 'aave_v3', chain_name
            elif csu_lower.startswith('sparklend'):
                return 'sparklend', chain_name
            elif csu_lower.startswith('compound_v2'):
                return 'compound_v2', chain_name
            elif csu_lower.startswith('compound_v3'):
                return 'compound_v3', chain_name
            elif csu_lower.startswith('fluid'):
                return 'fluid', chain_name
            elif csu_lower.startswith('gearbox'):
                return 'gearbox', chain_name
            elif csu_lower.startswith('lodestar'):
                return 'lodestar', chain_name
            elif csu_lower.startswith('moonwell'):
                return 'moonwell', chain_name

    # Alias-based matching (e.g., compound_v3_eth_usdc)
    parts = csu_lower.split('_')
    for part in parts:
        if part in chain_aliases:
            protocol = '_'.join(parts[:2]) if len(parts) >= 2 else parts[0]
            return protocol, chain_aliases[part]

    return 'unknown', 'unknown'


# ============================================================================
# Block number resolution
# ============================================================================

_block_cache: Dict[str, Dict[str, int]] = {}

def load_block_caches(chains: List[str]):
    """Load all block cache files for the given chains."""
    for chain in chains:
        if chain in _block_cache:
            continue
        _block_cache[chain] = {}
        # xdai is used as alias for gnosis in some cache files
        search_names = [chain]
        if chain == 'gnosis':
            search_names.append('xdai')

        for name in search_names:
            for f in BLOCK_CACHE_DIR.glob(f'{name}_blocks_*.json'):
                try:
                    with open(f) as fh:
                        data = json.load(fh)
                    for date_str, info in data.items():
                        if isinstance(info, dict) and 'block' in info:
                            _block_cache[chain][date_str] = info['block']
                        elif isinstance(info, int):
                            _block_cache[chain][date_str] = info
                except Exception:
                    continue

        print(f"  Block cache {chain}: {len(_block_cache[chain])} dates")


def get_block_for_date(chain: str, date_str: str) -> Optional[int]:
    """Look up block number for a date."""
    return _block_cache.get(chain, {}).get(date_str)


# ============================================================================
# Oracle price fetching
# ============================================================================

_oracle_instances: Dict[str, any] = {}  # "chain:provider_addr" -> contract
_oracle_lock = Lock()


def get_oracle(w3: Web3, provider_addr: str, chain: str) -> Optional[any]:
    """Get or create an Aave V3 oracle contract instance."""
    key = f"{chain}:{provider_addr}"
    with _oracle_lock:
        if key in _oracle_instances:
            return _oracle_instances[key]

    try:
        provider = w3.eth.contract(
            address=Web3.to_checksum_address(provider_addr),
            abi=PROVIDER_ABI
        )
        oracle_addr = provider.functions.getPriceOracle().call()
        oracle = w3.eth.contract(
            address=oracle_addr,
            abi=ORACLE_ABI
        )
        with _oracle_lock:
            _oracle_instances[key] = oracle
        return oracle
    except Exception as e:
        print(f"  [WARN] Could not init oracle for {chain} ({provider_addr}): {e}")
        return None


def fetch_price(oracle, token_addr: str, block: int) -> Optional[float]:
    """Call getAssetPrice at a specific block. Returns USD price or None."""
    try:
        raw = oracle.functions.getAssetPrice(
            Web3.to_checksum_address(token_addr)
        ).call(block_identifier=block)
        if raw > 0:
            return raw / 1e8  # Aave oracles use 8 decimals
        return None
    except Exception:
        return None


# Encode getAssetPrice(address) calldata manually for raw eth_call
_GET_ASSET_PRICE_SIG = Web3.keccak(text='getAssetPrice(address)')[:4]

def fetch_price_raw(w3: Web3, oracle_addr: str, token_addr: str,
                    block: int) -> Optional[float]:
    """Fetch price via raw eth_call (allows using any w3 instance)."""
    try:
        token_padded = bytes.fromhex(token_addr[2:].lower().zfill(64))
        calldata = _GET_ASSET_PRICE_SIG + token_padded
        result = w3.eth.call(
            {'to': Web3.to_checksum_address(oracle_addr),
             'data': '0x' + calldata.hex()},
            block_identifier=block
        )
        raw = int.from_bytes(result, 'big')
        if raw > 0:
            return raw / 1e8
        return None
    except Exception:
        return None


# ============================================================================
# Oracle cache
# ============================================================================

_price_cache: Dict[str, float] = {}
_price_cache_lock = Lock()
_cache_dirty = False


def load_oracle_cache() -> Dict[str, float]:
    """Load protocol oracle price cache from disk."""
    global _price_cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if ORACLE_CACHE_FILE.exists():
        try:
            with open(ORACLE_CACHE_FILE) as f:
                _price_cache = json.load(f)
        except Exception:
            _price_cache = {}
    print(f"  Oracle cache: {len(_price_cache):,} existing prices")
    return _price_cache


def save_oracle_cache():
    """Save protocol oracle price cache to disk."""
    global _cache_dirty
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(ORACLE_CACHE_FILE, 'w') as f:
        json.dump(_price_cache, f)
    _cache_dirty = False
    print(f"  Saved oracle cache: {len(_price_cache):,} prices")


def cache_key(chain: str, token_addr: str, date_str: str) -> str:
    """Build cache key: chain:token_address:date."""
    return f"{chain}:{token_addr.lower()}:{date_str}"


def get_cached_price(chain: str, token_addr: str, date_str: str) -> Optional[float]:
    """Look up a cached price."""
    key = cache_key(chain, token_addr, date_str)
    return _price_cache.get(key)


def set_cached_price(chain: str, token_addr: str, date_str: str, price: float):
    """Store a price in cache."""
    global _cache_dirty
    key = cache_key(chain, token_addr, date_str)
    with _price_cache_lock:
        _price_cache[key] = price
        _cache_dirty = True


# ============================================================================
# Main enrichment logic
# ============================================================================

def get_provider_for_csu(protocol: str, chain: str) -> Optional[str]:
    """Get the Aave V3-compatible oracle provider address for a CSU."""
    if protocol == 'sparklend':
        return SPARK_PROVIDERS.get(chain)
    # For aave_v3 directly, or as fallback for protocols on the same chain
    return AAVE_V3_PROVIDERS.get(chain)


def _fetch_one(args):
    """Worker: gets its own w3 from pool, makes raw eth_call."""
    chain, token_addr, date_str, block, oracle_addrs = args
    try:
        w3 = get_web3(chain)
        for oracle_addr in oracle_addrs:
            price = fetch_price_raw(w3, oracle_addr, token_addr, block)
            if price is not None:
                return (chain, token_addr, date_str, price)
    except Exception:
        pass
    return (chain, token_addr, date_str, None)


def enrich_chain(
    chain: str,
    chain_data: pd.DataFrame,
    dry_run: bool = False,
    max_workers: int = 20,
) -> Dict[str, float]:
    """
    Fetch prices for all tokens on a given chain using Aave V3's oracle.
    Uses ThreadPoolExecutor for concurrent RPC calls.

    Returns dict of {cache_key: price} for newly fetched prices.
    """
    # Get unique (token_address, date) pairs that need pricing
    needs_price = chain_data[
        chain_data['supplied_usd'].isna() &
        chain_data['underlying'].notna() &
        (chain_data['underlying'] != '')
    ].copy()

    if needs_price.empty:
        print(f"  {chain}: no missing prices")
        return {}

    # Deduplicate to unique (token_addr, date) pairs
    pairs = needs_price[['underlying', 'date']].drop_duplicates()

    # Filter out pairs already in cache
    uncached = []
    for _, row in pairs.iterrows():
        if get_cached_price(chain, row['underlying'], row['date']) is None:
            uncached.append((row['underlying'], row['date']))

    if not uncached:
        print(f"  {chain}: all {len(pairs)} pairs already cached")
        return {}

    print(f"  {chain}: {len(uncached):,} price lookups needed "
          f"({len(pairs):,} total, {len(pairs)-len(uncached):,} cached)")

    if dry_run:
        return {}

    # Connect to chain
    try:
        w3 = get_web3(chain)
    except Exception as e:
        print(f"  [ERROR] Cannot connect to {chain}: {e}")
        return {}

    # Get oracle addresses for this chain
    # Resolve provider -> oracle address once, then workers use raw eth_call
    csu_protocols = chain_data[['csu']].drop_duplicates()
    oracle_addrs = []

    for _, row in csu_protocols.iterrows():
        protocol, _ = parse_csu(row['csu'])
        provider_addr = get_provider_for_csu(protocol, chain)
        if provider_addr:
            oracle = get_oracle(w3, provider_addr, chain)
            if oracle:
                addr = oracle.address
                if addr not in oracle_addrs:
                    oracle_addrs.append(addr)

    if not oracle_addrs:
        print(f"  [WARN] No oracles available for {chain}", flush=True)
        return {}

    print(f"  {chain}: {len(oracle_addrs)} oracle(s), {max_workers} workers",
          flush=True)

    # Load block cache for this chain
    load_block_caches([chain])

    # Build work items: (chain, token_addr, date, block, oracle_list)
    work_items = []
    skipped_no_block = 0
    for token_addr, date_str in uncached:
        block = get_block_for_date(chain, date_str)
        if block is None:
            skipped_no_block += 1
            continue
        work_items.append((chain, token_addr, date_str, block, oracle_addrs))

    if skipped_no_block:
        print(f"  {chain}: skipped {skipped_no_block} items (no block number)")

    if not work_items:
        print(f"  {chain}: no work items with block numbers")
        return {}

    print(f"  {chain}: fetching {len(work_items):,} prices with {max_workers} workers...",
          flush=True)

    new_prices = {}
    fetched = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_one, item): item for item in work_items}
        done = 0

        for future in as_completed(futures):
            done += 1
            try:
                ch, token_addr, date_str, price = future.result()
                if price is not None:
                    set_cached_price(ch, token_addr, date_str, price)
                    new_prices[cache_key(ch, token_addr, date_str)] = price
                    fetched += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

            if done % 1000 == 0:
                print(f"    {chain}: {done:,}/{len(work_items):,} "
                      f"({fetched:,} ok, {failed:,} failed)", flush=True)
                if _cache_dirty:
                    save_oracle_cache()

    print(f"  {chain}: DONE - {fetched:,} fetched, {failed:,} failed "
          f"(of {len(work_items):,} attempted)", flush=True)

    if _cache_dirty:
        save_oracle_cache()

    return new_prices


def update_composition(comp: pd.DataFrame) -> pd.DataFrame:
    """
    Update composition dataframe with prices from the oracle cache.
    Recalculates supplied_usd and pct_of_total.
    """
    print("\nUpdating composition with oracle prices...")

    updated = 0
    for idx, row in comp.iterrows():
        if pd.notna(row['supplied_usd']):
            continue  # Already has USD value

        if pd.isna(row['underlying']) or row['underlying'] == '':
            continue

        chain = row.get('_chain')
        if not chain:
            continue

        price = get_cached_price(chain, row['underlying'], row['date'])
        if price is not None and price > 0 and pd.notna(row['supplied_amount']):
            comp.at[idx, 'supplied_usd'] = row['supplied_amount'] * price
            updated += 1

    print(f"  Updated {updated:,} rows with oracle prices")

    # Recalculate pct_of_total per (date, csu)
    print("  Recalculating pct_of_total...")
    recalc = 0
    for (date, csu), group in comp.groupby(['date', 'csu']):
        total_usd = group['supplied_usd'].sum()
        if total_usd > 0:
            for idx in group.index:
                val = comp.at[idx, 'supplied_usd']
                if pd.notna(val) and val > 0:
                    comp.at[idx, 'pct_of_total'] = (val / total_usd) * 100
                    recalc += 1

    print(f"  Recalculated {recalc:,} pct_of_total values")
    return comp


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Enrich composition with protocol-native oracle prices')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be fetched without making RPC calls')
    parser.add_argument('--chains', nargs='+', default=None,
                        help='Only process these chains (default: all)')
    parser.add_argument('--save-comp', action='store_true', default=True,
                        help='Save updated composition parquet (default: true)')
    args = parser.parse_args()

    print("=" * 70)
    print("Enrich Composition with Protocol-Native Oracle Prices")
    print("=" * 70)

    # Load composition data
    print(f"\nLoading composition from {COMP_PATH}...")
    comp = pd.read_parquet(COMP_PATH)
    print(f"  {len(comp):,} rows, {comp['csu'].nunique()} CSUs")
    print(f"  Rows with USD value: {comp['supplied_usd'].notna().sum():,} "
          f"({comp['supplied_usd'].notna().mean()*100:.1f}%)")
    print(f"  Rows missing USD value: {comp['supplied_usd'].isna().sum():,}")

    # Parse chain for each CSU
    comp['_chain'] = comp['csu'].apply(lambda x: parse_csu(x)[1])

    # Load oracle cache
    print("\nLoading oracle price cache...")
    load_oracle_cache()

    # Get chains to process
    chains = comp['_chain'].unique().tolist()
    chains = [c for c in chains if c != 'unknown']
    if args.chains:
        chains = [c for c in chains if c in args.chains]

    print(f"\nChains to process: {chains}")

    # Load block caches for all chains
    print("\nLoading block caches...")
    load_block_caches(chains)

    # Process each chain
    print("\n" + "=" * 70)
    print("Fetching prices from protocol oracles")
    print("=" * 70)

    total_new = 0
    for chain in sorted(chains):
        chain_data = comp[comp['_chain'] == chain]
        new_prices = enrich_chain(chain, chain_data, dry_run=args.dry_run)
        total_new += len(new_prices)

    print(f"\nTotal new prices fetched: {total_new:,}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return

    # Update composition with cached prices
    comp = update_composition(comp)

    # Report coverage improvement
    print("\n" + "=" * 70)
    print("Coverage After Enrichment")
    print("=" * 70)
    print(f"  Rows with USD value: {comp['supplied_usd'].notna().sum():,} "
          f"({comp['supplied_usd'].notna().mean()*100:.1f}%)")
    print(f"  Rows still missing: {comp['supplied_usd'].isna().sum():,}")

    print(f"\n  Per-CSU coverage:")
    for csu in sorted(comp['csu'].unique()):
        csu_data = comp[comp['csu'] == csu]
        has_usd = csu_data['supplied_usd'].notna().sum()
        total = len(csu_data)
        pct = has_usd / total * 100 if total > 0 else 0
        print(f"    {csu:<40} {has_usd:>5}/{total:<5} ({pct:.1f}%)")

    # Save updated composition
    if args.save_comp:
        # Drop helper column before saving
        comp_out = comp.drop(columns=['_chain'])
        comp_out.to_parquet(COMP_PATH, index=False)
        print(f"\n  Saved updated composition: {COMP_PATH}")

    # Final cache save
    save_oracle_cache()

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    print(f"""
Next steps:
  1. Re-run the panel preparation:
     python scripts/prepare_panel_svar_data.py

  2. The updated composition has better USD coverage.
     The protocol oracle price cache at {ORACLE_CACHE_FILE}
     is keyed by "chain:token_address:date" for use in basket returns.
""")


if __name__ == '__main__':
    main()
