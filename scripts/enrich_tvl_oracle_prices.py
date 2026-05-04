#!/usr/bin/env python3
"""
Enrich ALL bronze TVL data with on-chain oracle prices.

Scans data/bronze/tvl/ for unique (chain, token_address, date) tuples,
queries each protocol's own oracle at the historical block via dRPC,
and stores results in data/cache/prices/protocol_oracle_prices.json.

Oracle selection per chain:
- Chains with Aave V3: use PoolAddressesProvider -> getPriceOracle -> getAssetPrice
- Fantom (IronBank): Compound V2 oracle via Comptroller.oracle() -> getUnderlyingPrice
- Meter/Flare: Compound V2 oracle
- Fallback: DefiLlama address-based API

No stablecoin assumptions — every token gets its real on-chain price.

Usage:
    python scripts/enrich_tvl_oracle_prices.py
    python scripts/enrich_tvl_oracle_prices.py --chains ethereum arbitrum
    python scripts/enrich_tvl_oracle_prices.py --workers 15
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Dict, Optional, List, Set, Tuple

from web3 import Web3

# ============================================================================
# Config
# ============================================================================

BRONZE_DIR = Path('data/bronze/tvl')
BLOCK_CACHE_DIR = Path('data/cache')
ORACLE_CACHE_FILE = Path('data/cache/prices/protocol_oracle_prices.json')

DRPC_KEY = os.environ.get("DRPC_KEY", "")
if not DRPC_KEY:
    raise RuntimeError("DRPC_KEY environment variable is not set. See .env.example.")

DRPC_NETWORKS = {
    "ethereum": "ethereum", "polygon": "polygon", "avalanche": "avalanche",
    "arbitrum": "arbitrum", "optimism": "optimism", "base": "base",
    "gnosis": "gnosis", "linea": "linea", "scroll": "scroll",
    "bsc": "bsc", "binance": "bsc", "ink": "ink", "sonic": "sonic",
    "celo": "celo", "fantom": "fantom", "blast": "blast",
    "zksync": "zksync-mainnet", "meter": "meter",
}

# Aave V3 PoolAddressesProvider per chain (getAssetPrice returns 8-decimal USD)
AAVE_V3_PROVIDERS = {
    'ethereum':  '0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e',
    'arbitrum':  '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    'optimism':  '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    'polygon':   '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    'avalanche': '0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb',
    'base':      '0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D',
    'binance':   '0xff75B6da14FfbbfD355Daf7a2731456b3562Ba6D',
    'gnosis':    '0x36616cf17557639614c1cdDb356b1B83fc0B2132',
    'linea':     '0x89502c3731F69DDC95B65753708A07F8Cd0373F4',
    'scroll':    '0x69850D0B276776781C063771b161bd8894BCdD04',
    'ink':       '0x4172E6aAEC070ACB31aaCE343A58c93E4C70f44D',
    'sonic':     '0x5C2e738F6E27bCE0F7558051Bf90605dD6176900',
    'celo':      '0x9F7Cf9417D5251C59fE94fB9147feEe1aAd9Cea5',
    'blast':     '0xb0811a1FC9Fb9972ee683Ba04c32Cb828Bcf587B',
    'zksync':    '0x4f285Ea117eF0067B59853D6d16a5dE8088bA259',
}

# SparkLend providers (separate Aave V3 fork)
SPARK_PROVIDERS = {
    'ethereum': '0x02C3eA4e34C0cBd694D2adFa2c690EECbC1793eE',
    'gnosis':   '0xA98DaCB3fC964A6A0d2ce3B77294241585EAbA6d',
}

# Compound V2 oracle: Comptroller.oracle() -> getUnderlyingPrice(cToken)
# Used for chains without Aave V3
COMPOUND_V2_COMPTROLLERS = {
    'fantom':    '0x4250A6D3BD57455d7C6821eECb6206F507576cD2',  # Iron Bank
    'meter':     '0xCa03230E7FB13456326a234CEFdD06CBFA0fD2B7',  # Sumer
}

# ABIs
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

COMPTROLLER_ABI = [
    {"inputs": [], "name": "oracle",
     "outputs": [{"type": "address"}],
     "stateMutability": "view", "type": "function"},
]

COMPOUND_ORACLE_ABI = [
    {"inputs": [{"type": "address", "name": "cToken"}],
     "name": "getUnderlyingPrice",
     "outputs": [{"type": "uint256"}],
     "stateMutability": "view", "type": "function"},
]

# For raw eth_call (avoids ABI overhead, better compatibility)
_GET_ASSET_PRICE_SIG = Web3.keccak(text='getAssetPrice(address)')[:4]


# ============================================================================
# Oracle cache
# ============================================================================

_cache: Dict[str, float] = {}
_cache_lock = Lock()
_cache_dirty = False


def load_cache():
    global _cache
    ORACLE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if ORACLE_CACHE_FILE.exists():
        with open(ORACLE_CACHE_FILE) as f:
            _cache = json.load(f)
    print(f"  Oracle cache loaded: {len(_cache):,} entries")


def save_cache():
    """Save cache with load-merge-save to prevent parallel overwrites."""
    global _cache, _cache_dirty
    with _cache_lock:
        # Merge with on-disk version to avoid clobbering parallel writes
        if ORACLE_CACHE_FILE.exists():
            try:
                with open(ORACLE_CACHE_FILE) as f:
                    disk = json.load(f)
                # Merge: in-memory wins for conflicts
                disk.update(_cache)
                _cache = disk
            except Exception:
                pass
        with open(ORACLE_CACHE_FILE, 'w') as f:
            json.dump(_cache, f)
        _cache_dirty = False
    print(f"  Oracle cache saved: {len(_cache):,} entries")


def cache_key(chain: str, token_addr: str, date: str) -> str:
    return f"{chain}:{token_addr.lower()}:{date}"


# ============================================================================
# Block cache
# ============================================================================

_block_caches: Dict[str, Dict[str, int]] = {}


def load_block_cache(chain: str) -> Dict[str, int]:
    if chain in _block_caches:
        return _block_caches[chain]

    blocks = {}
    search_names = [chain]
    if chain == 'gnosis':
        search_names.append('xdai')
    if chain == 'binance':
        search_names.append('bsc')

    for name in search_names:
        for f in BLOCK_CACHE_DIR.glob(f'{name}_blocks_*.json'):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                for date_str, info in data.items():
                    if isinstance(info, dict) and 'block' in info:
                        blocks[date_str] = int(info['block'])
                    elif isinstance(info, int):
                        blocks[date_str] = info
            except Exception:
                continue

    _block_caches[chain] = blocks
    return blocks


# ============================================================================
# Chain parsing
# ============================================================================

def get_chain(csu: str) -> str:
    csu_lower = csu.lower()
    for c in ['ethereum', 'arbitrum', 'optimism', 'polygon', 'avalanche',
              'binance', 'gnosis', 'linea', 'scroll', 'ink', 'base',
              'sonic', 'celo', 'fantom', 'blast', 'zksync', 'meter',
              'flare', 'cronos', 'manta']:
        if c in csu_lower:
            return c
    aliases = {'eth': 'ethereum', 'arb': 'arbitrum', 'op': 'optimism',
               'bsc': 'binance', 'poly': 'polygon', 'xdai': 'gnosis'}
    for part in csu_lower.split('_'):
        if part in aliases:
            return aliases[part]
    return 'unknown'


# ============================================================================
# Scan bronze TVL
# ============================================================================

CHAIN_ALIASES = {'xdai': 'gnosis', 'bsc': 'binance'}


def normalize_chain(chain: str) -> str:
    """Normalize chain names (xdai->gnosis, bsc->binance)."""
    return CHAIN_ALIASES.get(chain.lower(), chain.lower())


def scan_bronze_tvl() -> Dict[str, Set[Tuple[str, str]]]:
    """Scan bronze TVL for unique (chain -> set of (token_addr, date)) needing prices."""
    needs: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)

    for csu_dir in sorted(BRONZE_DIR.iterdir()):
        if not csu_dir.is_dir():
            continue
        csu = csu_dir.name

        # Read chain from the first JSON file rather than guessing from name
        chain = None
        for json_file in sorted(csu_dir.glob('*.json')):
            date = json_file.stem
            if len(date) != 10 or date[4] != '-':
                continue
            try:
                with open(json_file) as f:
                    data = json.load(f)
                if isinstance(data, dict) and 'chain' in data:
                    chain = normalize_chain(data['chain'])
                    break
            except Exception:
                continue

        if not chain:
            chain = get_chain(csu)
        if chain == 'unknown':
            continue

        for json_file in csu_dir.glob('*.json'):
            date = json_file.stem
            if len(date) != 10 or date[4] != '-':
                continue
            try:
                with open(json_file) as f:
                    data = json.load(f)
                markets = data.get('data', data if isinstance(data, list) else [])
                for m in markets:
                    # Extract token address from any schema
                    token_addr = (m.get('underlying') or
                                  m.get('loan_token') or
                                  m.get('collateral_token') or
                                  m.get('token_address') or '')
                    if not token_addr or not token_addr.startswith('0x'):
                        continue
                    key = cache_key(chain, token_addr, date)
                    if key not in _cache:
                        needs[chain].add((token_addr.lower(), date))
            except Exception:
                continue

    return needs


# ============================================================================
# Oracle fetching
# ============================================================================

def get_web3(chain: str) -> Optional[Web3]:
    network = DRPC_NETWORKS.get(chain)
    if not network:
        return None
    url = f"https://lb.drpc.org/ogrpc?network={network}&dkey={DRPC_KEY}"
    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 60}))
    return w3


def resolve_aave_oracle(w3: Web3, provider_addr: str) -> Optional[str]:
    """Resolve Aave V3 oracle address from provider."""
    try:
        provider = w3.eth.contract(
            address=Web3.to_checksum_address(provider_addr),
            abi=PROVIDER_ABI
        )
        return provider.functions.getPriceOracle().call()
    except Exception as e:
        print(f"    [WARN] Cannot resolve oracle from {provider_addr}: {e}")
        return None


def fetch_aave_price_raw(w3: Web3, oracle_addr: str, token_addr: str,
                         block: int) -> Optional[float]:
    """Fetch price via raw eth_call for Aave V3 oracle."""
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


def _worker_aave(args):
    """Worker for Aave V3 oracle price fetch."""
    chain, token_addr, date, block, oracle_addrs = args
    try:
        w3 = get_web3(chain)
        if not w3:
            return (chain, token_addr, date, None)
        for oracle_addr in oracle_addrs:
            price = fetch_aave_price_raw(w3, oracle_addr, token_addr, block)
            if price is not None:
                return (chain, token_addr, date, price)
    except Exception:
        pass
    return (chain, token_addr, date, None)


def enrich_chain_aave(chain: str, pairs: Set[Tuple[str, str]],
                      max_workers: int = 15) -> int:
    """Enrich prices for a chain using Aave V3 oracle(s)."""
    w3 = get_web3(chain)
    if not w3:
        print(f"  {chain}: cannot connect via dRPC")
        return 0

    # Load block cache
    blocks = load_block_cache(chain)
    if not blocks:
        print(f"  {chain}: no block cache found")
        return 0

    # Resolve oracle addresses
    oracle_addrs = []

    # Primary: Aave V3
    if chain in AAVE_V3_PROVIDERS:
        addr = resolve_aave_oracle(w3, AAVE_V3_PROVIDERS[chain])
        if addr:
            oracle_addrs.append(addr)
            print(f"    Aave V3 oracle: {addr}")

    # Secondary: SparkLend
    if chain in SPARK_PROVIDERS:
        addr = resolve_aave_oracle(w3, SPARK_PROVIDERS[chain])
        if addr and addr not in oracle_addrs:
            oracle_addrs.append(addr)
            print(f"    SparkLend oracle: {addr}")

    if not oracle_addrs:
        print(f"  {chain}: no Aave-style oracle available")
        return 0

    # Build work items
    work_items = []
    skipped = 0
    for token_addr, date in pairs:
        block = blocks.get(date)
        if block is None:
            skipped += 1
            continue
        work_items.append((chain, token_addr, date, block, oracle_addrs))

    if skipped:
        print(f"    Skipped {skipped} items (no block number)")

    if not work_items:
        return 0

    print(f"    Fetching {len(work_items):,} prices with {max_workers} workers...")

    fetched = 0
    failed = 0
    global _cache_dirty

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_worker_aave, item): item for item in work_items}
        done = 0

        for future in as_completed(futures):
            done += 1
            try:
                ch, token_addr, date, price = future.result()
                if price is not None:
                    key = cache_key(ch, token_addr, date)
                    with _cache_lock:
                        _cache[key] = price
                        _cache_dirty = True
                    fetched += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

            if done % 2000 == 0:
                print(f"    {chain}: {done:,}/{len(work_items):,} "
                      f"({fetched:,} ok, {failed:,} failed)", flush=True)
                if _cache_dirty:
                    save_cache()

    print(f"  {chain}: DONE - {fetched:,} fetched, {failed:,} failed")

    if _cache_dirty:
        save_cache()

    return fetched


def enrich_chain_compound_v2(chain: str, pairs: Set[Tuple[str, str]],
                             max_workers: int = 10) -> int:
    """
    Enrich prices for a chain using Compound V2 oracle.
    Falls back to DefiLlama address-based API since Compound V2 oracle
    takes cToken address (not underlying), and we only have underlying addresses.
    """
    # For Compound V2, the oracle takes cToken addresses, not underlying.
    # We don't have cToken->underlying mappings in bronze TVL consistently.
    # So for these chains, try Aave oracle first if available, then DefiLlama.

    w3 = get_web3(chain)
    if not w3:
        print(f"  {chain}: cannot connect via dRPC")
        return 0

    blocks = load_block_cache(chain)
    if not blocks:
        print(f"  {chain}: no block cache found")
        return 0

    # Try Aave V3 oracle if available on this chain
    oracle_addrs = []
    if chain in AAVE_V3_PROVIDERS:
        addr = resolve_aave_oracle(w3, AAVE_V3_PROVIDERS[chain])
        if addr:
            oracle_addrs.append(addr)

    if oracle_addrs:
        # Use Aave oracle path
        print(f"    {chain}: using Aave V3 oracle as primary")
        return enrich_chain_aave(chain, pairs, max_workers)

    # Fallback: DefiLlama address-based API
    print(f"    {chain}: no Aave oracle, using DefiLlama address API")
    return enrich_chain_defillama(chain, pairs)


def enrich_chain_defillama(chain: str, pairs: Set[Tuple[str, str]]) -> int:
    """Fallback: fetch prices from DefiLlama by address."""
    import requests
    from datetime import datetime, timezone

    DL_CHAINS = {
        "ethereum": "ethereum", "polygon": "polygon", "avalanche": "avax",
        "arbitrum": "arbitrum", "optimism": "optimism", "base": "base",
        "gnosis": "gnosis", "linea": "linea", "scroll": "scroll",
        "bsc": "bsc", "binance": "bsc", "ink": "ink", "sonic": "sonic",
        "celo": "celo", "fantom": "fantom", "blast": "blast",
        "zksync": "era", "meter": "meter",
    }

    dl_chain = DL_CHAINS.get(chain)
    if not dl_chain:
        print(f"    {chain}: no DefiLlama chain mapping")
        return 0

    # Deduplicate: group by date, batch tokens
    date_tokens: Dict[str, List[str]] = defaultdict(list)
    for token_addr, date in pairs:
        date_tokens[date].append(token_addr)

    fetched = 0
    failed = 0
    global _cache_dirty

    for i, (date, tokens) in enumerate(sorted(date_tokens.items())):
        # Build batch request (up to 30 per call)
        dt = datetime.strptime(date, '%Y-%m-%d')
        ts = int(dt.replace(tzinfo=timezone.utc).timestamp())

        unique_tokens = list(set(tokens))
        for batch_start in range(0, len(unique_tokens), 25):
            batch = unique_tokens[batch_start:batch_start + 25]
            coin_ids = [f"{dl_chain}:{addr}" for addr in batch]
            coins_str = ','.join(coin_ids)

            try:
                url = f"https://coins.llama.fi/prices/historical/{ts}/{coins_str}"
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    for coin_id in coin_ids:
                        coin_data = data.get("coins", {}).get(coin_id)
                        if coin_data:
                            price = coin_data.get("price")
                            if price and price > 0:
                                addr = coin_id.split(':')[1]
                                key = cache_key(chain, addr, date)
                                with _cache_lock:
                                    _cache[key] = price
                                    _cache_dirty = True
                                fetched += 1
                            else:
                                failed += 1
                        else:
                            failed += 1
                time.sleep(0.25)  # Rate limit: 4 req/sec
            except Exception:
                failed += len(batch)

        if (i + 1) % 50 == 0:
            print(f"    {chain}: {i+1}/{len(date_tokens)} dates, "
                  f"{fetched:,} ok, {failed:,} failed", flush=True)
            if _cache_dirty:
                save_cache()

    print(f"  {chain}: DONE (DefiLlama) - {fetched:,} fetched, {failed:,} failed")
    if _cache_dirty:
        save_cache()
    return fetched


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Enrich ALL bronze TVL with on-chain oracle prices')
    parser.add_argument('--chains', nargs='+', default=None,
                        help='Only process these chains')
    parser.add_argument('--workers', type=int, default=15,
                        help='Workers per chain (default: 15)')
    parser.add_argument('--defillama-only', action='store_true',
                        help='Skip Aave pass, go straight to DefiLlama for all gaps')
    args = parser.parse_args()

    print("=" * 70)
    print("Enrich Bronze TVL with On-Chain Oracle Prices")
    print("=" * 70)

    # Load oracle cache
    print("\nLoading oracle cache...")
    load_cache()

    # Scan bronze TVL
    print("\nScanning bronze TVL for missing prices...")
    needs = scan_bronze_tvl()

    total_needed = sum(len(v) for v in needs.values())
    print(f"\nTotal lookups needed: {total_needed:,}")
    for chain in sorted(needs.keys(), key=lambda c: -len(needs[c])):
        tokens = set(addr for addr, _ in needs[chain])
        print(f"  {chain:15s}  {len(needs[chain]):>7,} lookups  ({len(tokens)} tokens)")

    if args.chains:
        needs = {c: v for c, v in needs.items() if c in args.chains}
        print(f"\nFiltered to chains: {args.chains}")

    total_fetched = 0

    if not getattr(args, 'defillama_only', False):
        # Pass 1: On-chain oracles
        print("\n" + "=" * 70)
        print("Pass 1: Fetching prices from protocol oracles via dRPC")
        print("=" * 70)

        aave_chains = [c for c in needs if c in AAVE_V3_PROVIDERS]
        other_chains = [c for c in needs if c not in AAVE_V3_PROVIDERS]

        for chain in sorted(aave_chains, key=lambda c: -len(needs[c])):
            print(f"\n--- {chain} ({len(needs[chain]):,} lookups) ---")
            n = enrich_chain_aave(chain, needs[chain], max_workers=args.workers)
            total_fetched += n

        for chain in sorted(other_chains, key=lambda c: -len(needs[c])):
            print(f"\n--- {chain} ({len(needs[chain]):,} lookups, DefiLlama fallback) ---")
            n = enrich_chain_defillama(chain, needs[chain])
            total_fetched += n

        save_cache()

        # Re-scan for still-missing prices
        needs = scan_bronze_tvl()

    # Pass 2: DefiLlama fallback for ALL remaining gaps
    remaining = sum(len(v) for v in needs.values())
    if remaining > 0:
        print("\n" + "=" * 70)
        print(f"Pass 2: DefiLlama fallback for {remaining:,} remaining gaps")
        print("=" * 70)

        for chain in sorted(needs.keys(), key=lambda c: -len(needs[c])):
            count = len(needs[chain])
            if count == 0:
                continue
            print(f"\n--- {chain} ({count:,} lookups, DefiLlama) ---")
            n = enrich_chain_defillama(chain, needs[chain])
            total_fetched += n
        save_cache()
    else:
        print("\nNo remaining gaps — all prices fetched!")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total new prices fetched: {total_fetched:,}")
    print(f"  Oracle cache now: {len(_cache):,} entries")

    # Coverage by chain
    from collections import Counter
    chain_counts = Counter()
    for key in _cache:
        ch = key.split(':')[0]
        chain_counts[ch] += 1
    print("\n  Prices by chain:")
    for ch, n in chain_counts.most_common():
        print(f"    {ch:15s}  {n:>7,}")

    print(f"\nDone. Next: python scripts/build_volatility_panel.py")


if __name__ == '__main__':
    main()
