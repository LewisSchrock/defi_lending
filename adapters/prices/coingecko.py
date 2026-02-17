"""
CoinGecko Price Adapter

Fetches historical token prices from CoinGecko API.
Used as fallback when DefiLlama doesn't have the token.

Demo API key: ~30 calls/minute, 1 year historical data
Set COINGECKO_API_KEY environment variable or in .env file
"""

import os
import time
import requests
from pathlib import Path

# Auto-load .env file for API keys
try:
    from dotenv import load_dotenv
    # Look for .env in project root (parent of adapters/prices/)
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on shell exports
from typing import Dict, Optional, List
from datetime import datetime, date

# Try to load API key from environment or .env file
def _load_api_key() -> Optional[str]:
    """Load CoinGecko API key from environment or .env file."""
    key = os.environ.get('COINGECKO_API_KEY')
    if key:
        return key

    # Try .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                # Handle both "export KEY='value'" and "KEY='value'" formats
                if line.startswith('export '):
                    line = line[7:]  # Remove 'export ' prefix
                if line.startswith('COINGECKO_API_KEY='):
                    return line.split('=', 1)[1].strip().strip('"\'')
    return None

# CoinGecko API configuration
API_KEY = _load_api_key()
BASE_URL = "https://api.coingecko.com/api/v3" if not API_KEY else "https://api.coingecko.com/api/v3"

# Rate limiting: 30 calls/minute for demo tier = 2 seconds between calls
_last_call_time = 0
MIN_CALL_INTERVAL = 2.0  # 30 calls/minute max

# Token symbol to CoinGecko ID mapping
# CoinGecko uses its own IDs, not ticker symbols
COINGECKO_IDS = {
    # Major tokens
    'ETH': 'ethereum',
    'WETH': 'weth',
    'BTC': 'bitcoin',
    'WBTC': 'wrapped-bitcoin',
    'USDC': 'usd-coin',
    'USDT': 'tether',
    'DAI': 'dai',
    'FRAX': 'frax',
    'LUSD': 'liquity-usd',

    # LSTs (Liquid Staking Tokens) - treated as separate assets
    'stETH': 'staked-ether',
    'wstETH': 'wrapped-steth',
    'rETH': 'rocket-pool-eth',
    'cbETH': 'coinbase-wrapped-staked-eth',
    'weETH': 'wrapped-eeth',
    'ezETH': 'renzo-restaked-eth',
    'rsETH': 'kelp-dao-restaked-eth',
    'sfrxETH': 'staked-frax-ether',
    'osETH': 'stakewise-staked-eth',
    'ETHx': 'stader-ethx',

    # DeFi tokens
    'LINK': 'chainlink',
    'UNI': 'uniswap',
    'AAVE': 'aave',
    'COMP': 'compound-governance-token',
    'MKR': 'maker',
    'CRV': 'curve-dao-token',
    'SNX': 'havven',
    'GNO': 'gnosis',
    'GMX': 'gmx',
    'PENDLE': 'pendle',
    'LDO': 'lido-dao',
    'BAL': 'balancer',
    'ENS': 'ethereum-name-service',
    '1INCH': '1inch',
    'RPL': 'rocket-pool',
    'STG': 'stargate-finance',
    'KNC': 'kyber-network-crystal',
    'FXS': 'frax-share',

    # L2 tokens
    'ARB': 'arbitrum',
    'OP': 'optimism',
    'MATIC': 'matic-network',
    'METIS': 'metis-token',

    # Avalanche tokens
    'AVAX': 'avalanche-2',
    'WAVAX': 'wrapped-avax',
    'sAVAX': 'benqi-liquid-staked-avax',
    'QI': 'benqi',
    'BTC.b': 'bitcoin-avalanche-bridged-btc-b',
    'BTCb': 'bitcoin-avalanche-bridged-btc-b',

    # Stablecoins with prices (yield-bearing)
    'sDAI': 'savings-dai',
    'crvUSD': 'crvusd',
    'GHO': 'gho',

    # Ethena
    'USDe': 'ethena-usde',
    'sUSDe': 'ethena-staked-usde',

    # Other tokens
    'tBTC': 'tbtc',
    'cbBTC': 'coinbase-wrapped-btc',
    'MAI': 'mimatic',
    'WELL': 'moonwell-artemis',
    'GEAR': 'gearbox',
    'AERO': 'aerodrome-finance',
    'PYUSD': 'paypal-usd',
    'WLD': 'worldcoin-wld',

    # Additional LSTs and restaked tokens
    'mETH': 'mantle-staked-ether',
    'pufETH': 'puffer-restaked-eth',
    'rswETH': 'restaked-swell-eth',
    'stMATIC': 'lido-staked-matic',
    'tETH': 'treehouse-eth',
    'wOETH': 'wrapped-oeth',
    'wrsETH': 'wrapped-rseth',
    'wsuperOETHb': 'wrapped-super-oethb',

    # Additional BTC variants
    'FBTC': 'ignition-fbtc',
    'LBTC': 'lombard-staked-btc',
    'eBTC': 'ebtc',

    # DeFi and index tokens
    'DPI': 'defipulse-index',
    'GHST': 'aavegotchi',
    'SKY': 'sky',
    'SUSHI': 'sushi',

    # Wrapped native tokens
    'WMATIC': 'wmatic',
    'WPOL': 'wmatic',
    'QUICK': 'quick',
    'WXDAI': 'wrapped-xdai',
    'MaticX': 'stader-maticx',

    # Real world assets
    'EURe': 'monerium-eur-money',
    'XAUt': 'tether-gold',
}

