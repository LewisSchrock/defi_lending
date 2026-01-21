"""
Unified Price Service with Caching

Provides token prices with:
1. Local cache lookup (fastest)
2. Chainlink on-chain oracle (primary source)
3. DefiLlama API (free, unlimited history)
4. CoinGecko API (demo key, 1 year history)
5. Stablecoin assumption ($1.00) as last resort

Cache Structure:
    data/cache/prices/
    ├── daily_prices.json       # {date: {token: price}}
    └── token_not_found.json    # {token: [dates_tried]} - avoid repeated failures
"""

import json
import threading
from pathlib import Path
from typing import Dict, Optional, Set
from datetime import datetime
from web3 import Web3

from .chainlink import get_token_price_chainlink, get_stablecoins
from .defillama import get_token_price_defillama, STABLECOINS as DL_STABLECOINS
from .coingecko import get_token_price_coingecko, STABLECOINS as CG_STABLECOINS

# Block cache for date->block lookups
BLOCK_CACHE_DIR = Path('data/cache')

# Cache paths
CACHE_DIR = Path('data/cache/prices')
DAILY_CACHE_FILE = CACHE_DIR / 'daily_prices.json'
NOT_FOUND_FILE = CACHE_DIR / 'token_not_found.json'

# Thread safety
_cache_lock = threading.Lock()
_price_cache: Dict[str, Dict[str, float]] = {}  # {date: {token: price}}
_not_found_cache: Dict[str, Set[str]] = {}  # {token: {dates}}
_cache_loaded = False


def _ensure_cache_loaded():
    """Load cache from disk if not already loaded."""
    global _price_cache, _not_found_cache, _cache_loaded

    if _cache_loaded:
        return

    with _cache_lock:
        if _cache_loaded:
            return

        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Load daily prices cache
        if DAILY_CACHE_FILE.exists():
            try:
                with open(DAILY_CACHE_FILE) as f:
                    _price_cache = json.load(f)
            except Exception:
                _price_cache = {}

        # Load not-found cache
        if NOT_FOUND_FILE.exists():
            try:
                with open(NOT_FOUND_FILE) as f:
                    data = json.load(f)
                    _not_found_cache = {k: set(v) for k, v in data.items()}
            except Exception:
                _not_found_cache = {}

        _cache_loaded = True


def _save_cache():
    """Save cache to disk."""
    with _cache_lock:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Save daily prices
        with open(DAILY_CACHE_FILE, 'w') as f:
            json.dump(_price_cache, f, indent=2)

        # Save not-found cache (convert sets to lists)
        with open(NOT_FOUND_FILE, 'w') as f:
            data = {k: list(v) for k, v in _not_found_cache.items()}
            json.dump(data, f, indent=2)


def _get_block_for_date(chain: str, date_str: str) -> Optional[int]:
    """Look up block number for a date from block cache."""
    # Try to find a matching block cache file
    cache_patterns = [
        BLOCK_CACHE_DIR / f'{chain}_blocks_2024-01-01_2024-12-31.json',
        BLOCK_CACHE_DIR / f'{chain}_blocks_{date_str[:7]}-01_{date_str[:7]}-31.json',
    ]

    for cache_file in cache_patterns:
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    blocks = json.load(f)
                    if date_str in blocks:
                        return blocks[date_str].get('block')
            except Exception:
                pass

    return None


def _normalize_symbol(symbol: str) -> str:
    """Normalize token symbol for cache lookups."""
    s = symbol.upper().strip()
    # Handle common variations
    if s in ('WETH', 'ETH'):
        return 'ETH'
    if s in ('WBTC', 'BTC'):
        return 'BTC'
    return s


def _is_stablecoin(symbol: str) -> bool:
    """Check if token is a stablecoin."""
    s = _normalize_symbol(symbol)
    all_stables = set(get_stablecoins()) | DL_STABLECOINS | CG_STABLECOINS
    return s in all_stables


