"""
DefiLlama Price Adapter

Fetches historical token prices from DefiLlama's free API.
No rate limits, unlimited historical data.

API Docs: https://defillama.com/docs/api
"""

import time
import requests
from datetime import datetime
from typing import Dict, Optional, List

# DefiLlama API base URL
BASE_URL = "https://coins.llama.fi"

# Rate limiting (be nice to free API)
_last_call_time = 0
MIN_CALL_INTERVAL = 0.2  # 5 calls/second max

# Token symbol to DefiLlama ID mapping
# Format: "chain:address" or "coingecko:id"
DEFILLAMA_IDS = {
    # Use CoinGecko IDs for most tokens (DefiLlama supports them)
    'ETH': 'coingecko:ethereum',
    'WETH': 'coingecko:weth',
    'BTC': 'coingecko:bitcoin',
    'WBTC': 'coingecko:wrapped-bitcoin',
    'USDC': 'coingecko:usd-coin',
    'USDT': 'coingecko:tether',
    'DAI': 'coingecko:dai',
    'FRAX': 'coingecko:frax',
    'LUSD': 'coingecko:liquity-usd',

    # LSTs
    'stETH': 'coingecko:staked-ether',
    'wstETH': 'coingecko:wrapped-steth',
    'rETH': 'coingecko:rocket-pool-eth',
    'cbETH': 'coingecko:coinbase-wrapped-staked-eth',
    'weETH': 'coingecko:wrapped-eeth',
    'ezETH': 'coingecko:renzo-restaked-eth',
    'rsETH': 'coingecko:kelp-dao-restaked-eth',
    'sfrxETH': 'coingecko:staked-frax-ether',
    'osETH': 'coingecko:stakewise-staked-eth',

    # DeFi tokens
    'LINK': 'coingecko:chainlink',
    'UNI': 'coingecko:uniswap',
    'AAVE': 'coingecko:aave',
    'COMP': 'coingecko:compound-governance-token',
    'MKR': 'coingecko:maker',
    'CRV': 'coingecko:curve-dao-token',
    'SNX': 'coingecko:havven',
    'GNO': 'coingecko:gnosis',
    'GMX': 'coingecko:gmx',
    'PENDLE': 'coingecko:pendle',
    'LDO': 'coingecko:lido-dao',

    # L2 tokens
    'ARB': 'coingecko:arbitrum',
    'OP': 'coingecko:optimism',
    'MATIC': 'coingecko:matic-network',

    # Other
    'AVAX': 'coingecko:avalanche-2',
    'GHO': 'coingecko:gho',
    'tBTC': 'coingecko:tbtc',
    'cbBTC': 'coingecko:coinbase-wrapped-btc',
    'sDAI': 'coingecko:savings-dai',
    'USDS': 'coingecko:usds',
    'MAI': 'coingecko:mimatic',
    'QI': 'coingecko:benqi',
    'sAVAX': 'coingecko:benqi-liquid-staked-avax',
    'WELL': 'coingecko:moonwell-artemis',
    'GEAR': 'coingecko:gearbox',

    # AERO (Base native)
    'AERO': 'coingecko:aerodrome-finance',

    # Additional tokens found in Aave
    'BAL': 'coingecko:balancer',
    'ENS': 'coingecko:ethereum-name-service',
    '1INCH': 'coingecko:1inch',
    'RPL': 'coingecko:rocket-pool',
    'STG': 'coingecko:stargate-finance',
    'KNC': 'coingecko:kyber-network-crystal',
    'FXS': 'coingecko:frax-share',
    'crvUSD': 'coingecko:crvusd',
    'osETH': 'coingecko:stakewise-staked-eth',
    'USDe': 'coingecko:ethena-usde',
    'sUSDe': 'coingecko:ethena-staked-usde',
    'PYUSD': 'coingecko:paypal-usd',
    'cbBTC': 'coingecko:coinbase-wrapped-btc',
    'tBTC': 'coingecko:tbtc',

    # Avalanche tokens
    'WAVAX': 'coingecko:wrapped-avax',
    'sAVAX': 'coingecko:benqi-liquid-staked-avax',
    'BTC.b': 'coingecko:bitcoin-avalanche-bridged-btc-b',
    'BTCb': 'coingecko:bitcoin-avalanche-bridged-btc-b',

    # Other L2/chain tokens
    'METIS': 'coingecko:metis-token',
    'WLD': 'coingecko:worldcoin-wld',

    # Additional LSTs and restaked tokens
    'ETHx': 'coingecko:stader-ethx',
    'mETH': 'coingecko:mantle-staked-ether',
    'pufETH': 'coingecko:puffer-restaked-eth',
    'rswETH': 'coingecko:restaked-swell-eth',
    'stMATIC': 'coingecko:lido-staked-matic',
    'tETH': 'coingecko:treehouse-eth',
    'wOETH': 'coingecko:wrapped-oeth',
    'wrsETH': 'coingecko:wrapped-rseth',
    'wsuperOETHb': 'coingecko:wrapped-super-oethb',

    # Additional BTC variants
    'FBTC': 'coingecko:ignition-fbtc',
    'LBTC': 'coingecko:lombard-staked-btc',
    'eBTC': 'coingecko:ebtc',

    # DeFi and index tokens
    'DPI': 'coingecko:defipulse-index',
    'GHST': 'coingecko:aavegotchi',
    'SKY': 'coingecko:sky',
    'SUSHI': 'coingecko:sushi',

    # Wrapped native tokens
    'WPOL': 'coingecko:wmatic',
    'WXDAI': 'coingecko:wrapped-xdai',
    'MaticX': 'coingecko:stader-maticx',

    # Real world assets
    'EURe': 'coingecko:monerium-eur-money',
    'XAUt': 'coingecko:tether-gold',

    # Avalanche bridged tokens (.e suffix) - map to base token
    # Uppercase variants
    'DAI.E': 'coingecko:dai',
    'WETH.E': 'coingecko:weth',
    'WBTC.E': 'coingecko:wrapped-bitcoin',
    'LINK.E': 'coingecko:chainlink',
    'AAVE.E': 'coingecko:aave',
    'USDC.E': 'coingecko:usd-coin',
    'USDT.E': 'coingecko:tether',
    # Lowercase variants (as seen in bronze data)
    'DAI.e': 'coingecko:dai',
    'WETH.e': 'coingecko:weth',
    'WBTC.e': 'coingecko:wrapped-bitcoin',
    'LINK.e': 'coingecko:chainlink',
    'AAVE.e': 'coingecko:aave',
    'USDC.e': 'coingecko:usd-coin',
    'USDT.e': 'coingecko:tether',

    # BNB Chain tokens
    'WBNB': 'coingecko:wbnb',
    'CAKE': 'coingecko:pancakeswap-token',
    'FDUSD': 'coingecko:first-digital-usd',

    # Euro stablecoins
    'EURS': 'coingecko:stasis-eurs',
    'EURC': 'coingecko:euro-coin',
    'EURA': 'coingecko:ageur',
    'JEUR': 'coingecko:jarvis-synthetic-euro',

    # Additional stablecoins
    'USDBC': 'coingecko:bridged-usd-coin-base',
    'RLUSD': 'coingecko:ripple-usd',
    'USDTB': 'coingecko:tether',  # Treat as USDT
    'USDT0': 'coingecko:tether',  # Stargate USDT variant
    'SUSD': 'coingecko:susd',
    'MUSD': 'coingecko:musd',
    'MIMATIC': 'coingecko:mimatic',

    # Ethena ecosystem
    'EUSDE': 'coingecko:ethena-usde',  # EURe denominated USDe
    'DEUSD': 'coingecko:davos-protocol',
    'SDEUSD': 'coingecko:davos-protocol',  # Staked version

    # Savings/yield tokens
    'SDAI': 'coingecko:savings-dai',
    'SFRAX': 'coingecko:staked-frax',
    'SUSDS': 'coingecko:susds',
    'WUSDM': 'coingecko:wrapped-usdm',

    # Additional LSTs
    'OSETH': 'coingecko:stakewise-staked-eth',
    'WSUPEROETHB': 'coingecko:wrapped-super-oethb',
    'EBTC': 'coingecko:ebtc',

    # Chain-specific tokens
    'QI': 'coingecko:benqi',
    'SCR': 'coingecko:scroll',
    'COMP': 'coingecko:compound-governance-token',

    # BNB Chain
    'BNB': 'coingecko:binancecoin',
    'BTCB': 'coingecko:bitcoin-bep2',
    'XVS': 'coingecko:venus',
    'SXP': 'coingecko:swipe',
    'DOT': 'coingecko:polkadot',
    'ADA': 'coingecko:cardano',
    'DOGE': 'coingecko:dogecoin',
    'LTC': 'coingecko:litecoin',
    'XRP': 'coingecko:ripple',
    'BCH': 'coingecko:bitcoin-cash',
    'FIL': 'coingecko:filecoin',
    'BETH': 'coingecko:binance-eth',
    'TRX': 'coingecko:tron',
    'FLOKI': 'coingecko:floki',
    'UNI': 'coingecko:uniswap',
    'TWT': 'coingecko:trust-wallet-token',

    # Meter chain
    'MTRG': 'coingecko:meter-governance',

    # Wrapped staked BNB
    'wBETH': 'coingecko:wrapped-beacon-eth',
}

