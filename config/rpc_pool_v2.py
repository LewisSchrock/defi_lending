"""
Multi-Provider RPC Connection Pool v2

Intelligently routes requests across multiple RPC providers to maximize throughput
and minimize rate limit hits.

Provider Summary:
-----------------
| Provider   | Monthly Limit      | Burst Limit   | eth_getLogs Cost | Priority |
|------------|-------------------|---------------|------------------|----------|
| dRPC       | Pay-as-you-go     | ~100 req/sec  | Low              | Default  |
| Alchemy    | 30M CU/acct       | 300 CU/sec    | 60 CU            | Fallback |
| BlockPi    | 50M RU/31 days    | 400 RU/sec    | 75 RU            | Fallback |
| NodeReal   | 100M CU/month     | 150 CU/sec    | 75 CU            | Fallback |
| Ankr       | 200M credits/mo   | ~30 req/sec   | ~100 credits     | Secondary|
| Infura     | 3M credits/day    | 500 cred/sec  | HIGH             | Last     |
| Public     | No limit          | ~5-10 req/sec | N/A              | Last     |

Strategy:
- Default: dRPC (fastest, supports all chains with a single key)
- Fallback: Alchemy, BlockPi, NodeReal for eth_getLogs
- Secondary: Ankr for overflow
- Last resort: Infura (daily cap), Public RPCs
- Per-chain optimization based on provider support

Usage:
    from config.rpc_pool_v2 import get_web3, get_provider_stats

    w3 = get_web3('ethereum')
    block = w3.eth.block_number
"""

import os
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from web3 import Web3

# Auto-load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass


# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

@dataclass
class ProviderConfig:
    """Configuration for an RPC provider."""
    name: str
    monthly_limit: int  # Total units per month
    burst_limit: float  # Units per second
    get_logs_cost: int  # Cost per eth_getLogs call
    call_cost: int  # Cost per eth_call
    block_cost: int  # Cost per eth_getBlockByNumber
    priority: int  # Lower = higher priority (used first)
    url_template: str  # URL template with {key} and {chain} placeholders
    chain_map: Dict[str, str]  # Maps our chain names to provider's chain names
    daily_limit: Optional[int] = None  # If provider has daily limits


