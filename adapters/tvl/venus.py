"""
Venus TVL Adapter (Compound V2 Fork)

Architecture:
- Registry: Comptroller (Unitroller) contract
- Markets: vTokens (like cTokens in Compound)
- Each vToken represents a lending market

TVL Calculation (Compound-style):
- getCash() - idle funds in contract
- totalBorrows() - total borrowed amount
- totalReserves() - protocol reserves
- TVL = getCash + totalBorrows - totalReserves

Note: Some vTokens wrap native BNB (no underlying() function)
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

# Minimal vToken ABI (Compound-style)
VTOKEN_ABI = [
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

# Minimal ERC20 ABI for underlying
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


def _safe_call(func, default=None):
    """Safely call a contract function."""
    try:
        return func()
    except Exception:
        return default


def get_venus_tvl(web3: Web3, comptroller_address: str, block: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract TVL from Venus Core Pool at a given block.
    
    Args:
        web3: Web3 instance
        comptroller_address: Comptroller (Unitroller) contract address
        block: Block number (None = latest)
        
    Returns:
        List of dicts, one per vToken:
        {
            'vtoken': vToken address,
            'vtoken_symbol': vToken symbol (e.g., 'vUSDC'),
            'vtoken_decimals': vToken decimals,
            'underlying': underlying asset address (None for native BNB),
            'underlying_symbol': underlying symbol,
            'underlying_decimals': underlying decimals,
            'get_cash_raw': idle cash in contract,
            'total_borrows_raw': total borrowed,
            'total_reserves_raw': protocol reserves,
            'total_supply_raw': vToken total supply,
            'tvl_underlying_raw': getCash + totalBorrows - totalReserves,
        }
    """
    comptroller_address = Web3.to_checksum_address(comptroller_address)
    comptroller = web3.eth.contract(address=comptroller_address, abi=COMPTROLLER_ABI)
    
    call_kwargs = {'block_identifier': block} if block is not None else {}
    
    # Step 1: Get all vTokens
    vtoken_addresses = comptroller.functions.getAllMarkets().call(**call_kwargs)
    
    results = []
    
    # Step 2: Query each vToken
    for vtoken_addr in vtoken_addresses:
        vtoken_addr = Web3.to_checksum_address(vtoken_addr)
        vtoken = web3.eth.contract(address=vtoken_addr, abi=VTOKEN_ABI)
        
        try:
            # Get vToken metadata
            vtoken_symbol = _safe_call(lambda: vtoken.functions.symbol().call(**call_kwargs), "UNKNOWN")
            vtoken_decimals = _safe_call(lambda: vtoken.functions.decimals().call(**call_kwargs), 8)
            
            # Get underlying asset (may fail for native BNB markets)
            underlying_addr = _safe_call(lambda: vtoken.functions.underlying().call(**call_kwargs), None)
            underlying_symbol = None
            underlying_decimals = None
            
            if underlying_addr:
                underlying_addr = Web3.to_checksum_address(underlying_addr)
                underlying = web3.eth.contract(address=underlying_addr, abi=ERC20_ABI)
                underlying_symbol = _safe_call(lambda: underlying.functions.symbol().call(**call_kwargs), "UNKNOWN")
                underlying_decimals = _safe_call(lambda: underlying.functions.decimals().call(**call_kwargs), 18)
            else:
                # Native BNB market
                underlying_symbol = "BNB"
                underlying_decimals = 18
            
            # Get TVL values
            get_cash = _safe_call(lambda: vtoken.functions.getCash().call(**call_kwargs), 0)
            total_borrows = _safe_call(lambda: vtoken.functions.totalBorrows().call(**call_kwargs), 0)
            total_reserves = _safe_call(lambda: vtoken.functions.totalReserves().call(**call_kwargs), 0)
            total_supply = _safe_call(lambda: vtoken.functions.totalSupply().call(**call_kwargs), 0)
            
            # TVL in underlying units
            tvl_underlying = get_cash + total_borrows - total_reserves
            
            results.append({
                'vtoken': vtoken_addr,
                'vtoken_symbol': vtoken_symbol,
                'vtoken_decimals': vtoken_decimals,
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
            print(f"Warning: Failed to process vToken {vtoken_addr}: {e}")
            continue
    
    return results


if __name__ == '__main__':
    # Quick test
    from web3 import Web3
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.rpc_config import get_rpc_url
    
    rpc = get_rpc_url('binance')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    # Venus Comptroller on BSC
    comptroller = '0xfd36e2c2a6789db23113685031d7f16329158384'
    
    print("Testing Venus TVL extraction...")
    print(f"Latest block: {w3.eth.block_number:,}")
    
    results = get_venus_tvl(w3, comptroller)
    
    print(f"\n✅ Found {len(results)} vTokens")
    if results:
        print("\nFirst vToken:")
        first = results[0]
        print(f"  vToken: {first['vtoken_symbol']}")
        print(f"  Underlying: {first['underlying_symbol']}")
        if first['underlying_decimals']:
            print(f"  TVL: {first['tvl_underlying_raw'] / 10**first['underlying_decimals']:.2f}")
            print(f"  Cash: {first['get_cash_raw'] / 10**first['underlying_decimals']:.2f}")
            print(f"  Borrows: {first['total_borrows_raw'] / 10**first['underlying_decimals']:.2f}")
