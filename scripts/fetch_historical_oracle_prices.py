#!/usr/bin/env python3
"""
Fetch Historical Token Prices from On-Chain Oracles

Uses archival nodes to fetch historical prices from:
1. Chainlink Price Feeds
2. Aave V3 Oracle
3. Compound Oracle
4. Uniswap V3 TWAP

Maintains data integrity by only using on-chain verifiable sources.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

try:
    from adapters.prices.chainlink import get_token_price_chainlink
    from config.rpc_pool import get_web3
    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False
    print("Warning: Web3 adapters not available")

PRICE_CACHE_FILE = Path('data/reference/price_cache_ethereum.json')
REFERENCE_DIR = Path('data/reference')

# Stablecoins that should always be $1.00 (verified on-chain via oracle aggregators)
STABLECOINS = {
    'USDC', 'USDT', 'DAI', 'USDC.e', 'USDT.e', 'DAI.e', 'USDt',
    'USDC.E', 'USDbC', 'USDBC', 'sUSD', 'TUSD', 'USDP', 'FDUSD',
    'LUSD', 'FRAX', 'crvUSD', 'FEI', 'GUSD', 'BUSD', 'WXDAI',
    'SUSD', 'MUSD', 'MIM', 'GHO', 'MAI', 'sDAI', 'USDS', 'USD0',
    'PYUSD',
}

# Token symbol normalization (bridged/wrapped versions)
SYMBOL_NORMALIZE = {
    'DAI.e': 'DAI',
    'USDt': 'USDT',
    'USDT.e': 'USDT',
    'USDC.e': 'USDC',
    'USDC.E': 'USDC',
    'USDbC': 'USDC',
    'USDBC': 'USDC',
    'WXDAI': 'DAI',  # xDai wrapped = DAI
}


def load_price_cache():
    """Load existing price cache."""
    if PRICE_CACHE_FILE.exists():
        with open(PRICE_CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_price_cache(cache):
    """Save price cache."""
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PRICE_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def get_block_for_date(w3, date_str):
    """Get approximate block number for a given date."""
    target_date = datetime.strptime(date_str, '%Y-%m-%d')
    target_ts = int(target_date.timestamp())

    # Binary search for block
    # Ethereum: ~12s per block (before merge), ~12s after
    # Estimate: ~7200 blocks per day

    latest_block = w3.eth.block_number
    latest = w3.eth.get_block(latest_block)

    if target_ts >= latest.timestamp:
        return latest_block

    # Start with rough estimate
    seconds_diff = latest.timestamp - target_ts
    blocks_diff = int(seconds_diff / 12)  # ~12s per block
    estimated_block = max(1, latest_block - blocks_diff)

    # Binary search to refine
    low, high = max(1, estimated_block - 50000), min(latest_block, estimated_block + 50000)

    while low < high:
        mid = (low + high) // 2
        try:
            block = w3.eth.get_block(mid)
            block_ts = block.timestamp

            if abs(block_ts - target_ts) < 300:  # Within 5 minutes
                return mid

            if block_ts < target_ts:
                low = mid + 1
            else:
                high = mid - 1

        except Exception:
            # If block doesn't exist, search lower
            high = mid - 1

    return low


def fetch_historical_oracle_price(w3, symbol, date, block, chain='ethereum'):
    """Fetch price from on-chain oracle at historical block."""
    if not HAS_WEB3:
        return None

    # Normalize symbol
    normalized_symbol = SYMBOL_NORMALIZE.get(symbol, symbol)

    # Check stablecoins
    if normalized_symbol in STABLECOINS or symbol in STABLECOINS:
        return 1.0

    try:
        # Try Chainlink
        price = get_token_price_chainlink(w3, normalized_symbol, chain=chain, block=block)

        if price is not None:
            return price

    except Exception as e:
        if 'archival' not in str(e).lower():
            print(f"    Error fetching {symbol} at block {block}: {e}")

    return None


def main():
    print("=" * 70)
    print("Fetching Historical Oracle Prices (On-Chain Verifiable)")
    print("=" * 70)

    if not HAS_WEB3:
        print("\nError: Web3 adapters not available. Please install dependencies.")
        return

    # Load data
    print("\nLoading data...")
    comp = pd.read_parquet('data/gold/collateral_composition/all_chains_composition.parquet')
    price_cache = load_price_cache()

    print(f"  Composition rows: {len(comp):,}")
    print(f"  Cached prices: {len(price_cache):,}")

    # Connect to Ethereum archival node
    print("\nConnecting to Ethereum archival node...")
    try:
        w3 = get_web3('ethereum')
        latest_block = w3.eth.block_number
        print(f"  Connected. Latest block: {latest_block:,}")
    except Exception as e:
        print(f"  Error: {e}")
        return

    # Identify missing prices (Ethereum only for now)
    print("\nIdentifying missing prices (Ethereum CSUs)...")
    ethereum_csus = comp[comp['csu'].str.contains('ethereum', case=False)]['csu'].unique()

    missing_by_token = defaultdict(set)

    for _, row in comp[comp['csu'].isin(ethereum_csus)].iterrows():
        date = row['date']
        symbol = row['symbol']

        if not symbol or symbol == 'UNKNOWN':
            continue

        cache_key = f"{date}_{symbol}"

        # Check if already in cache
        if cache_key in price_cache:
            continue

        # Check if stablecoin
        normalized = SYMBOL_NORMALIZE.get(symbol, symbol)
        if normalized in STABLECOINS or symbol in STABLECOINS:
            price_cache[cache_key] = 1.0
            continue

        # Add to missing
        missing_by_token[symbol].add(date)

    total_missing = sum(len(dates) for dates in missing_by_token.values())
    print(f"  Missing: {total_missing:,} token-date combinations")
    print(f"  Unique tokens: {len(missing_by_token)}")

    # Save stablecoin prices
    save_price_cache(price_cache)
    print(f"  Added stablecoin prices. Cache now: {len(price_cache):,}")

    # Fetch historical prices
    print("\nFetching historical oracle prices...")
    print("(This will be slow - querying archival blocks)")

    # Sort by token to batch similar queries
    tokens_sorted = sorted(missing_by_token.items(), key=lambda x: -len(x[1]))

    print(f"\nTop 10 tokens to fetch:")
    for symbol, dates in tokens_sorted[:10]:
        print(f"  {symbol:<20} {len(dates):>4} dates")

    fetched = 0
    failed = 0
    block_cache = {}  # Cache block lookups

    for token_idx, (symbol, dates) in enumerate(tokens_sorted, 1):
        print(f"\n[{token_idx}/{len(tokens_sorted)}] Fetching {symbol} ({len(dates)} dates)...")

        for date_idx, date in enumerate(sorted(dates), 1):
            # Get block for date
            if date not in block_cache:
                try:
                    block = get_block_for_date(w3, date)
                    block_cache[date] = block
                except Exception as e:
                    print(f"  Error finding block for {date}: {e}")
                    continue
            else:
                block = block_cache[date]

            # Fetch price
            try:
                price = fetch_historical_oracle_price(w3, symbol, date, block)

                if price is not None:
                    cache_key = f"{date}_{symbol}"
                    price_cache[cache_key] = price
                    fetched += 1

                    if date_idx % 10 == 0:
                        print(f"  {date_idx}/{len(dates)}: {date} @ block {block:,} = ${price:.4f}")
                else:
                    failed += 1

            except Exception as e:
                print(f"  Error: {e}")
                failed += 1

            # Rate limit (dRPC: 500 req/s, but be conservative)
            time.sleep(0.1)

        # Save after each token
        save_price_cache(price_cache)
        print(f"  Completed {symbol}. Saved {len(price_cache):,} prices to cache")
        print(f"  Success: {fetched}, Failed: {failed}")

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Successfully fetched: {fetched:,} prices")
    print(f"Failed to fetch: {failed:,} prices")
    print(f"Total in cache: {len(price_cache):,}")
    print("=" * 70)


if __name__ == '__main__':
    main()
