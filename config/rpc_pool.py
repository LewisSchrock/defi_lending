"""
Multi-Account Alchemy Connection Pool with Rate Limiting

Rotates across verified Alchemy accounts and respects free tier limits:
- Free tier: 300 compute units/second (CUs) per account
- eth_call: ~26 CUs
- eth_getLogs: ~75 CUs
- eth_getBlockByNumber: ~16 CUs

With 5 accounts: ~1,500 CUs/second total capacity
- ~57 eth_call/second distributed
- ~20 eth_getLogs/second distributed

Uses verified key-chain mapping from test_key_mapping.py to ensure
we only use keys that work for each chain.

Includes automatic key blacklisting: if a key returns 401 Unauthorized,
it is removed from rotation for that chain.

Usage:
    from config.rpc_pool import get_web3, blacklist_key

    w3 = get_web3('ethereum')
    block = w3.eth.block_number
"""

import os
import json
import threading
import time
from pathlib import Path
from web3 import Web3
from typing import Dict, List, Optional, Set

# Load API keys from environment
ALCHEMY_KEYS = {
    'key_1': os.environ.get('ALCHEMY_KEY_1'),
    'key_2': os.environ.get('ALCHEMY_KEY_2'),
    'key_3': os.environ.get('ALCHEMY_KEY_3'),
    'key_4': os.environ.get('ALCHEMY_KEY_4'),
    'key_5': os.environ.get('ALCHEMY_KEY_5'),
    'key_6': os.environ.get('ALCHEMY_KEY_6'),
}

# Remove None values
ALCHEMY_KEYS = {k: v for k, v in ALCHEMY_KEYS.items() if v}

if len(ALCHEMY_KEYS) == 0:
    raise ValueError("No Alchemy API keys found! Set ALCHEMY_KEY_1, ALCHEMY_KEY_2, etc.")

# Verified key-chain mapping (from test_key_mapping.py)
# Only use keys that have been tested and work for each chain
CHAIN_KEY_MAPPING = {
    "ethereum": ["key_1", "key_2", "key_3", "key_4", "key_5", "key_6"],
    "arbitrum": ["key_1", "key_2", "key_3", "key_5", "key_6"],
    "optimism": ["key_1", "key_2", "key_3", "key_5", "key_6"],
    "base": ["key_1", "key_2", "key_3", "key_4", "key_5", "key_6"],
    "polygon": ["key_1", "key_2", "key_3", "key_4", "key_5", "key_6"],
    "avalanche": ["key_1", "key_2", "key_3", "key_4", "key_5", "key_6"],
    "binance": ["key_1", "key_2", "key_3", "key_5", "key_6"],
    "linea": ["key_1", "key_2", "key_3", "key_5", "key_6"],
    "gnosis": ["key_1", "key_2", "key_3", "key_5", "key_6"],
    "plasma": ["key_1", "key_2", "key_3", "key_4", "key_5", "key_6"],
    "sonic": [],  # Force public RPC - new chain, unstable on Alchemy
}

# Alchemy chain patterns
ALCHEMY_CHAINS = {
    'ethereum': 'eth-mainnet',
    'arbitrum': 'arb-mainnet',
    'optimism': 'opt-mainnet',
    'base': 'base-mainnet',
    'polygon': 'polygon-mainnet',
    'avalanche': 'avax-mainnet',
    'binance': 'bnb-mainnet',
    'plasma': 'plasma-mainnet',
    'linea': 'linea-mainnet',
    'gnosis': 'gnosis-mainnet',
}

