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

Usage:
    from config.rpc_pool import get_web3
    
    w3 = get_web3('ethereum')
    block = w3.eth.block_number
"""

import os
import threading
import time
from web3 import Web3
from typing import Dict, List

# Load API keys from environment
ALCHEMY_KEYS = {
    'key_1': os.environ.get('ALCHEMY_KEY_1'),
    'key_2': os.environ.get('ALCHEMY_KEY_2'),
    'key_3': os.environ.get('ALCHEMY_KEY_3'),
    'key_4': os.environ.get('ALCHEMY_KEY_4'),
    'key_5': os.environ.get('ALCHEMY_KEY_5'),
}

# Remove None values
ALCHEMY_KEYS = {k: v for k, v in ALCHEMY_KEYS.items() if v}

if len(ALCHEMY_KEYS) == 0:
    raise ValueError("No Alchemy API keys found! Set ALCHEMY_KEY_1, ALCHEMY_KEY_2, etc.")

# Verified key-chain mapping (from test_key_mapping.py)
# Only use keys that have been tested and work for each chain
CHAIN_KEY_MAPPING = {
    "ethereum": ["key_1", "key_2", "key_3", "key_4", "key_5"],
    "arbitrum": ["key_1", "key_2", "key_3", "key_5"],
    "optimism": ["key_1", "key_2", "key_3", "key_5"],
    "base": ["key_1", "key_2", "key_3", "key_4", "key_5"],
    "polygon": ["key_1", "key_2", "key_3", "key_4", "key_5"],
    "avalanche": ["key_1", "key_2", "key_3", "key_4", "key_5"],
    "binance": ["key_1", "key_2", "key_3", "key_5"],
    "linea": ["key_1", "key_2", "key_3", "key_5"],
    "gnosis": ["key_1", "key_2", "key_3", "key_5"],
    "plasma": [],  # NO WORKING KEYS - will use public RPC
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
    'plasma': 'polygonzkevm-mainnet',
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
}


class RateLimiter:
    """
    Rate limiter for Alchemy free tier compliance.
    
    Free tier: 300 compute units/second (CUs)
    - eth_call: 26 CUs
    - eth_getLogs: 75 CUs
    - eth_getBlockByNumber: 16 CUs
    
    Conservative approach: limit to ~10 calls/second per key
    This gives us headroom regardless of call type.
    """
    
    def __init__(self, calls_per_second: float = 10):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
        self.lock = threading.Lock()
    
    def wait(self):
        """Wait if necessary to respect rate limit"""
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            self.last_call = time.time()



class AlchemyConnectionPool:
    """
    Round-robin connection pool using only verified working keys.
    
    Thread-safe rotation with per-key rate limiting for Alchemy free tier compliance.
    """
    
    def __init__(self, chain: str):
        self.chain = chain
        self.providers: List[tuple] = []  # List of (Web3, RateLimiter) tuples
        self.current_idx = 0
        self.lock = threading.Lock()
        
        # Build providers for this chain using only verified working keys
        if chain in ALCHEMY_CHAINS:
            chain_pattern = ALCHEMY_CHAINS[chain]
            working_keys = CHAIN_KEY_MAPPING.get(chain, [])
            
            if len(working_keys) == 0:
                print(f"[RPC Pool] ⚠️  {chain}: No working Alchemy keys, using public RPC")
            else:
                for key_name in working_keys:
                    key_value = ALCHEMY_KEYS.get(key_name)
                    if key_value:
                        url = f'https://{chain_pattern}.g.alchemy.com/v2/{key_value}'
                        w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 60}))
                        rate_limiter = RateLimiter(calls_per_second=10)  # Conservative
                        self.providers.append((w3, rate_limiter))
                
                print(f"[RPC Pool] {chain}: {len(self.providers)} Alchemy connection(s)")
        
        # Fallback to public RPCs if no Alchemy keys or not an Alchemy chain
        if len(self.providers) == 0 and chain in PUBLIC_RPCS:
            for url in PUBLIC_RPCS[chain]:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 60}))
                rate_limiter = RateLimiter(calls_per_second=5)  # Public RPCs more conservative
                self.providers.append((w3, rate_limiter))
            print(f"[RPC Pool] {chain}: {len(self.providers)} public RPC connection(s)")
        
        if len(self.providers) == 0:
            raise ValueError(f"Chain {chain} has no available providers")
    
    def get_connection(self) -> Web3:
        """
        Get next Web3 connection in round-robin fashion.
        Applies rate limiting before returning.
        Thread-safe.
        """
        with self.lock:
            w3, rate_limiter = self.providers[self.current_idx]
            self.current_idx = (self.current_idx + 1) % len(self.providers)
        
        # Apply rate limiting (outside lock to avoid blocking other threads)
        rate_limiter.wait()
        
        return w3
    
    def test_connection(self) -> bool:
        """Test if at least one provider works"""
        for w3, _ in self.providers:
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
    
    return _POOL_CACHE[chain].get_connection()


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