# Stablecoins (assume $1.00 USD)
STABLECOINS = {
    # Major USD stables
    'USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'sUSD', 'USDbC',
    'USDC.e', 'DAI.e', 'GHO', 'MAI', 'sDAI', 'USDS', 'USD0',
    'crvUSD', 'PYUSD', 'GUSD', 'TUSD', 'BUSD', 'USDP',
    # Additional stablecoins found in 2025 data
    'USDG', 'mUSD', 'syrupUSDT', 'WXDAI',
    # Sonic chain USDT variant (Unicode)
    'USD₮0',
    # Agora USD
    'AUSD',
    # Bridged stables
    'USDC.E', 'USDT.E', 'DAI.E', 'USDBC',
    # USDT variants
    'USDT0', 'USDTB',
    # First Digital USD
    'FDUSD',
    # Ripple USD
    'RLUSD',
    # Synthetix USD
    'SUSD',
    # mStable USD
    'MUSD',
    # syrup USDT
    'SYRUPUSDT',
}


def _rate_limit():
    """Apply rate limiting between API calls."""
    global _last_call_time
    now = time.time()
    elapsed = now - _last_call_time
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    _last_call_time = time.time()


def get_defillama_id(symbol: str) -> Optional[str]:
    """Get DefiLlama ID for a token symbol."""
    # Try exact match first (for mixed case like wstETH)
    if symbol in DEFILLAMA_IDS:
        return DEFILLAMA_IDS[symbol]
    # Then try uppercase
    if symbol.upper() in DEFILLAMA_IDS:
        return DEFILLAMA_IDS[symbol.upper()]
    # Finally try case-insensitive search
    symbol_upper = symbol.upper()
    for key, value in DEFILLAMA_IDS.items():
        if key.upper() == symbol_upper:
            return value
    return None