# Provider definitions
PROVIDERS = {
    'drpc': ProviderConfig(
        name='drpc',
        monthly_limit=999_999_999,  # Pay-as-you-go, effectively unlimited
        burst_limit=100,  # ~100 req/sec
        get_logs_cost=1,  # Low cost, no CU-based billing
        call_cost=1,
        block_cost=1,
        priority=0,  # Highest priority — default provider
        url_template='https://lb.drpc.org/ogrpc?network={chain}&dkey={key}',
        chain_map={
            'ethereum': 'ethereum',
            'arbitrum': 'arbitrum',
            'optimism': 'optimism',
            'base': 'base',
            'polygon': 'polygon',
            'avalanche': 'avalanche',
            'binance': 'bsc',
            'linea': 'linea',
            'gnosis': 'gnosis',
            'scroll': 'scroll',
            'sonic': 'sonic',
            'ink': 'ink',
            'plasma': 'plasma',
            'meter': 'meter',
            'flare': 'flare',
        }
    ),
    'alchemy': ProviderConfig(
        name='alchemy',
        monthly_limit=30_000_000,
        burst_limit=300,
        get_logs_cost=60,
        call_cost=26,
        block_cost=20,
        priority=1,
        url_template='https://{chain}.g.alchemy.com/v2/{key}',
        chain_map={
            'ethereum': 'eth-mainnet',
            'arbitrum': 'arb-mainnet',
            'optimism': 'opt-mainnet',
            'base': 'base-mainnet',
            'polygon': 'polygon-mainnet',
            'avalanche': 'avax-mainnet',
            'binance': 'bnb-mainnet',
            'linea': 'linea-mainnet',
            'gnosis': 'gnosis-mainnet',
            'scroll': 'scroll-mainnet',
            'sonic': 'sonic-mainnet',
            'ink': 'ink-mainnet',
            'plasma': 'plasma-mainnet',
        }
    ),
    'blockpi': ProviderConfig(
        name='blockpi',
        monthly_limit=50_000_000,  # 50M RU per 31 days
        burst_limit=400,  # 400 RU/sec (binding constraint)
        get_logs_cost=75,
        call_cost=20,
        block_cost=20,
        priority=1,  # Same priority as Alchemy - best for logs
        url_template='https://{chain}.blockpi.network/v1/rpc/{key}',
        chain_map={
            'ethereum': 'ethereum',
            'optimism': 'optimism',
            'polygon': 'polygon',
            'arbitrum': 'arbitrum',
            'binance': 'bsc',
            'gnosis': 'gnosis',
            'avalanche': 'avalanche',
            'base': 'base',
            'linea': 'linea',
            'meter': 'meter',
            'sonic': 'sonic',
            'ink': 'ink',
        }
    ),
    'nodereal': ProviderConfig(
        name='nodereal',
        monthly_limit=100_000_000,
        burst_limit=150,
        get_logs_cost=75,
        call_cost=20,
        block_cost=20,
        priority=2,
        url_template='special',  # Has different URL patterns per chain
        chain_map={
            'binance': 'bsc-mainnet',
            'ethereum': 'eth-mainnet',
            'optimism': 'opt-mainnet',
            'avalanche': 'avalanche-c',
            'arbitrum': 'arbitrum-nitro',
            'base': 'base',
        }
    ),
    'ankr': ProviderConfig(
        name='ankr',
        monthly_limit=200_000_000,
        burst_limit=30,  # ~30 req/sec
        get_logs_cost=100,  # Estimated
        call_cost=30,
        block_cost=30,
        priority=3,
        url_template='https://rpc.ankr.com/{chain}/{key}',
        chain_map={
            'ethereum': 'eth',
            'polygon': 'polygon',
            'binance': 'bsc',
            'base': 'base',
            'arbitrum': 'arbitrum',
            'avalanche': 'avalanche',
            'gnosis': 'gnosis',
            'optimism': 'optimism',
            'flare': 'flare',
        }
    ),
    'infura': ProviderConfig(
        name='infura',
        monthly_limit=90_000_000,  # 3M/day * 30 days
        daily_limit=3_000_000,
        burst_limit=500,
        get_logs_cost=200,  # HIGH - avoid for logs
        call_cost=50,
        block_cost=50,
        priority=4,  # Use as fallback
        url_template='https://{chain}.infura.io/v3/{key}',
        chain_map={
            'ethereum': 'mainnet',
            'linea': 'linea-mainnet',
            'polygon': 'polygon-mainnet',
            'base': 'base-mainnet',
            'optimism': 'optimism-mainnet',
            'arbitrum': 'arbitrum-mainnet',
            'binance': 'bsc-mainnet',
            'scroll': 'scroll-mainnet',
            'avalanche': 'avalanche-mainnet',
        }
    ),
}

# Public RPC fallbacks (no auth, low rate limits)
PUBLIC_RPCS = {
    'ethereum': ['https://cloudflare-eth.com', 'https://eth.llamarpc.com'],
    'arbitrum': ['https://arb1.arbitrum.io/rpc', 'https://arbitrum.llamarpc.com'],
    'optimism': ['https://mainnet.optimism.io', 'https://optimism.llamarpc.com'],
    'base': ['https://mainnet.base.org', 'https://base.llamarpc.com'],
    'polygon': ['https://polygon-rpc.com', 'https://polygon.llamarpc.com'],
    'avalanche': ['https://api.avax.network/ext/bc/C/rpc'],
    'binance': ['https://bsc-dataseed.binance.org', 'https://bsc.publicnode.com'],
    'linea': ['https://rpc.linea.build'],
    'gnosis': ['https://rpc.gnosischain.com'],
    'scroll': ['https://rpc.scroll.io'],
    'sonic': ['https://rpc.soniclabs.com'],
    'meter': ['https://rpc.meter.io'],
    'ink': ['https://rpc-qnd.inkonchain.com'],
    'cronos': ['https://evm.cronos.org'],
    'flare': ['https://flare-api.flare.network/ext/C/rpc'],
}

