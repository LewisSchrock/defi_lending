"""
Fluid Lending TVL Adapter

Architecture:
- Registry: FluidLendingResolver contract
- Markets: fTokens (like aTokens)
- Each fToken wraps an underlying ERC20

TVL Extraction:
1. Call getAllFTokens() on resolver
2. For each fToken, read:
   - asset() - underlying token
   - totalAssets() - total supplied in underlying
   - totalSupply() - fToken supply
   - symbol(), decimals()
3. Return raw amounts

Note: Fluid doesn't separate supply/borrow like Aave
- totalAssets() represents the vault TVL
- Borrowing is implicit (not directly visible in fToken)
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# Minimal Resolver ABI
RESOLVER_ABI = [
    {
        "inputs": [],
        "name": "getAllFTokens",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# Minimal fToken ABI
FTOKEN_ABI = [
    {
        "inputs": [],
        "name": "asset",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
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


def get_fluid_tvl(web3: Web3, resolver_address: str, block: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract TVL from Fluid Lending at a given block.
    
    Args:
        web3: Web3 instance
        resolver_address: FluidLendingResolver contract address
        block: Block number (None = latest)
        
    Returns:
        List of dicts, one per fToken:
        {
            'ftoken': fToken address,
            'ftoken_symbol': fToken symbol,
            'ftoken_decimals': fToken decimals,
            'underlying': underlying asset address,
            'underlying_symbol': underlying symbol,
            'underlying_decimals': underlying decimals,
            'total_assets_raw': totalAssets() in underlying units,
            'ftoken_supply_raw': fToken totalSupply,
        }
    """
    resolver_address = Web3.to_checksum_address(resolver_address)
    resolver = web3.eth.contract(address=resolver_address, abi=RESOLVER_ABI)
    
    call_kwargs = {'block_identifier': block} if block is not None else {}
    
    # Step 1: Get all fTokens
    ftoken_addresses = resolver.functions.getAllFTokens().call(**call_kwargs)
    
    results = []
    
    # Step 2: Query each fToken
    for ftoken_addr in ftoken_addresses:
        ftoken_addr = Web3.to_checksum_address(ftoken_addr)
        ftoken = web3.eth.contract(address=ftoken_addr, abi=FTOKEN_ABI)
        
        try:
            # Get fToken metadata
            ftoken_symbol = _safe_call(lambda: ftoken.functions.symbol().call(**call_kwargs), "UNKNOWN")
            ftoken_decimals = _safe_call(lambda: ftoken.functions.decimals().call(**call_kwargs), 18)
            
            # Get underlying asset
            underlying_addr = ftoken.functions.asset().call(**call_kwargs)
            underlying_addr = Web3.to_checksum_address(underlying_addr)
            
            # Get underlying metadata
            underlying = web3.eth.contract(address=underlying_addr, abi=ERC20_ABI)
            underlying_symbol = _safe_call(lambda: underlying.functions.symbol().call(**call_kwargs), "UNKNOWN")
            underlying_decimals = _safe_call(lambda: underlying.functions.decimals().call(**call_kwargs), 18)
            
            # Get TVL values
            total_assets = _safe_call(lambda: ftoken.functions.totalAssets().call(**call_kwargs), 0)
            ftoken_supply = _safe_call(lambda: ftoken.functions.totalSupply().call(**call_kwargs), 0)
            
            results.append({
                'ftoken': ftoken_addr,
                'ftoken_symbol': ftoken_symbol,
                'ftoken_decimals': ftoken_decimals,
                'underlying': underlying_addr,
                'underlying_symbol': underlying_symbol,
                'underlying_decimals': underlying_decimals,
                'total_assets_raw': total_assets,
                'ftoken_supply_raw': ftoken_supply,
            })
            
        except Exception as e:
            print(f"Warning: Failed to process fToken {ftoken_addr}: {e}")
            continue
    
    return results


if __name__ == '__main__':
    # Quick test
    from web3 import Web3
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.rpc_config import get_rpc_url
    
    rpc = get_rpc_url('ethereum')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    # Fluid resolver on Ethereum
    resolver = '0xC215485C572365AE87f908ad35233EC2572A3BEC'
    
    print("Testing Fluid TVL extraction...")
    print(f"Latest block: {w3.eth.block_number:,}")
    
    results = get_fluid_tvl(w3, resolver)
    
    print(f"\n✅ Found {len(results)} fTokens")
    if results:
        print("\nFirst fToken:")
        first = results[0]
        print(f"  fToken: {first['ftoken_symbol']}")
        print(f"  Underlying: {first['underlying_symbol']}")
        print(f"  Total Assets: {first['total_assets_raw'] / 10**first['underlying_decimals']:.2f}")
        print(f"  fToken Supply: {first['ftoken_supply_raw'] / 10**first['ftoken_decimals']:.2f}")