def get_historical_price(
    defillama_id: str,
    date_str: str
) -> Optional[float]:
    """
    Get historical price from DefiLlama.

    Args:
        defillama_id: DefiLlama token ID (e.g., 'coingecko:ethereum')
        date_str: Date in YYYY-MM-DD format

    Returns:
        Price in USD as float, or None if failed
    """
    _rate_limit()

    try:
        # Convert date to Unix timestamp (midnight UTC)
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        timestamp = int(dt.timestamp())

        url = f"{BASE_URL}/prices/historical/{timestamp}/{defillama_id}"

        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            return None

        data = response.json()
        coins = data.get('coins', {})

        if defillama_id in coins:
            return coins[defillama_id].get('price')

        return None

    except Exception as e:
        print(f"[DefiLlama] Error fetching {defillama_id} for {date_str}: {e}")
        return None


def get_token_price_defillama(
    token_symbol: str,
    date_str: str
) -> Optional[float]:
    """
    Get token price from DefiLlama.

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

    # Get DefiLlama ID
    dl_id = get_defillama_id(symbol)
    if not dl_id:
        return None

    return get_historical_price(dl_id, date_str)


def get_current_price(defillama_id: str) -> Optional[float]:
    """Get current price from DefiLlama."""
    _rate_limit()

    try:
        url = f"{BASE_URL}/prices/current/{defillama_id}"
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            return None

        data = response.json()
        coins = data.get('coins', {})

        if defillama_id in coins:
            return coins[defillama_id].get('price')

        return None

    except Exception as e:
        return None


def batch_get_historical_prices(
    defillama_ids: List[str],
    date_str: str
) -> Dict[str, Optional[float]]:
    """
    Get historical prices for multiple tokens in one API call.

    Args:
        defillama_ids: List of DefiLlama IDs
        date_str: Date in YYYY-MM-DD format

    Returns:
        Dict of {defillama_id: price}
    """
    _rate_limit()

    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        timestamp = int(dt.timestamp())

        # Batch up to 30 tokens per call
        ids_str = ','.join(defillama_ids[:30])
        url = f"{BASE_URL}/prices/historical/{timestamp}/{ids_str}"

        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            return {dl_id: None for dl_id in defillama_ids}

        data = response.json()
        coins = data.get('coins', {})

        results = {}
        for dl_id in defillama_ids:
            if dl_id in coins:
                results[dl_id] = coins[dl_id].get('price')
            else:
                results[dl_id] = None

        return results

    except Exception as e:
        print(f"[DefiLlama] Batch error: {e}")
        return {dl_id: None for dl_id in defillama_ids}


def get_supported_tokens() -> List[str]:
    """Get list of tokens with DefiLlama IDs."""
    return list(DEFILLAMA_IDS.keys()) + list(STABLECOINS)


if __name__ == '__main__':
    print("Testing DefiLlama Price Adapter")
    print("=" * 50)

    # Test tokens
    test_tokens = ['ETH', 'WBTC', 'ARB', 'wstETH', 'weETH', 'USDC', 'AERO']
    test_date = '2024-06-15'

    print(f"\nHistorical prices for {test_date}:")
    for token in test_tokens:
        price = get_token_price_defillama(token, test_date)
        if price:
            print(f"  {token}: ${price:,.4f}")
        else:
            print(f"  {token}: Not available")

    # Test batch
    print("\nBatch test:")
    ids = [get_defillama_id(t) for t in test_tokens[:5] if get_defillama_id(t)]
    batch_prices = batch_get_historical_prices(ids, test_date)
    for dl_id, price in batch_prices.items():
        print(f"  {dl_id}: ${price:,.4f}" if price else f"  {dl_id}: N/A")