# POA chains requiring middleware
POA_CHAINS = {'binance', 'polygon', 'gnosis', 'avalanche', 'optimism',
              'linea', 'scroll', 'sonic', 'cronos', 'meter', 'flare'}

# Alchemy keys that DON'T support certain chains (need to enable in dashboard)
# Format: {chain: [list of key indices (1-based) that are NOT enabled]}
ALCHEMY_CHAIN_EXCLUSIONS = {
    'sonic': [1, 2, 3, 4],  # Keys 5-13 have Sonic enabled
    'ink': [1, 2, 3, 4, 5, 6, 7, 9],  # Keys 8, 10-13 have Ink enabled
    'scroll': [1, 2, 3, 4, 5, 6, 8],  # Keys 7, 9-13 have Scroll enabled
    'plasma': [4, 7],  # Keys 1-3, 5-6, 8-13 have Plasma enabled
}


# =============================================================================
# LOAD API KEYS
# =============================================================================

def load_api_keys() -> Dict[str, any]:
    """Load all API keys from environment."""
    keys = defaultdict(list)

    # dRPC generic keys (work for any chain)
    for i in range(1, 10):
        key = os.environ.get(f'DRPC_KEY_{i}')
        if key:
            keys['drpc'].append(key)

    # Also try per-chain dRPC keys and extract the raw key
    # Format: DRPC_KEY_ETHEREUM='https://lb.drpc.live/ethereum/KEY'
    if not keys['drpc']:
        for env_name in ['DRPC_KEY_ETHEREUM', 'DRPC_KEY_ARBITRUM', 'DRPC_KEY_BASE']:
            url = os.environ.get(env_name, '')
            if url and 'drpc.live' in url:
                # Extract key from URL: https://lb.drpc.live/{chain}/{key}
                raw_key = url.rstrip('/').rsplit('/', 1)[-1]
                if raw_key and raw_key != 'YOUR_KEY':
                    keys['drpc'].append(raw_key)
                    break  # One key is enough since it works for all chains

    # Alchemy keys (multiple accounts)
    for i in range(1, 20):
        key = os.environ.get(f'ALCHEMY_KEY_{i}')
        if key:
            keys['alchemy'].append(key)

    # Single-key providers
    for provider in ['infura', 'nodereal', 'ankr']:
        key = os.environ.get(f'{provider.upper()}_API_KEY')
        if key:
            keys[provider].append(key)

    # BlockPi has per-chain keys
    blockpi_keys = {}
    blockpi_chain_map = {
        'ethereum': 'ETHEREUM',
        'optimism': 'OPTIMISM',
        'polygon': 'POLYGON',
        'arbitrum': 'ARBITRUM',
        'binance': 'BSC',
        'gnosis': 'GNOSIS',
        'avalanche': 'AVALANCHE',
        'sonic': 'SONIC',
        'ink': 'INK',
        'linea': 'LINEA',
        'meter': 'METER',
        'base': 'BASE',
    }
    for chain, env_suffix in blockpi_chain_map.items():
        key = os.environ.get(f'BLOCKPI_KEY_{env_suffix}')
        if key:
            blockpi_keys[chain] = key
    if blockpi_keys:
        keys['blockpi'] = blockpi_keys

    return dict(keys)


API_KEYS = load_api_keys()


# =============================================================================
# USAGE TRACKING
# =============================================================================

USAGE_FILE = Path('data/.rpc_usage_v2.json')
_usage_lock = threading.Lock()


def load_usage() -> Dict:
    """Load usage tracking data."""
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {'providers': {}, 'month': time.strftime('%Y-%m')}


def save_usage(usage: Dict):
    """Save usage tracking data."""
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, 'w') as f:
        json.dump(usage, f, indent=2)


