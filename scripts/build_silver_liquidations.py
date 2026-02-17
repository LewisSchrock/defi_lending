#!/usr/bin/env python3
"""
Silver Liquidation Pipeline

Transforms bronze liquidation events into a clean, unified dataset.

Input:  data/bronze/liquidations/{chain}/events.jsonl
Output: data/silver/liquidations/{chain}/liquidations.parquet

Features:
- Unified schema across protocols (Aave, Compound, Sparklend)
- Joins Compound AbsorbDebt + AbsorbCollateral events
- Derives block_timestamp where missing
- Adds token metadata (symbol, decimals)
- Calculates USD values using historical prices

Usage:
    python scripts/build_silver_liquidations.py --chain ethereum
    python scripts/build_silver_liquidations.py --chain ethereum --skip-prices
    python scripts/build_silver_liquidations.py --chain ethereum --quick  # Skip RPC calls
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import time
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import pytz

# Optional imports
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from config.rpc_pool_v2 import get_web3

# Constants
NY_TZ = pytz.timezone("America/New_York")
DATA_DIR = Path(__file__).parent.parent / "data"
BRONZE_DIR = DATA_DIR / "bronze" / "liquidations"
SILVER_DIR = DATA_DIR / "silver" / "liquidations"
REFERENCE_DIR = DATA_DIR / "reference"

# Protocols to exclude from silver pipeline
EXCLUDED_PROTOCOLS = {'gearbox'}

# Chain name aliases (bronze dir name → RPC pool name)
CHAIN_ALIASES = {
    'bsc': 'binance',
    'xdai': 'gnosis',
}

# ERC20 ABI for token metadata
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
]


def load_bronze_events(chain: str) -> List[dict]:
    """Load bronze liquidation events for a chain."""
    events_file = BRONZE_DIR / chain / "events.jsonl"
    if not events_file.exists():
        raise FileNotFoundError(f"No bronze data found: {events_file}")

    events = []
    with open(events_file, 'r') as f:
        for line in f:
            if line.strip():
                event = json.loads(line)
                # Filter out excluded protocols
                protocol = event.get('protocol', '').lower()
                if protocol not in EXCLUDED_PROTOCOLS:
                    events.append(event)

    return events


def join_compound_events(events: List[dict]) -> List[dict]:
    """
    Join Compound v3 AbsorbDebt and AbsorbCollateral events.

    Compound emits separate events for debt and collateral in a liquidation.
    We join them by tx_hash + borrower to create unified records.
    """
    # Separate Compound events from others
    compound_debt = []
    compound_collateral = []
    other_events = []

    for e in events:
        if 'compound' in e.get('protocol', '').lower():
            # FIX: The parallel collector uses 'event_type', not 'event_name'
            # Check both field names for compatibility
            event_name = e.get('event_name') or e.get('event_type', '')
            if event_name == 'AbsorbDebt':
                compound_debt.append(e)
            elif event_name == 'AbsorbCollateral':
                compound_collateral.append(e)
            else:
                other_events.append(e)
        else:
            other_events.append(e)

    # Index collateral events by (tx_hash, borrower)
    collateral_by_key = defaultdict(list)
    for e in compound_collateral:
        key = (e.get('tx_hash'), e.get('borrower'))
        collateral_by_key[key].append(e)

    # Join debt events with their collateral events
    joined_events = []
    unmatched_debt = 0

    for debt_event in compound_debt:
        key = (debt_event.get('tx_hash'), debt_event.get('borrower'))
        collateral_matches = collateral_by_key.get(key, [])

        if collateral_matches:
            # Create one joined event per collateral type seized
            for coll_event in collateral_matches:
                joined = {
                    'tx_hash': debt_event.get('tx_hash'),
                    'log_index': debt_event.get('log_index'),
                    'block_number': debt_event.get('block_number'),
                    'block_timestamp': debt_event.get('block_timestamp') or coll_event.get('block_timestamp'),
                    'protocol': debt_event.get('protocol'),
                    'csu': debt_event.get('csu'),
                    'event_name': 'Liquidation',
                    'contract': debt_event.get('contract') or debt_event.get('contract_address'),
                    'borrower': debt_event.get('borrower'),
                    'liquidator': debt_event.get('absorber'),  # Compound calls it absorber
                    # FIX: The parallel collector outputs 'asset' (from indexed param) and 'collateral_raw',
                    # not 'collateral_asset' and 'collateral_absorbed_raw'. Check both field names.
                    'collateral_asset': coll_event.get('collateral_asset') or coll_event.get('asset'),
                    'collateral_seized_raw': coll_event.get('collateral_absorbed_raw') or coll_event.get('collateral_raw'),
                    'debt_asset': None,  # Compound v3 base asset determined by market
                    'debt_repaid_raw': debt_event.get('base_paid_out_raw'),
                    # Keep USD values if present
                    'collateral_usd_raw': coll_event.get('usd_value_raw'),
                    'debt_usd_raw': debt_event.get('usd_value_raw'),
                }
                joined_events.append(joined)
        else:
            # No collateral match - keep debt event with null collateral
            unmatched_debt += 1
            joined = {
                'tx_hash': debt_event.get('tx_hash'),
                'log_index': debt_event.get('log_index'),
                'block_number': debt_event.get('block_number'),
                'block_timestamp': debt_event.get('block_timestamp'),
                'protocol': debt_event.get('protocol'),
                'csu': debt_event.get('csu'),
                'event_name': 'Liquidation',
                'contract': debt_event.get('contract') or debt_event.get('contract_address'),
                'borrower': debt_event.get('borrower'),
                'liquidator': debt_event.get('absorber'),
                'collateral_asset': None,
                'collateral_seized_raw': None,
                'debt_asset': None,
                'debt_repaid_raw': debt_event.get('base_paid_out_raw'),
                'debt_usd_raw': debt_event.get('usd_value_raw'),
            }
            joined_events.append(joined)

    if unmatched_debt > 0:
        print(f"  Warning: {unmatched_debt} Compound debt events without matching collateral")

    print(f"  Compound events: {len(compound_debt)} debt + {len(compound_collateral)} collateral -> {len(joined_events)} joined")

    return other_events + joined_events


def normalize_event(event: dict, chain: str) -> dict:
    """Normalize an event to the unified schema."""
    protocol = event.get('protocol', '').lower()

    # Common fields
    normalized = {
        'tx_hash': event.get('tx_hash'),
        'log_index': event.get('log_index'),
        'block_number': event.get('block_number'),
        'block_timestamp': event.get('block_timestamp'),
        'chain': chain,
        'protocol': protocol,
        'csu': event.get('csu'),
        'borrower': event.get('borrower'),
        'liquidator': event.get('liquidator'),
    }

    # Protocol-specific field mapping
    if 'aave' in protocol or 'spark' in protocol:
        normalized['collateral_asset'] = event.get('collateral_asset')
        normalized['collateral_seized_raw'] = event.get('collateral_seized_raw')
        normalized['debt_asset'] = event.get('debt_asset')
        normalized['debt_repaid_raw'] = event.get('debt_repaid_raw')
    elif 'compound_v3' in protocol or ('compound' in protocol and event.get('event_name') == 'Liquidation'):
        # Compound V3: Already normalized by join_compound_events
        normalized['collateral_asset'] = event.get('collateral_asset')
        normalized['collateral_seized_raw'] = event.get('collateral_seized_raw')
        normalized['debt_asset'] = event.get('debt_asset')
        normalized['debt_repaid_raw'] = event.get('debt_repaid_raw')
        # Compound V3 has pre-computed USD values
        normalized['collateral_usd_raw'] = event.get('collateral_usd_raw')
        normalized['debt_usd_raw'] = event.get('debt_usd_raw')
    elif 'compound_v2' in protocol or 'venus' in protocol or 'benqi' in protocol or 'moonwell' in protocol:
        # FIX: Compound V2-style forks emit LiquidateBorrow with different field names
        # The parallel collector outputs: ctoken_collateral, repay_amount_raw, seize_tokens_raw
        # The cToken that emitted the event is the debt market (contract_address)
        normalized['collateral_asset'] = event.get('collateral_asset') or event.get('ctoken_collateral')
        normalized['collateral_seized_raw'] = event.get('collateral_seized_raw') or event.get('seize_tokens_raw')
        normalized['debt_asset'] = event.get('debt_asset') or event.get('contract_address')
        normalized['debt_repaid_raw'] = event.get('debt_repaid_raw') or event.get('repay_amount_raw')
    elif 'fluid' in protocol:
        # FIX: Fluid events use 'debt_token' and 'collateral_token' (not 'debt_asset'/'collateral_asset')
        # Map to unified schema
        normalized['collateral_asset'] = event.get('collateral_asset') or event.get('collateral_token')
        normalized['collateral_seized_raw'] = event.get('collateral_seized_raw')
        normalized['debt_asset'] = event.get('debt_asset') or event.get('debt_token')
        normalized['debt_repaid_raw'] = event.get('debt_repaid_raw')
    else:
        # Generic mapping
        normalized['collateral_asset'] = event.get('collateral_asset')
        normalized['collateral_seized_raw'] = event.get('collateral_seized_raw')
        normalized['debt_asset'] = event.get('debt_asset')
        normalized['debt_repaid_raw'] = event.get('debt_repaid_raw')

    return normalized


def build_token_registry_from_tvl(chain: str) -> Dict[str, dict]:
    """
    Build token registry from TVL bronze data.

    Returns: {address: {symbol, decimals, coingecko_id}}
    """
    registry = {}
    tvl_dir = DATA_DIR / "bronze" / "tvl"

    # Find all TVL directories for this chain
    for csu_dir in tvl_dir.iterdir():
        if not csu_dir.is_dir():
            continue

        # Check if this CSU is for the target chain by reading a sample file
        sample_files = list(csu_dir.glob("*.json"))
        if not sample_files:
            continue

        try:
            with open(sample_files[0]) as f:
                data = json.load(f)

            if data.get('chain') != chain:
                continue

            # Extract token info from market data
            for market in data.get('data', []):
                address = market.get('underlying')
                if address and address not in registry:
                    registry[address] = {
                        'symbol': market.get('symbol'),
                        'decimals': market.get('decimals'),
                        'address': address,
                    }
        except Exception:
            continue

    return registry


def load_token_registry(chain: str) -> Dict[str, dict]:
    """Load token registry from cache or build from TVL data."""
    registry_file = REFERENCE_DIR / f"token_registry_{chain}.json"

    if registry_file.exists():
        with open(registry_file) as f:
            return json.load(f)

    # Build from TVL data
    registry = build_token_registry_from_tvl(chain)

    # Save for future use
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(registry_file, 'w') as f:
        json.dump(registry, f, indent=2)

    return registry


def save_token_registry(chain: str, registry: Dict[str, dict]):
    """Save token registry to cache."""
    registry_file = REFERENCE_DIR / f"token_registry_{chain}.json"
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(registry_file, 'w') as f:
        json.dump(registry, f, indent=2)


def fetch_token_metadata(w3, address: str) -> Optional[dict]:
    """Fetch token metadata from chain via ERC20 calls."""
    try:
        contract = w3.eth.contract(address=w3.to_checksum_address(address), abi=ERC20_ABI)
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        return {
            'symbol': symbol,
            'decimals': decimals,
            'address': address,
        }
    except Exception as e:
        print(f"    Failed to fetch metadata for {address}: {e}")
        return None


def enrich_with_token_metadata(events: List[dict], chain: str, skip_rpc: bool = False) -> Tuple[List[dict], Dict[str, dict]]:
    """Add token metadata (symbol, decimals) to events."""
    registry = load_token_registry(chain)
    print(f"  Loaded token registry: {len(registry)} tokens")

    # Collect all unique token addresses
    token_addresses = set()
    for e in events:
        if e.get('collateral_asset'):
            token_addresses.add(e['collateral_asset'])
        if e.get('debt_asset'):
            token_addresses.add(e['debt_asset'])

    # Find missing tokens
    missing = [addr for addr in token_addresses if addr not in registry]

    if missing and not skip_rpc:
        print(f"  Fetching metadata for {len(missing)} missing tokens...")
        w3 = get_web3(CHAIN_ALIASES.get(chain, chain))

        for addr in missing:
            metadata = fetch_token_metadata(w3, addr)
            if metadata:
                registry[addr] = metadata
                print(f"    Added: {metadata['symbol']} ({addr[:10]}...)")

        # Save updated registry
        save_token_registry(chain, registry)
    elif missing:
        print(f"  Skipping {len(missing)} missing tokens (quick mode)")

    # Enrich events
    for e in events:
        coll_addr = e.get('collateral_asset')
        if coll_addr and coll_addr in registry:
            e['collateral_symbol'] = registry[coll_addr].get('symbol')
            e['collateral_decimals'] = registry[coll_addr].get('decimals')

        debt_addr = e.get('debt_asset')
        if debt_addr and debt_addr in registry:
            e['debt_symbol'] = registry[debt_addr].get('symbol')
            e['debt_decimals'] = registry[debt_addr].get('decimals')

    return events, registry


def load_block_timestamp_cache(chain: str) -> Dict[int, int]:
    """Load block->timestamp cache."""
    cache_file = REFERENCE_DIR / f"block_timestamps_{chain}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            # JSON keys are strings, convert to int
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}


def save_block_timestamp_cache(chain: str, cache: Dict[int, int]):
    """Save block->timestamp cache."""
    cache_file = REFERENCE_DIR / f"block_timestamps_{chain}.json"
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    # Convert int keys to strings for JSON
    with open(cache_file, 'w') as f:
        json.dump({str(k): v for k, v in cache.items()}, f)


def derive_block_timestamps(events: List[dict], chain: str) -> List[dict]:
    """Derive block_timestamp for events missing it."""
    # Find events missing timestamp
    missing_ts = [e for e in events if not e.get('block_timestamp')]

    if not missing_ts:
        return events

    print(f"  Deriving timestamps for {len(missing_ts)} events...", flush=True)

    # Get unique block numbers
    blocks_needed = set(e['block_number'] for e in missing_ts if e.get('block_number'))
    print(f"  Unique blocks needed: {len(blocks_needed)}", flush=True)

    # Load cached block timestamps
    block_cache = load_block_timestamp_cache(chain)
    print(f"  Loaded {len(block_cache)} cached block timestamps", flush=True)

    # For blocks not in cache, fetch from RPC
    uncached_blocks = sorted([b for b in blocks_needed if b not in block_cache])

    if uncached_blocks:
        print(f"  Fetching {len(uncached_blocks)} blocks from RPC...", flush=True)
        w3 = get_web3(CHAIN_ALIASES.get(chain, chain))

        for i, block_num in enumerate(uncached_blocks):
            try:
                block = w3.eth.get_block(block_num)
                block_cache[block_num] = block['timestamp']

                if (i + 1) % 500 == 0:
                    print(f"    Progress: {i + 1}/{len(uncached_blocks)} blocks", flush=True)
                    # Save periodically
                    save_block_timestamp_cache(chain, block_cache)

            except Exception as e:
                if (i + 1) % 100 == 0:
                    print(f"    Warning: Failed block {block_num}: {e}", flush=True)

        # Final save
        save_block_timestamp_cache(chain, block_cache)
        print(f"  Saved {len(block_cache)} block timestamps to cache", flush=True)

    # Update events with timestamps
    updated = 0
    for e in events:
        if not e.get('block_timestamp') and e.get('block_number'):
            ts = block_cache.get(e['block_number'])
            if ts:
                e['block_timestamp'] = ts
                updated += 1

    print(f"  Updated {updated} events with timestamps", flush=True)

    return events


def add_dates(events: List[dict]) -> List[dict]:
    """Add NY timezone date to events."""
    for e in events:
        ts = e.get('block_timestamp')
        if ts:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(NY_TZ)
            e['date'] = dt.date().isoformat()
        else:
            e['date'] = None
    return events


def calculate_amounts(events: List[dict]) -> List[dict]:
    """Calculate human-readable amounts from raw values."""
    for e in events:
        # Collateral amount
        raw = e.get('collateral_seized_raw')
        decimals = e.get('collateral_decimals')
        if raw is not None and decimals is not None:
            try:
                e['collateral_amount'] = float(raw) / (10 ** decimals)
            except (ValueError, TypeError):
                e['collateral_amount'] = None
        else:
            e['collateral_amount'] = None

        # Debt amount
        raw = e.get('debt_repaid_raw')
        decimals = e.get('debt_decimals')
        if raw is not None and decimals is not None:
            try:
                e['debt_amount'] = float(raw) / (10 ** decimals)
            except (ValueError, TypeError):
                e['debt_amount'] = None
        else:
            e['debt_amount'] = None

    return events


def load_price_cache(chain: str) -> Dict[str, Dict[str, float]]:
    """Load price cache: {block_symbol: price}"""
    cache_file = REFERENCE_DIR / f"price_cache_{chain}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return {}


def save_price_cache(chain: str, cache: Dict[str, float]):
    """Save price cache."""
    cache_file = REFERENCE_DIR / f"price_cache_{chain}.json"
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)


# Import Chainlink adapter
try:
    from adapters.prices.chainlink import get_token_price_chainlink, get_stablecoins
    HAS_CHAINLINK = True
except ImportError:
    HAS_CHAINLINK = False
    def get_token_price_chainlink(*args, **kwargs):
        return None
    def get_stablecoins():
        return ['USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'GHO', 'sUSD', 'PYUSD', 'USDS', 'crvUSD']


def get_price_for_date(w3, symbol: str, date: str, representative_block: int,
                       price_cache: Dict[str, float], chain: str = 'ethereum') -> Optional[float]:
    """
    Get token price for a specific date using Chainlink oracle.

    Uses one representative block per date to minimize RPC calls.

    Args:
        chain: Chain name — used to select the correct Chainlink feed address.
    """
    if not symbol:
        return None

    cache_key = f"{date}_{symbol}"

    # Check cache first
    if cache_key in price_cache:
        return price_cache[cache_key]

    # Check stablecoins (assume $1.00) and cache the result
    stablecoins = get_stablecoins()
    if symbol in stablecoins or symbol.upper() in stablecoins:
        price_cache[cache_key] = 1.0
        return 1.0

    # Fetch from Chainlink at representative block
    # FIX: Was hardcoded chain='ethereum' — now uses the actual chain parameter
    # so that Chainlink lookups use the correct feed address for each chain
    price = get_token_price_chainlink(w3, symbol, chain=chain, block=representative_block)

    if price is not None:
        price_cache[cache_key] = price

    return price


def calculate_usd_values(events: List[dict], chain: str, skip_prices: bool = False) -> List[dict]:
    """Calculate USD values for collateral and debt using Chainlink oracles."""

    # First, use pre-computed USD values from Compound if available
    for e in events:
        # Compound v3 provides USD values in raw form (scaled by 1e8)
        if e.get('collateral_usd_raw') is not None:
            try:
                e['collateral_usd'] = float(e['collateral_usd_raw']) / 1e8
            except (ValueError, TypeError):
                e['collateral_usd'] = None
        else:
            e['collateral_usd'] = None

        if e.get('debt_usd_raw') is not None:
            try:
                e['debt_usd'] = float(e['debt_usd_raw']) / 1e8
            except (ValueError, TypeError):
                e['debt_usd'] = None
        else:
            e['debt_usd'] = None

    if skip_prices:
        print("  Skipping price fetching (--skip-prices)")
        return events

    if not HAS_CHAINLINK:
        print("  Warning: Chainlink adapter not available, skipping prices")
        return events

    # Load price cache (date_symbol -> price)
    price_cache = load_price_cache(chain)
    print(f"  Loaded {len(price_cache)} cached prices", flush=True)

    # Get web3 connection
    w3 = get_web3(chain)

    # Build date -> representative_block mapping (use first block of each date)
    date_to_block = {}
    for e in events:
        date = e.get('date')
        block = e.get('block_number')
        if date and block:
            if date not in date_to_block or block < date_to_block[date]:
                date_to_block[date] = block

    # Collect unique (date, symbol) pairs that need prices
    needs_price = set()
    for e in events:
        date = e.get('date')
        if not date:
            continue
        if e.get('collateral_usd') is None and e.get('collateral_symbol') and e.get('collateral_amount'):
            needs_price.add((date, e['collateral_symbol']))
        if e.get('debt_usd') is None and e.get('debt_symbol') and e.get('debt_amount'):
            needs_price.add((date, e['debt_symbol']))

    # Filter to prices not in cache
    uncached = [(d, s) for d, s in needs_price if f"{d}_{s}" not in price_cache]
    print(f"  Unique (date, symbol) pairs needing prices: {len(needs_price):,}", flush=True)
    print(f"  Uncached pairs to fetch: {len(uncached):,}", flush=True)

    # Fetch prices from Chainlink
    if uncached:
        fetched = 0
        stablecoin_count = 0

        for i, (date, symbol) in enumerate(sorted(uncached)):
            block = date_to_block.get(date)
            if not block:
                continue

            price = get_price_for_date(w3, symbol, date, block, price_cache, chain=chain)

            if price is not None:
                if price == 1.0:
                    stablecoin_count += 1
                else:
                    fetched += 1

            # Progress update
            if (i + 1) % 50 == 0:
                print(f"    Progress: {i + 1}/{len(uncached)} pairs ({fetched} Chainlink lookups)", flush=True)
                save_price_cache(chain, price_cache)

        save_price_cache(chain, price_cache)
        print(f"  Fetched {fetched} prices from Chainlink ({stablecoin_count} stablecoins assumed $1)", flush=True)

    # Apply prices to events
    applied_collateral = 0
    applied_debt = 0

    for e in events:
        date = e.get('date')
        if not date:
            continue

        # Collateral USD
        if e.get('collateral_usd') is None:
            symbol = e.get('collateral_symbol')
            amount = e.get('collateral_amount')
            cache_key = f"{date}_{symbol}"
            if symbol and amount and cache_key in price_cache:
                e['collateral_usd'] = amount * price_cache[cache_key]
                applied_collateral += 1

        # Debt USD
        if e.get('debt_usd') is None:
            symbol = e.get('debt_symbol')
            amount = e.get('debt_amount')
            cache_key = f"{date}_{symbol}"
            if symbol and amount and cache_key in price_cache:
                e['debt_usd'] = amount * price_cache[cache_key]
                applied_debt += 1

    print(f"  Applied prices: {applied_collateral:,} collateral, {applied_debt:,} debt", flush=True)

    return events


def validate_events(events: List[dict]) -> List[str]:
    """Run sanity checks on normalized events. Returns list of warning strings."""
    warnings = []

    if not events:
        warnings.append("No events to validate")
        return warnings

    # Check for duplicate (tx_hash, log_index) — indicates dedup failure
    seen = set()
    duplicates = 0
    for e in events:
        key = (e.get('tx_hash'), e.get('log_index'))
        if key in seen:
            duplicates += 1
        seen.add(key)
    if duplicates > 0:
        warnings.append(f"Found {duplicates} duplicate (tx_hash, log_index) pairs")

    # Check for missing critical fields
    missing_tx = sum(1 for e in events if not e.get('tx_hash'))
    missing_block = sum(1 for e in events if not e.get('block_number'))
    missing_borrower = sum(1 for e in events if not e.get('borrower'))
    if missing_tx:
        warnings.append(f"{missing_tx} events missing tx_hash")
    if missing_block:
        warnings.append(f"{missing_block} events missing block_number")
    if missing_borrower:
        warnings.append(f"{missing_borrower} events missing borrower")

    # Check for negative amounts
    neg_collateral = sum(1 for e in events if (e.get('collateral_amount') or 0) < 0)
    neg_debt = sum(1 for e in events if (e.get('debt_amount') or 0) < 0)
    if neg_collateral:
        warnings.append(f"{neg_collateral} events with negative collateral_amount")
    if neg_debt:
        warnings.append(f"{neg_debt} events with negative debt_amount")

    # Check for suspiciously large USD values (> $1B single liquidation)
    huge_coll = sum(1 for e in events if (e.get('collateral_usd') or 0) > 1e9)
    huge_debt = sum(1 for e in events if (e.get('debt_usd') or 0) > 1e9)
    if huge_coll:
        warnings.append(f"{huge_coll} events with collateral_usd > $1B (possible scaling error)")
    if huge_debt:
        warnings.append(f"{huge_debt} events with debt_usd > $1B (possible scaling error)")

    # Check collateral/debt USD ratio (should be close, typically 1.0-1.15x)
    both_usd = [e for e in events if (e.get('collateral_usd') or 0) > 0 and (e.get('debt_usd') or 0) > 0]
    if both_usd:
        extreme_ratio = 0
        for e in both_usd:
            ratio = e['collateral_usd'] / e['debt_usd']
            if ratio > 3.0 or ratio < 0.3:
                extreme_ratio += 1
        if extreme_ratio:
            warnings.append(f"{extreme_ratio}/{len(both_usd)} events with extreme collateral/debt ratio (>3x or <0.3x)")

    # Coverage stats (informational)
    has_date = sum(1 for e in events if e.get('date'))
    has_coll_usd = sum(1 for e in events if e.get('collateral_usd') is not None)
    has_debt_usd = sum(1 for e in events if e.get('debt_usd') is not None)
    print(f"  Coverage: date={has_date}/{len(events)}, "
          f"collateral_usd={has_coll_usd}/{len(events)}, "
          f"debt_usd={has_debt_usd}/{len(events)}")

    return warnings


def export_to_parquet(events: List[dict], chain: str):
    """Export events to parquet file."""
    if not HAS_PANDAS:
        # Fallback to JSON if pandas not available
        output_file = SILVER_DIR / chain / "liquidations.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"  Exported to {output_file} (JSON fallback)")
        return

    # Define column order
    columns = [
        'tx_hash', 'log_index', 'block_number', 'block_timestamp', 'date',
        'chain', 'protocol', 'csu', 'borrower', 'liquidator',
        'collateral_asset', 'collateral_symbol', 'collateral_decimals', 'collateral_amount', 'collateral_usd',
        'debt_asset', 'debt_symbol', 'debt_decimals', 'debt_amount', 'debt_usd',
    ]

    df = pd.DataFrame(events)

    # Ensure all columns exist
    for col in columns:
        if col not in df.columns:
            df[col] = None

    # Reorder and select columns
    df = df[columns]

    # Output
    output_file = SILVER_DIR / chain / "liquidations.parquet"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_file, index=False)

    print(f"  Exported to {output_file}")
    print(f"  Shape: {df.shape}")


def print_summary(events: List[dict]):
    """Print summary statistics."""
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    print(f"\nTotal events: {len(events):,}")

    # By protocol
    from collections import Counter
    protocol_counts = Counter(e.get('protocol') for e in events)
    print("\nBy protocol:")
    for proto, count in protocol_counts.most_common():
        print(f"  {proto}: {count:,}")

    # USD coverage
    has_collateral_usd = sum(1 for e in events if e.get('collateral_usd') is not None)
    has_debt_usd = sum(1 for e in events if e.get('debt_usd') is not None)
    print(f"\nUSD coverage:")
    print(f"  Collateral USD: {has_collateral_usd:,} / {len(events):,} ({100*has_collateral_usd/len(events):.1f}%)")
    print(f"  Debt USD: {has_debt_usd:,} / {len(events):,} ({100*has_debt_usd/len(events):.1f}%)")

    # Date range
    dates = [e.get('date') for e in events if e.get('date')]
    if dates:
        print(f"\nDate range: {min(dates)} to {max(dates)}")

    # Total USD liquidated
    total_collateral_usd = sum(e.get('collateral_usd', 0) or 0 for e in events)
    total_debt_usd = sum(e.get('debt_usd', 0) or 0 for e in events)
    print(f"\nTotal USD values:")
    print(f"  Collateral seized: ${total_collateral_usd:,.2f}")
    print(f"  Debt repaid: ${total_debt_usd:,.2f}")


def main():
    parser = argparse.ArgumentParser(description='Build silver liquidation data')
    parser.add_argument('--chain', required=True, help='Chain to process (e.g., ethereum)')
    parser.add_argument('--skip-prices', action='store_true', help='Skip fetching prices from CoinGecko')
    parser.add_argument('--quick', action='store_true', help='Quick mode: skip RPC calls for timestamps and missing tokens')

    args = parser.parse_args()
    chain = args.chain
    quick_mode = args.quick

    print("="*70)
    print(f"SILVER LIQUIDATION PIPELINE - {chain.upper()}")
    if quick_mode:
        print("(QUICK MODE - skipping RPC calls)")
    print("="*70)

    # Step 1: Load bronze data
    print("\n[1/8] Loading bronze data...")
    events = load_bronze_events(chain)
    print(f"  Loaded {len(events):,} events (excluding Gearbox)")

    # Step 2: Join Compound events
    print("\n[2/8] Joining Compound events...")
    events = join_compound_events(events)

    # Step 3: Normalize schema
    print("\n[3/8] Normalizing schema...")
    events = [normalize_event(e, chain) for e in events]
    print(f"  Normalized {len(events):,} events")

    # Step 4: Enrich with token metadata
    print("\n[4/8] Enriching with token metadata...")
    events, registry = enrich_with_token_metadata(events, chain, skip_rpc=quick_mode)

    # Step 5: Derive missing timestamps
    print("\n[5/8] Deriving block timestamps...")
    if quick_mode:
        print("  Skipping RPC timestamp derivation (quick mode)")
    else:
        events = derive_block_timestamps(events, chain)
    events = add_dates(events)

    # Step 6: Calculate amounts and USD values
    print("\n[6/8] Calculating amounts and USD values...")
    events = calculate_amounts(events)
    events = calculate_usd_values(events, chain, skip_prices=args.skip_prices or quick_mode)

    # Step 7: Validate
    print("\n[7/8] Running validation checks...")
    warnings = validate_events(events)
    if warnings:
        print(f"  Found {len(warnings)} warnings:")
        for w in warnings[:15]:
            print(f"    {w}")
        if len(warnings) > 15:
            print(f"    ... and {len(warnings) - 15} more")
    else:
        print("  All checks passed")

    # Step 8: Export
    print("\n[8/8] Exporting to parquet...")
    export_to_parquet(events, chain)

    # Summary
    print_summary(events)


if __name__ == '__main__':
    main()