# Public RPC fallbacks (no auth needed)
PUBLIC_RPCS = {
    'ethereum': [
        'https://eth.llamarpc.com',
        'https://rpc.ankr.com/eth',
    ],
    'arbitrum': [
        'https://arb1.arbitrum.io/rpc',
        'https://arbitrum.llamarpc.com',
    ],
    'optimism': [
        'https://mainnet.optimism.io',
        'https://optimism.llamarpc.com',
    ],
    'base': [
        'https://mainnet.base.org',
        'https://base.llamarpc.com',
    ],
    'polygon': [
        'https://polygon-rpc.com',
        'https://polygon.llamarpc.com',
        'https://polygon-bor-rpc.publicnode.com',
        'https://rpc.ankr.com/polygon',
    ],
    'avalanche': [
        'https://api.avax.network/ext/bc/C/rpc',
        'https://avalanche.public-rpc.com',
    ],
    'binance': [
        'https://bsc-dataseed.binance.org',
        'https://bsc.publicnode.com',
    ],
    'plasma': [
        'https://zkevm-rpc.com',  # Plasma has NO working Alchemy keys
    ],
    'linea': [
        'https://rpc.linea.build',
    ],
    'gnosis': [
        'https://rpc.gnosischain.com',
    ],
    'ink': [
        'https://rpc-qnd.inkonchain.com',
    ],
    'cronos': [
        'https://evm.cronos.org',
    ],
    'flare': [
        'https://flare-api.flare.network/ext/C/rpc',
        'https://flare.solidifi.app/ext/bc/C/rpc',
    ],
    'meter': [
        'https://rpc.meter.io',
    ],
    'scroll': [
        'https://rpc.scroll.io',
        'https://scroll.blockpi.network/v1/rpc/public',
    ],
    'sonic': [
        'https://rpc.soniclabs.com',
    ],
}

# ============================================================================
# Key Blacklist Management
# ============================================================================
# Blacklist file stores keys that returned 401 Unauthorized
BLACKLIST_FILE = Path('data/.key_blacklist.json')
_blacklist_lock = threading.Lock()

def _load_blacklist() -> Dict[str, List[str]]:
    """Load blacklist from file. Returns {chain: [key_name, ...]}"""
    if BLACKLIST_FILE.exists():
        try:
            with open(BLACKLIST_FILE) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_blacklist(blacklist: Dict[str, List[str]]):
    """Save blacklist to file."""
    BLACKLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BLACKLIST_FILE, 'w') as f:
        json.dump(blacklist, f, indent=2)

def blacklist_key(chain: str, key_name: str, reason: str = "401 Unauthorized"):
    """
    Blacklist a key for a specific chain.

    This removes the key from rotation and persists the blacklist to disk.
    Called automatically when a 401 error is detected.
    """
    with _blacklist_lock:
        blacklist = _load_blacklist()

        if chain not in blacklist:
            blacklist[chain] = []

        if key_name not in blacklist[chain]:
            blacklist[chain].append(key_name)
            _save_blacklist(blacklist)
            print(f"[RPC Pool] 🚫 Blacklisted {key_name} for {chain}: {reason}")

            # Force pool rebuild on next get_web3 call
            if chain in _POOL_CACHE:
                del _POOL_CACHE[chain]

def get_blacklisted_keys(chain: str) -> Set[str]:
    """Get set of blacklisted key names for a chain."""
    blacklist = _load_blacklist()
    return set(blacklist.get(chain, []))

def clear_blacklist(chain: Optional[str] = None):
    """Clear blacklist for a chain or all chains."""
    with _blacklist_lock:
        if chain:
            blacklist = _load_blacklist()
            if chain in blacklist:
                del blacklist[chain]
                _save_blacklist(blacklist)
                if chain in _POOL_CACHE:
                    del _POOL_CACHE[chain]
                print(f"[RPC Pool] Cleared blacklist for {chain}")
        else:
            _save_blacklist({})
            _POOL_CACHE.clear()
            print("[RPC Pool] Cleared all blacklists")