def record_call(provider: str, method: str, cost: int):
    """Record an API call for usage tracking."""
    with _usage_lock:
        usage = load_usage()

        # Reset if new month
        current_month = time.strftime('%Y-%m')
        if usage.get('month') != current_month:
            usage = {'providers': {}, 'month': current_month}

        if provider not in usage['providers']:
            usage['providers'][provider] = {'total_cu': 0, 'calls': 0, 'by_method': {}}

        usage['providers'][provider]['total_cu'] += cost
        usage['providers'][provider]['calls'] += 1
        usage['providers'][provider]['by_method'][method] = \
            usage['providers'][provider]['by_method'].get(method, 0) + 1

        # Save periodically (every 100 calls)
        if sum(p['calls'] for p in usage['providers'].values()) % 100 == 0:
            save_usage(usage)


def get_provider_usage(provider: str) -> Dict:
    """Get current usage for a provider."""
    usage = load_usage()
    return usage.get('providers', {}).get(provider, {'total_cu': 0, 'calls': 0})


# =============================================================================
# RATE LIMITING
# =============================================================================

@dataclass
class RateLimiter:
    """Per-provider rate limiter with backoff."""
    provider: str
    calls_per_second: float
    min_interval: float = field(init=False)
    last_call: float = field(default=0)
    backoff_until: float = field(default=0)
    consecutive_errors: int = field(default=0)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        self.min_interval = 1.0 / self.calls_per_second

    def wait(self):
        """Wait if necessary to respect rate limit."""
        with self.lock:
            now = time.time()

            # Check backoff
            if now < self.backoff_until:
                sleep_time = self.backoff_until - now
                time.sleep(sleep_time)
                now = time.time()

            # Normal rate limiting
            elapsed = now - self.last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)

            self.last_call = time.time()

    def report_error(self, is_rate_limit: bool = False):
        """Report an error, triggering backoff for rate limits."""
        with self.lock:
            if is_rate_limit:
                self.consecutive_errors += 1
                backoff = min(5 * (2 ** (self.consecutive_errors - 1)), 120)
                self.backoff_until = time.time() + backoff
                print(f"[{self.provider}] Rate limit hit, backing off {backoff}s")

    def report_success(self):
        """Report success, resetting backoff."""
        with self.lock:
            self.consecutive_errors = 0


# =============================================================================
# PROVIDER POOL
# =============================================================================

class ProviderEndpoint:
    """A single provider endpoint (URL + rate limiter)."""

    def __init__(self, provider: str, url: str, config: ProviderConfig, key_name: str = None):
        self.provider = provider
        self.url = url
        self.config = config
        self.key_name = key_name
        self.web3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 60}))

        # Calculate calls per second based on burst limit and typical cost
        avg_cost = (config.get_logs_cost + config.call_cost) / 2
        if avg_cost > 0 and config.burst_limit > 0:
            calls_per_sec = config.burst_limit / avg_cost
        else:
            calls_per_sec = 5  # Default for public RPCs
        self.rate_limiter = RateLimiter(provider, max(calls_per_sec, 1))

        # Inject POA middleware if needed
        self._inject_poa_middleware()

    def _inject_poa_middleware(self):
        """Inject POA middleware for chains that need it."""
        try:
            from web3.middleware import ExtraDataToPOAMiddleware as poa_middleware
        except ImportError:
            try:
                from web3.middleware import geth_poa_middleware as poa_middleware
            except ImportError:
                return

        try:
            if hasattr(self.web3, 'middleware_onion'):
                self.web3.middleware_onion.inject(poa_middleware, layer=0)
        except:
            pass