def get_token_price(
    token_symbol: str,
    date_str: str,
    web3: Optional[Web3] = None,
    chain: str = 'ethereum',
    block: Optional[int] = None,
    use_api_fallback: bool = True,
    verbose: bool = False
) -> Optional[float]:
    """
    Get token price with caching.

    Priority:
    1. Cache lookup
    2. Chainlink oracle (if web3 provided)
    3. DefiLlama API (free, unlimited history)
    4. CoinGecko API (demo key, 1 year history)
    5. Stablecoin check ($1.00) - last resort

    Args:
        token_symbol: Token symbol (e.g., 'WETH', 'USDC')
        date_str: Date in YYYY-MM-DD format
        web3: Web3 instance for Chainlink (optional)
        chain: Chain name for Chainlink
        block: Block number for Chainlink (optional)
        use_api_fallback: Whether to use DefiLlama/CoinGecko as fallback
        verbose: Print debug info about price lookups

    Returns:
        Price in USD as float, or None if not available
    """
    _ensure_cache_loaded()

    symbol = _normalize_symbol(token_symbol)

    # 1. Check cache first
    with _cache_lock:
        if date_str in _price_cache and symbol in _price_cache[date_str]:
            return _price_cache[date_str][symbol]

        # Check if we already tried and failed for this token/date
        if symbol in _not_found_cache and date_str in _not_found_cache[symbol]:
            return None

    price = None

    # 2. Try Chainlink first (if web3 provided)
    if web3 is not None:
        # Look up block number from cache if not provided
        lookup_block = block
        if lookup_block is None:
            lookup_block = _get_block_for_date(chain, date_str)

        price = get_token_price_chainlink(web3, symbol, chain, lookup_block)
        if price is not None:
            if verbose:
                print(f"    [Chainlink] {symbol} @ {date_str}: ${price:,.4f}")
            _cache_price(symbol, date_str, price)
            return price

    # 3. Try DefiLlama (free, unlimited historical data)
    if use_api_fallback and price is None:
        price = get_token_price_defillama(symbol, date_str)
        if price is not None:
            if verbose:
                print(f"    [DefiLlama] {symbol} @ {date_str}: ${price:,.4f}")
            _cache_price(symbol, date_str, price)
            return price

    # 4. Try CoinGecko (demo key, 1 year history limit)
    if use_api_fallback and price is None:
        price = get_token_price_coingecko(symbol, date_str)
        if price is not None:
            if verbose:
                print(f"    [CoinGecko] {symbol} @ {date_str}: ${price:,.4f}")
            _cache_price(symbol, date_str, price)
            return price

    # 5. Stablecoins return $1.00 as last resort
    if _is_stablecoin(symbol):
        if verbose:
            print(f"    [Stablecoin] {symbol} @ {date_str}: $1.00")
        _cache_price(symbol, date_str, 1.0)
        return 1.0

    # Mark as not found to avoid repeated lookups
    if price is None:
        if verbose:
            print(f"    [NOT FOUND] {symbol} @ {date_str}")
        _mark_not_found(symbol, date_str)

    return price


def _cache_price(symbol: str, date_str: str, price: float):
    """Cache a price."""
    with _cache_lock:
        if date_str not in _price_cache:
            _price_cache[date_str] = {}
        _price_cache[date_str][symbol] = price

    # Save periodically (every 10 new entries)
    total_entries = sum(len(v) for v in _price_cache.values())
    if total_entries % 10 == 0:
        _save_cache()


def _mark_not_found(symbol: str, date_str: str):
    """Mark a token/date as not found."""
    with _cache_lock:
        if symbol not in _not_found_cache:
            _not_found_cache[symbol] = set()
        _not_found_cache[symbol].add(date_str)


def get_cached_price(token_symbol: str, date_str: str) -> Optional[float]:
    """Get price from cache only (no API calls)."""
    _ensure_cache_loaded()
    symbol = _normalize_symbol(token_symbol)

    if _is_stablecoin(symbol):
        return 1.0

    with _cache_lock:
        return _price_cache.get(date_str, {}).get(symbol)


