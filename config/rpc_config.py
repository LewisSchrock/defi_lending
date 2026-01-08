"""
RPC URL resolution - auto-generates Alchemy URLs from API key.
"""

import os
from typing import Optional

# Alchemy URL patterns
ALCHEMY_PATTERNS = {
    'ethereum': 'https://eth-mainnet.g.alchemy.com/v2/{key}',
    'polygon': 'https://polygon-mainnet.g.alchemy.com/v2/{key}',
    'plasma': 'https://plasma-mainnet.g.alchemy.com/v2/{key}',
    'arbitrum': 'https://arb-mainnet.g.alchemy.com/v2/{key}',
    'optimism': 'https://opt-mainnet.g.alchemy.com/v2/{key}',
    'base': 'https://base-mainnet.g.alchemy.com/v2/{key}',
    'binance': 'https://bnb-mainnet.g.alchemy.com/v2/{key}',
    'linea': 'https://linea-mainnet.g.alchemy.com/v2/{key}',
    'xdai': 'https://gnosis-mainnet.g.alchemy.com/v2/{key}',
    'avalanche': 'https://avax-mainnet.g.alchemy.com/v2/{key}',
    'solana': 'https://solana-mainnet.g.alchemy.com/v2/{key}',
}

# Public RPCs for non-Alchemy chains
PUBLIC_RPCS = {
    'cronos': 'https://evm.cronos.org',
    'flare': 'https://flare-api.flare.network/ext/C/rpc',
    'ink': 'https://rpc-qnd.inkonchain.com',
    'core': 'https://rpc.test2.btcs.network',  # CORE testnet
    'meter': 'https://rpc.meter.io',
    'scroll': 'https://rpc.scroll.io',
    'sonic': 'https://rpc.soniclabs.com',
}


def get_rpc_url(chain: str, api_key: Optional[str] = None) -> str:
    """
    Get RPC URL for a chain.
    
    Args:
        chain: Chain name (e.g., 'ethereum', 'arbitrum')
        api_key: Alchemy API key (uses ALCHEMY_API_KEY env var if not provided)
        
    Returns:
        Complete RPC URL
    """
    chain = chain.lower()
    
    # Try Alchemy first
    if chain in ALCHEMY_PATTERNS:
        key = api_key or os.getenv('ALCHEMY_API_KEY')
        if not key:
            raise ValueError(
                f"Alchemy API key required for {chain}. "
                "Set ALCHEMY_API_KEY env var or pass api_key parameter."
            )
        return ALCHEMY_PATTERNS[chain].format(key=key)
    
    # Fall back to public RPC
    if chain in PUBLIC_RPCS:
        return PUBLIC_RPCS[chain]
    
    raise ValueError(f"Unknown chain: {chain}")