class RateLimiter:
    """
    Rate limiter for Alchemy free tier compliance.

    Free tier: 300 compute units/second (CUs)
    - eth_call: 26 CUs
    - eth_getLogs: 75 CUs
    - eth_getBlockByNumber: 16 CUs

    Conservative approach: limit to ~11 calls/second per key
    This gives us headroom regardless of call type.
    With 6 keys = 66 calls/sec total (~300 CUs/sec/key budget)
    """

    def __init__(self, calls_per_second: float = 11):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
        self.lock = threading.Lock()
        # Backoff state for 429/503 errors
        self.backoff_until = 0
        self.consecutive_errors = 0
        self.max_backoff = 300  # 5 minutes max backoff

    def wait(self):
        """Wait if necessary to respect rate limit (normal interval only)"""
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            self.last_call = time.time()

    def is_backing_off(self) -> bool:
        """Check if we're currently in backoff mode due to rate limits"""
        with self.lock:
            return time.time() < self.backoff_until

    def get_backoff_remaining(self) -> float:
        """Get seconds remaining in backoff period (0 if not backing off)"""
        with self.lock:
            remaining = self.backoff_until - time.time()
            return max(0, remaining)

    def report_error(self, is_rate_limit: bool = False):
        """Report an error - triggers backoff for rate limits (429/503)"""
        with self.lock:
            if is_rate_limit:
                self.consecutive_errors += 1
                # Exponential backoff: 5s, 10s, 20s, 40s... up to max_backoff
                backoff_time = min(5 * (2 ** (self.consecutive_errors - 1)), self.max_backoff)
                self.backoff_until = time.time() + backoff_time
                print(f"[RateLimiter] Rate limit hit ({self.consecutive_errors}x), backing off {backoff_time}s")

    def report_success(self):
        """Report a successful call - resets backoff state"""
        with self.lock:
            if self.consecutive_errors > 0:
                self.consecutive_errors = 0
                self.backoff_until = 0



class AlchemyConnectionPool:
    """
    Round-robin connection pool using only verified working keys.

    Thread-safe rotation with per-key rate limiting for Alchemy free tier compliance.
    Excludes blacklisted keys.
    """

    def __init__(self, chain: str):
        self.chain = chain
        self.providers: List[tuple] = []  # List of (Web3, RateLimiter, key_name) tuples
        self.current_idx = 0
        self.lock = threading.Lock()

        # Get blacklisted keys for this chain
        blacklisted = get_blacklisted_keys(chain)

        # Build providers for this chain using only verified working keys
        if chain in ALCHEMY_CHAINS:
            chain_pattern = ALCHEMY_CHAINS[chain]
            working_keys = CHAIN_KEY_MAPPING.get(chain, [])

            # Filter out blacklisted keys
            available_keys = [k for k in working_keys if k not in blacklisted]

            if blacklisted:
                print(f"[RPC Pool] {chain}: Excluding {len(blacklisted)} blacklisted key(s)")

            if len(available_keys) == 0:
                print(f"[RPC Pool] ⚠️  {chain}: No working Alchemy keys, using public RPC")
            else:
                for key_name in available_keys:
                    key_value = ALCHEMY_KEYS.get(key_name)
                    if key_value:
                        url = f'https://{chain_pattern}.g.alchemy.com/v2/{key_value}'
                        w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 60}))
                        rate_limiter = RateLimiter(calls_per_second=10)  # Conservative
                        self.providers.append((w3, rate_limiter, key_name))

                print(f"[RPC Pool] {chain}: {len(self.providers)} Alchemy connection(s)")

        # Fallback to public RPCs if no Alchemy keys or not an Alchemy chain
        if len(self.providers) == 0 and chain in PUBLIC_RPCS:
            for url in PUBLIC_RPCS[chain]:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 60}))
                rate_limiter = RateLimiter(calls_per_second=5)  # Public RPCs more conservative
                self.providers.append((w3, rate_limiter, None))  # None = public RPC
            print(f"[RPC Pool] {chain}: {len(self.providers)} public RPC connection(s)")

        if len(self.providers) == 0:
            raise ValueError(f"Chain {chain} has no available providers")

    def get_connection(self) -> tuple:
        """
        Get next Web3 connection in round-robin fashion.
        Applies rate limiting before returning.
        Thread-safe.

        Returns:
            Tuple of (Web3, key_name, rate_limiter) where key_name is None for public RPCs
        """
        with self.lock:
            w3, rate_limiter, key_name = self.providers[self.current_idx]
            self.current_idx = (self.current_idx + 1) % len(self.providers)

        # Apply rate limiting (outside lock to avoid blocking other threads)
        rate_limiter.wait()

        return w3, key_name, rate_limiter

    def test_connection(self) -> bool:
        """Test if at least one provider works"""
        for w3, _, key_name in self.providers:
            try:
                block = w3.eth.block_number
                print(f"[RPC Pool] {self.chain}: Connection OK (block {block})")
                return True
            except Exception:
                continue
        return False


