"""
Chainlink Price Feed Adapter

Fetches historical token prices from Chainlink oracles via Alchemy.
Uses getRoundData() to get prices at specific blocks.

Chainlink feeds return prices with 8 decimals (e.g., 200000000000 = $2000.00)
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from web3 import Web3
import yaml

# Chainlink Aggregator V3 ABI (minimal)
AGGREGATOR_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"internalType": "uint80", "name": "roundId", "type": "uint80"},
            {"internalType": "int256", "name": "answer", "type": "int256"},
            {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
            {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
            {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Load feed config
CONFIG_PATH = Path('config/prices/chainlink_feeds.yaml')


def load_feed_config() -> Dict:
    """Load Chainlink feed configuration."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return {'feeds': {}, 'stablecoins': [], 'token_addresses': {}}


def get_chainlink_price(
    web3: Web3,
    feed_address: str,
    block: Optional[int] = None
) -> Optional[float]:
    """
    Get price from a Chainlink feed at a specific block.

    Args:
        web3: Web3 instance
        feed_address: Chainlink aggregator address
        block: Block number (None = latest)

    Returns:
        Price in USD as float, or None if failed
    """
    try:
        feed_address = Web3.to_checksum_address(feed_address)
        contract = web3.eth.contract(address=feed_address, abi=AGGREGATOR_ABI)

        call_kwargs = {'block_identifier': block} if block else {}

        # Get decimals
        decimals = contract.functions.decimals().call(**call_kwargs)

        # Get latest round data
        round_data = contract.functions.latestRoundData().call(**call_kwargs)
        answer = round_data[1]  # answer is at index 1

        # Convert to float with proper decimals
        price = answer / (10 ** decimals)

        return price

    except Exception as e:
        # Silently fail - will use fallback
        return None


def get_token_price_chainlink(
    web3: Web3,
    token_symbol: str,
    chain: str = 'ethereum',
    block: Optional[int] = None
) -> Optional[float]:
    """
    Get token price from Chainlink.

    Args:
        web3: Web3 instance connected to the chain
        token_symbol: Token symbol (e.g., 'WETH', 'USDC')
        chain: Chain name
        block: Block number (None = latest)

    Returns:
        Price in USD as float, or None if no feed available
    """
    config = load_feed_config()

    # Normalize symbol
    symbol = token_symbol.upper().strip()

    # Check if it's a stablecoin (assume $1.00)
    if symbol in config.get('stablecoins', []):
        return 1.0

    # Look up feed address
    feeds = config.get('feeds', {})

    if symbol not in feeds:
        return None

    feed_info = feeds[symbol]

    # Get feed address for this chain (fallback to ethereum)
    if isinstance(feed_info, dict):
        feed_address = feed_info.get(chain) or feed_info.get('ethereum')
    else:
        feed_address = feed_info

    if not feed_address:
        return None

    return get_chainlink_price(web3, feed_address, block)


def get_supported_tokens() -> List[str]:
    """Get list of tokens with Chainlink feeds."""
    config = load_feed_config()
    tokens = list(config.get('feeds', {}).keys())
    tokens.extend(config.get('stablecoins', []))
    return list(set(tokens))


def get_stablecoins() -> List[str]:
    """Get list of stablecoins (assumed $1.00)."""
    config = load_feed_config()
    return config.get('stablecoins', [])


if __name__ == '__main__':
    import os
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config.rpc_pool import get_web3

    print("Testing Chainlink Price Feeds")
    print("=" * 50)

    w3 = get_web3('ethereum')
    print(f"Connected to Ethereum, block {w3.eth.block_number:,}")

    test_tokens = ['ETH', 'WETH', 'WBTC', 'USDC', 'USDT', 'DAI', 'LINK', 'ARB']

    print("\nCurrent prices:")
    for token in test_tokens:
        price = get_token_price_chainlink(w3, token)
        if price:
            print(f"  {token}: ${price:,.2f}")
        else:
            print(f"  {token}: No feed available")

    # Test historical price
    print("\nHistorical price test (block 19000000 ~Jan 2024):")
    eth_price = get_token_price_chainlink(w3, 'ETH', block=19000000)
    if eth_price:
        print(f"  ETH at block 19000000: ${eth_price:,.2f}")