# Stablecoins (assume $1.00) - NOT looked up via API
STABLECOINS = {
    'USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'sUSD', 'USDbC',
    'USDC.e', 'DAI.e', 'MAI', 'USDS', 'USD0',
    'PYUSD', 'GUSD', 'TUSD', 'BUSD', 'USDP',
    # Additional stablecoins found in 2025 data
    'USDG', 'mUSD', 'syrupUSDT', 'WXDAI', 'GHO',
}


def _rate_limit():
    """Apply rate limiting between API calls."""
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    _last_call_time = time.time()


def get_coingecko_id(symbol: str) -> Optional[str]:
    """Get CoinGecko ID for a token symbol (case-insensitive)."""
    # Try exact match first (for mixed case like wstETH)
    if symbol in COINGECKO_IDS:
        return COINGECKO_IDS[symbol]
    # Then try uppercase
    if symbol.upper() in COINGECKO_IDS:
        return COINGECKO_IDS[symbol.upper()]
    # Finally try case-insensitive search
    symbol_upper = symbol.upper()
    for key, value in COINGECKO_IDS.items():
        if key.upper() == symbol_upper:
            return value
    return None


def get_historical_price(
    coingecko_id: str,
    date_str: str,
    verbose: bool = False
) -> Optional[float]:
    """
    Get historical price from CoinGecko.

    Args:
        coingecko_id: CoinGecko token ID
        date_str: Date in YYYY-MM-DD format
        verbose: Print debug info

    Returns:
        Price in USD as float, or None if failed
    """
    _rate_limit()

    try:
        # Convert date format for CoinGecko API (DD-MM-YYYY)
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        cg_date = dt.strftime('%d-%m-%Y')

        url = f"{BASE_URL}/coins/{coingecko_id}/history"
        params = {
            'date': cg_date,
            'localization': 'false'
        }

        # Add API key header if available
        headers = {}
        if API_KEY:
            headers['x-cg-demo-api-key'] = API_KEY

        if verbose:
            print(f"  [CoinGecko] Fetching {coingecko_id} for {date_str}...")

        response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code == 429:
            print(f"[CoinGecko] Rate limited, waiting 60s...")
            time.sleep(60)
            return get_historical_price(coingecko_id, date_str, verbose)

        if response.status_code == 401:
            print(f"[CoinGecko] API key invalid or date too old (>1 year)")
            return None

        if response.status_code != 200:
            if verbose:
                print(f"  [CoinGecko] HTTP {response.status_code} for {coingecko_id}")
            return None

        data = response.json()
        market_data = data.get('market_data', {})
        current_price = market_data.get('current_price', {})

        price = current_price.get('usd')
        if verbose and price:
            print(f"  [CoinGecko] {coingecko_id}: ${price:,.4f}")

        return price

    except Exception as e:
        print(f"[CoinGecko] Error fetching {coingecko_id} for {date_str}: {e}")
        return None


def get_token_price_coingecko(
    token_symbol: str,
    date_str: str
) -> Optional[float]:
    """
    Get token price from CoinGecko.

    Args:
        token_symbol: Token symbol (e.g., 'WETH', 'ARB')
        date_str: Date in YYYY-MM-DD format

    Returns:
        Price in USD as float, or None if not available
    """
    symbol = token_symbol.upper().strip()

    # Check if it's a stablecoin
    if symbol in STABLECOINS:
        return 1.0

    # Get CoinGecko ID
    cg_id = get_coingecko_id(symbol)
    if not cg_id:
        return None

    return get_historical_price(cg_id, date_str)


def get_current_price(coingecko_id: str) -> Optional[float]:
    """Get current price from CoinGecko."""
    _rate_limit()

    try:
        url = f"{BASE_URL}/simple/price"
        params = {
            'ids': coingecko_id,
            'vs_currencies': 'usd'
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            return None

        data = response.json()
        return data.get(coingecko_id, {}).get('usd')

    except Exception as e:
        return None


def get_supported_tokens() -> List[str]:
    """Get list of tokens with CoinGecko IDs."""
    return list(COINGECKO_IDS.keys()) + list(STABLECOINS)


if __name__ == '__main__':
    print("Testing CoinGecko Price Adapter")
    print("=" * 50)

    # Test current prices
    test_tokens = ['ETH', 'WBTC', 'ARB', 'wstETH', 'USDC']

    print("\nCurrent prices:")
    for token in test_tokens:
        cg_id = get_coingecko_id(token)
        if cg_id:
            price = get_current_price(cg_id)
            if price:
                print(f"  {token}: ${price:,.2f}")
            else:
                print(f"  {token}: Failed to fetch")
        else:
            print(f"  {token}: No CoinGecko ID")

    # Test historical price
    print("\nHistorical price test (2024-06-15):")
    eth_price = get_token_price_coingecko('ETH', '2024-06-15')
    if eth_price:
        print(f"  ETH on 2024-06-15: ${eth_price:,.2f}")