def batch_get_prices(
    tokens: list,
    date_str: str,
    web3: Optional[Web3] = None,
    chain: str = 'ethereum',
    block: Optional[int] = None
) -> Dict[str, Optional[float]]:
    """
    Get prices for multiple tokens.

    Args:
        tokens: List of token symbols
        date_str: Date in YYYY-MM-DD format
        web3: Web3 instance for Chainlink
        chain: Chain name
        block: Block number

    Returns:
        Dict of {symbol: price} (None for unavailable)
    """
    results = {}

    for token in tokens:
        results[token] = get_token_price(
            token, date_str, web3, chain, block
        )

    return results


def save_all():
    """Force save all caches to disk."""
    _save_cache()


def clear_not_found(tokens: list = None) -> int:
    """
    Clear not-found cache entries to allow re-trying failed lookups.

    Args:
        tokens: List of token symbols to clear (None = clear all)

    Returns:
        Number of entries cleared
    """
    _ensure_cache_loaded()
    global _not_found_cache

    with _cache_lock:
        if tokens is None:
            # Clear all
            count = sum(len(v) for v in _not_found_cache.values())
            _not_found_cache = {}
        else:
            count = 0
            for token in tokens:
                normalized = _normalize_symbol(token)
                if normalized in _not_found_cache:
                    count += len(_not_found_cache[normalized])
                    del _not_found_cache[normalized]

    _save_cache()
    return count


def get_not_found_tokens() -> Dict[str, int]:
    """Get dict of tokens that couldn't be found and their date counts."""
    _ensure_cache_loaded()
    with _cache_lock:
        return {k: len(v) for k, v in _not_found_cache.items()}


def get_cache_stats() -> Dict:
    """Get cache statistics."""
    _ensure_cache_loaded()

    with _cache_lock:
        total_prices = sum(len(v) for v in _price_cache.values())
        total_dates = len(_price_cache)
        unique_tokens = set()
        for prices in _price_cache.values():
            unique_tokens.update(prices.keys())

        not_found_count = sum(len(v) for v in _not_found_cache.values())

        return {
            'total_prices': total_prices,
            'total_dates': total_dates,
            'unique_tokens': len(unique_tokens),
            'tokens': list(unique_tokens),
            'not_found_entries': not_found_count
        }


def preload_prices_for_date(
    date_str: str,
    tokens: list,
    web3: Optional[Web3] = None,
    chain: str = 'ethereum',
    block: Optional[int] = None,
    verbose: bool = False
) -> Dict[str, Optional[float]]:
    """
    Preload prices for a specific date.
    Useful for batch processing.

    Args:
        date_str: Date in YYYY-MM-DD format
        tokens: List of token symbols to preload
        web3: Web3 instance
        chain: Chain name
        block: Block number
        verbose: Print progress

    Returns:
        Dict of {symbol: price}
    """
    results = {}

    for i, token in enumerate(tokens):
        price = get_token_price(token, date_str, web3, chain, block)
        results[token] = price

        if verbose and (i + 1) % 10 == 0:
            print(f"  Loaded {i + 1}/{len(tokens)} prices for {date_str}")

    # Save after batch
    _save_cache()

    return results


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config.rpc_pool import get_web3

    print("Testing Price Service")
    print("=" * 50)

    # Get web3 for Chainlink
    w3 = get_web3('ethereum')
    print(f"Connected to Ethereum, block {w3.eth.block_number:,}")

    # Test tokens
    test_tokens = ['ETH', 'WETH', 'WBTC', 'USDC', 'ARB', 'wstETH', 'weETH']
    test_date = '2024-06-15'

    print(f"\nFetching prices for {test_date}:")
    for token in test_tokens:
        price = get_token_price(token, test_date, w3)
        if price:
            print(f"  {token}: ${price:,.2f}")
        else:
            print(f"  {token}: Not available")

    # Save cache
    save_all()

    # Show stats
    stats = get_cache_stats()
    print(f"\nCache stats:")
    print(f"  Total prices cached: {stats['total_prices']}")
    print(f"  Unique tokens: {stats['unique_tokens']}")
    print(f"  Dates covered: {stats['total_dates']}")