class ChainPool:
    """Pool of provider endpoints for a specific chain."""

    def __init__(self, chain: str):
        self.chain = chain
        self.endpoints: List[ProviderEndpoint] = []
        self.current_idx = 0
        self.lock = threading.Lock()

        self._build_endpoints()

    def _build_endpoints(self):
        """Build list of endpoints sorted by priority."""
        endpoints = []

        # Add provider endpoints
        for provider_name, config in sorted(PROVIDERS.items(), key=lambda x: x[1].priority):
            if self.chain not in config.chain_map:
                continue

            chain_name = config.chain_map[self.chain]

            # Handle BlockPi's per-chain key model
            if provider_name == 'blockpi':
                blockpi_keys = API_KEYS.get('blockpi', {})
                if isinstance(blockpi_keys, dict) and self.chain in blockpi_keys:
                    key = blockpi_keys[self.chain]
                    # BlockPi URL format: https://{chain}.blockpi.network/v1/rpc/{key}
                    blockpi_chain = config.chain_map[self.chain]
                    url = f'https://{blockpi_chain}.blockpi.network/v1/rpc/{key}'
                    endpoints.append(ProviderEndpoint(
                        provider=provider_name,
                        url=url,
                        config=config,
                        key_name=f"blockpi_{self.chain}"
                    ))
                continue

            # Standard providers with list of keys
            keys = API_KEYS.get(provider_name, [])
            if not keys or not isinstance(keys, list):
                continue

            for idx, key in enumerate(keys):
                key_num = idx + 1  # 1-based key number

                # Check if this Alchemy key is excluded for this chain
                if provider_name == 'alchemy':
                    excluded_keys = ALCHEMY_CHAIN_EXCLUSIONS.get(self.chain, [])
                    if key_num in excluded_keys:
                        continue  # Skip this key for this chain

                if config.url_template == 'special':
                    url = self._get_nodereal_url(chain_name, key)
                else:
                    url = config.url_template.format(chain=chain_name, key=key)

                if url:
                    endpoints.append(ProviderEndpoint(
                        provider=provider_name,
                        url=url,
                        config=config,
                        key_name=f"{provider_name}_{key_num}"
                    ))

        # Add public RPCs as fallback
        for url in PUBLIC_RPCS.get(self.chain, []):
            endpoints.append(ProviderEndpoint(
                provider='public',
                url=url,
                config=ProviderConfig(
                    name='public',
                    monthly_limit=999999999,
                    burst_limit=5,
                    get_logs_cost=0,
                    call_cost=0,
                    block_cost=0,
                    priority=99,
                    url_template='',
                    chain_map={}
                ),
                key_name=None
            ))

        self.endpoints = endpoints

        if endpoints:
            providers = set(e.provider for e in endpoints)
            print(f"[RPC Pool] {self.chain}: {len(endpoints)} endpoints ({', '.join(sorted(providers))})")
        else:
            print(f"[RPC Pool] {self.chain}: No endpoints available!")

    def _get_nodereal_url(self, chain_name: str, key: str) -> Optional[str]:
        """Get NodeReal URL (they have different patterns per chain)."""
        if chain_name == 'bsc-mainnet':
            return f'https://bsc-mainnet.nodereal.io/v1/{key}'
        elif chain_name == 'eth-mainnet':
            return f'https://eth-mainnet.nodereal.io/v1/{key}'
        elif chain_name == 'opt-mainnet':
            return f'https://opt-mainnet.nodereal.io/v1/{key}'
        elif chain_name == 'avalanche-c':
            return f'https://open-platform.nodereal.io/{key}/avalanche-c/ext/bc/C/rpc'
        elif chain_name == 'arbitrum-nitro':
            return f'https://open-platform.nodereal.io/{key}/arbitrum-nitro/'
        elif chain_name == 'base':
            return f'https://open-platform.nodereal.io/{key}/base'
        return None

    def get_connection(self) -> Tuple[Web3, str, ProviderEndpoint]:
        """Get next connection in round-robin fashion."""
        with self.lock:
            if not self.endpoints:
                raise ValueError(f"No endpoints available for {self.chain}")

            endpoint = self.endpoints[self.current_idx]
            self.current_idx = (self.current_idx + 1) % len(self.endpoints)

        # Apply rate limiting
        endpoint.rate_limiter.wait()

        return endpoint.web3, endpoint.provider, endpoint

    def test_connections(self) -> Dict[str, bool]:
        """Test all connections and return status."""
        results = {}
        for endpoint in self.endpoints:
            try:
                block = endpoint.web3.eth.block_number
                results[f"{endpoint.provider}:{endpoint.key_name or 'public'}"] = True
            except Exception as e:
                results[f"{endpoint.provider}:{endpoint.key_name or 'public'}"] = False
        return results


# =============================================================================
# GLOBAL POOL MANAGEMENT
# =============================================================================

_POOLS: Dict[str, ChainPool] = {}
_pool_lock = threading.Lock()