# Global pool cache (one per chain)
_POOL_CACHE: Dict[str, AlchemyConnectionPool] = {}


def get_web3(chain: str, force_new: bool = False) -> Web3:
    """
    Get a Web3 connection for the given chain.

    Automatically rotates across available Alchemy accounts.
    Caches connection pools per chain.

    Args:
        chain: Chain name (e.g., 'ethereum', 'arbitrum')
        force_new: Force creation of new pool (ignore cache)

    Returns:
        Web3 instance

    Example:
        w3 = get_web3('ethereum')
        block = w3.eth.block_number
    """
    if chain not in _POOL_CACHE or force_new:
        _POOL_CACHE[chain] = AlchemyConnectionPool(chain)

    w3, _, _ = _POOL_CACHE[chain].get_connection()
    return w3


def get_web3_with_key_info(chain: str, force_new: bool = False) -> tuple:
    """
    Get a Web3 connection with key and rate limiter info for error handling.

    Returns:
        Tuple of (Web3, key_name, rate_limiter) where key_name is None for public RPCs
    """
    if chain not in _POOL_CACHE or force_new:
        _POOL_CACHE[chain] = AlchemyConnectionPool(chain)

    return _POOL_CACHE[chain].get_connection()


def report_rpc_error(chain: str, error_str: str):
    """
    Report an RPC error to trigger backoff for rate limits.
    Call this when you get 429 or 503 errors.
    """
    if chain in _POOL_CACHE:
        # Check if it's a rate limit error
        is_rate_limit = '429' in error_str or '503' in error_str or 'too many' in error_str.lower()
        # Report to all rate limiters for this chain (they share the endpoint)
        for _, rate_limiter, _ in _POOL_CACHE[chain].providers:
            rate_limiter.report_error(is_rate_limit=is_rate_limit)


def is_chain_backing_off(chain: str) -> tuple:
    """
    Check if a chain is currently in backoff mode due to rate limits.

    Returns:
        Tuple of (is_backing_off: bool, seconds_remaining: float)
    """
    if chain not in _POOL_CACHE:
        return False, 0

    # Check if any provider for this chain is backing off
    for _, rate_limiter, _ in _POOL_CACHE[chain].providers:
        if rate_limiter.is_backing_off():
            return True, rate_limiter.get_backoff_remaining()

    return False, 0


def test_all_chains():
    """Test connection to all chains"""
    print("\n" + "="*60)
    print("Testing RPC Connections")
    print("="*60 + "\n")

    all_chains = list(ALCHEMY_CHAINS.keys()) + ['ink', 'cronos', 'flare', 'meter']

    results = {}
    for chain in all_chains:
        try:
            pool = AlchemyConnectionPool(chain)
            success = pool.test_connection()
            results[chain] = success
        except Exception as e:
            print(f"[RPC Pool] {chain}: FAILED - {e}")
            results[chain] = False

    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    working = sum(1 for v in results.values() if v)
    total = len(results)

    for chain, success in sorted(results.items()):
        status = "✅" if success else "❌"
        print(f"{status} {chain}")

    print(f"\nWorking: {working}/{total} chains")

    return results


if __name__ == '__main__':
    # Test connections
    test_all_chains()
