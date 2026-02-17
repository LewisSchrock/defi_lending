"""
Generic Compound V2-Style TVL Adapter

Works for any protocol following the Compound V2 pattern:
- Comptroller with getAllMarkets()
- cTokens/vTokens/qTokens with:
  - getCash(), totalBorrows(), totalReserves()
  - underlying() (may fail for native tokens)

Supported protocols:
- Venus (BSC)
- Benqi (Avalanche)
- Moonwell (Base)
- Kinetic (Flare)
- Tectonic (Cronos)
- Sumer (CORE)
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# Minimal Comptroller ABI
COMPTROLLER_ABI = [
    {
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# Minimal cToken/vToken/qToken ABI (Compound-style)
CTOKEN_ABI = [
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getCash",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalBorrows",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalReserves",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "underlying",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Minimal ERC20 ABI
ERC20_ABI = [
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def _safe_call(func, default=None, retries=2):
    """Safely call a contract function. Retries on connection errors."""
    import time
    for attempt in range(retries + 1):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()
            if attempt < retries and ('connection' in error_str or 'remote' in error_str or 'timeout' in error_str):
                time.sleep(0.5 * (attempt + 1))
                continue
            return default


def get_compound_style_tvl(
    web3: Web3,
    comptroller_address: str,
    block: Optional[int] = None,
    token_prefix: str = "cToken"
) -> List[Dict[str, Any]]:
    """
    Generic TVL extraction for Compound V2-style protocols.
    
    Args:
        web3: Web3 instance
        comptroller_address: Comptroller contract address
        block: Block number (None = latest)
        token_prefix: Token name for logging (cToken, vToken, qToken, etc.)
        
    Returns:
        List of dicts, one per market token:
        {
            'market_token': address,
            'market_symbol': symbol,
            'market_decimals': decimals,
            'underlying': underlying address (None for native),
            'underlying_symbol': symbol,
            'underlying_decimals': decimals,
            'get_cash_raw': idle cash,
            'total_borrows_raw': total borrowed,
            'total_reserves_raw': protocol reserves,
            'total_supply_raw': market token supply,
            'tvl_underlying_raw': getCash + totalBorrows - totalReserves,
        }
    """
    comptroller_address = Web3.to_checksum_address(comptroller_address)
    comptroller = web3.eth.contract(address=comptroller_address, abi=COMPTROLLER_ABI)

    call_kwargs = {'block_identifier': block} if block is not None else {}

    # Get all markets (with retry for connection errors)
    import time
    market_addresses = None
    for attempt in range(3):
        try:
            market_addresses = comptroller.functions.getAllMarkets().call(**call_kwargs)
            break
        except Exception as e:
            error_str = str(e).lower()
            if attempt < 2 and ('connection' in error_str or 'remote' in error_str or 'timeout' in error_str):
                time.sleep(1 * (attempt + 1))
                continue
            raise

    if market_addresses is None:
        return []
    
    results = []
    
    for market_addr in market_addresses:
        market_addr = Web3.to_checksum_address(market_addr)
        market_token = web3.eth.contract(address=market_addr, abi=CTOKEN_ABI)
        
        try:
            # Get market token metadata
            market_symbol = _safe_call(lambda: market_token.functions.symbol().call(**call_kwargs), "UNKNOWN")
            market_decimals = _safe_call(lambda: market_token.functions.decimals().call(**call_kwargs), 8)
            
            # Get underlying asset (may fail for native tokens)
            underlying_addr = _safe_call(lambda: market_token.functions.underlying().call(**call_kwargs), None)
            underlying_symbol = None
            underlying_decimals = None
            
            if underlying_addr:
                underlying_addr = Web3.to_checksum_address(underlying_addr)
                underlying = web3.eth.contract(address=underlying_addr, abi=ERC20_ABI)
                underlying_symbol = _safe_call(lambda: underlying.functions.symbol().call(**call_kwargs), "UNKNOWN")
                underlying_decimals = _safe_call(lambda: underlying.functions.decimals().call(**call_kwargs), 18)
            else:
                # Native token market (ETH, BNB, AVAX, etc.)
                underlying_symbol = "NATIVE"
                underlying_decimals = 18
            
            # Get TVL values
            get_cash = _safe_call(lambda: market_token.functions.getCash().call(**call_kwargs), 0)
            total_borrows = _safe_call(lambda: market_token.functions.totalBorrows().call(**call_kwargs), 0)
            total_reserves = _safe_call(lambda: market_token.functions.totalReserves().call(**call_kwargs), 0)
            total_supply = _safe_call(lambda: market_token.functions.totalSupply().call(**call_kwargs), 0)
            
            # TVL in underlying units = cash + borrows - reserves
            tvl_underlying = get_cash + total_borrows - total_reserves
            
            results.append({
                'market_token': market_addr,
                'market_symbol': market_symbol,
                'market_decimals': market_decimals,
                'underlying': underlying_addr,
                'underlying_symbol': underlying_symbol,
                'underlying_decimals': underlying_decimals,
                'get_cash_raw': get_cash,
                'total_borrows_raw': total_borrows,
                'total_reserves_raw': total_reserves,
                'total_supply_raw': total_supply,
                'tvl_underlying_raw': tvl_underlying,
            })
            
        except Exception as e:
            print(f"Warning: Failed to process {token_prefix} {market_addr}: {e}")
            continue
    
    return results


# Convenience wrappers for specific protocols
def get_venus_tvl(web3: Web3, comptroller: str, block: Optional[int] = None):
    """Venus on BSC."""
    return get_compound_style_tvl(web3, comptroller, block, "vToken")

def get_benqi_tvl(web3: Web3, comptroller: str, block: Optional[int] = None):
    """Benqi on Avalanche."""
    return get_compound_style_tvl(web3, comptroller, block, "qToken")

def get_moonwell_tvl(web3: Web3, comptroller: str, block: Optional[int] = None):
    """Moonwell on Base."""
    return get_compound_style_tvl(web3, comptroller, block, "mToken")

def get_kinetic_tvl(web3: Web3, comptroller: str, block: Optional[int] = None):
    """Kinetic on Flare."""
    return get_compound_style_tvl(web3, comptroller, block, "kToken")

def get_tectonic_tvl(web3: Web3, comptroller: str, block: Optional[int] = None):
    """Tectonic on Cronos."""
    return get_compound_style_tvl(web3, comptroller, block, "tToken")

def get_sumer_tvl(web3: Web3, comptroller: str, block: Optional[int] = None):
    """Sumer on CORE."""
    return get_compound_style_tvl(web3, comptroller, block, "cToken")


if __name__ == '__main__':
    # Test with Venus
    from web3 import Web3
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.rpc_config import get_rpc_url
    
    rpc = get_rpc_url('binance')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    comptroller = '0xfd36e2c2a6789db23113685031d7f16329158384'
    
    print("Testing generic Compound-style TVL with Venus...")
    results = get_venus_tvl(w3, comptroller)
    
    print(f"✅ Found {len(results)} markets")
    if results:
        print(f"\nFirst market: {results[0]['market_symbol']}")
        print(f"Underlying: {results[0]['underlying_symbol']}")