def get_pool(chain: str) -> ChainPool:
    """Get or create pool for a chain."""
    with _pool_lock:
        if chain not in _POOLS:
            _POOLS[chain] = ChainPool(chain)
        return _POOLS[chain]


def get_web3(chain: str) -> Web3:
    """Get a Web3 connection for the given chain."""
    pool = get_pool(chain)
    w3, provider, endpoint = pool.get_connection()
    return w3


def get_web3_with_info(chain: str) -> Tuple[Web3, str, ProviderEndpoint]:
    """Get Web3 connection with provider info for error handling."""
    pool = get_pool(chain)
    return pool.get_connection()


def report_rpc_error(chain: str, error_str: str):
    """Report an RPC error to trigger backoff."""
    is_rate_limit = any(p in error_str.lower() for p in ['429', '503', 'rate limit', 'too many'])

    pool = get_pool(chain)
    for endpoint in pool.endpoints:
        if is_rate_limit:
            endpoint.rate_limiter.report_error(is_rate_limit=True)


def is_chain_backing_off(chain: str) -> Tuple[bool, float]:
    """Check if any provider for this chain is backing off."""
    pool = get_pool(chain)
    for endpoint in pool.endpoints:
        if endpoint.rate_limiter.backoff_until > time.time():
            return True, endpoint.rate_limiter.backoff_until - time.time()
    return False, 0


def blacklist_key(chain: str, key_name: str, reason: str = ""):
    """Blacklist a key for a chain (triggers long backoff)."""
    pool = get_pool(chain)
    for endpoint in pool.endpoints:
        if endpoint.key_name == key_name:
            # Set a long backoff (1 hour) for this endpoint
            endpoint.rate_limiter.backoff_until = time.time() + 3600
            endpoint.rate_limiter.consecutive_errors = 10
            print(f"[RPC Pool] Blacklisted {key_name} on {chain}: {reason[:50]}")
            break


# =============================================================================
# STATUS & TESTING
# =============================================================================

def get_provider_stats() -> Dict:
    """Get current provider statistics."""
    stats = {
        'keys_configured': {},
        'usage': {},
        'monthly_capacity': 0,
    }

    for provider, keys in API_KEYS.items():
        if isinstance(keys, dict):
            # BlockPi: per-chain keys, but shared quota
            stats['keys_configured'][provider] = f"{len(keys)} chains"
            if provider in PROVIDERS:
                config = PROVIDERS[provider]
                # BlockPi has one shared quota across all chains
                stats['monthly_capacity'] += config.monthly_limit
        elif isinstance(keys, list):
            stats['keys_configured'][provider] = len(keys)
            if provider in PROVIDERS:
                config = PROVIDERS[provider]
                monthly = config.monthly_limit * len(keys)
                stats['monthly_capacity'] += monthly

    usage = load_usage()
    stats['usage'] = usage.get('providers', {})
    stats['month'] = usage.get('month', 'unknown')

    return stats


def test_all_chains() -> Dict[str, Dict]:
    """Test connections for all supported chains."""
    print("\n" + "=" * 70)
    print("TESTING ALL RPC CONNECTIONS")
    print("=" * 70)

    all_chains = set()
    for config in PROVIDERS.values():
        all_chains.update(config.chain_map.keys())
    all_chains.update(PUBLIC_RPCS.keys())

    results = {}
    for chain in sorted(all_chains):
        print(f"\n{chain}:")
        try:
            pool = get_pool(chain)
            chain_results = pool.test_connections()
            results[chain] = chain_results

            for endpoint, success in chain_results.items():
                status = "OK" if success else "FAILED"
                print(f"  [{status:6}] {endpoint}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results[chain] = {'error': str(e)}

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    working_chains = sum(1 for r in results.values() if any(v for v in r.values() if v is True))
    print(f"Working chains: {working_chains}/{len(results)}")

    stats = get_provider_stats()
    print(f"\nConfigured keys:")
    for provider, count in stats['keys_configured'].items():
        print(f"  {provider}: {count}")

    print(f"\nTotal monthly capacity: {stats['monthly_capacity']:,} CU")

    return results


if __name__ == '__main__':
    test_all_chains()
