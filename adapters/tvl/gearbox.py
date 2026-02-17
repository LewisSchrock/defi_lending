"""
Gearbox TVL Adapter (Credit Account System)

Architecture:
- AddressProvider → ContractsRegister → Credit Managers
- Each Credit Manager has a pool with underlying token
- Pool tracks totalAssets and totalBorrowed

Discovery:
1. Get ContractsRegister from AddressProvider
2. Call getCreditManagers()
3. For each Credit Manager, get pool() and query pool state
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# AddressProvider ABI
ADDRESS_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getContractsRegister",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ContractsRegister ABI
CONTRACTS_REGISTER_ABI = [
    {
        "inputs": [],
        "name": "getCreditManagers",
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# CreditManager ABI
CREDIT_MANAGER_ABI = [
    {
        "inputs": [],
        "name": "pool",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Pool ABI
POOL_ABI = [
    {
        "inputs": [],
        "name": "underlyingToken",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalBorrowed",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ERC20 ABI
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


def get_gearbox_tvl(
    web3: Web3,
    address_provider: str,
    block: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract TVL from Gearbox at a given block.
    
    Args:
        web3: Web3 instance
        address_provider: AddressProvider contract address
        block: Block number (None = latest)
        
    Returns:
        List of dicts, one per Credit Manager:
        {
            'credit_manager': address,
            'pool': address,
            'underlying_token': address,
            'underlying_symbol': symbol,
            'underlying_decimals': decimals,
            'total_assets_raw': pool totalAssets,
            'total_borrowed_raw': pool totalBorrowed,
            'available_liquidity_raw': totalAssets - totalBorrowed,
        }
    """
    address_provider = Web3.to_checksum_address(address_provider)
    
    call_kwargs = {'block_identifier': block} if block is not None else {}
    
    # Step 1: Get ContractsRegister
    provider = web3.eth.contract(address=address_provider, abi=ADDRESS_PROVIDER_ABI)
    contracts_register_addr = provider.functions.getContractsRegister().call(**call_kwargs)
    contracts_register_addr = Web3.to_checksum_address(contracts_register_addr)
    
    # Step 2: Get all Credit Managers
    contracts_register = web3.eth.contract(address=contracts_register_addr, abi=CONTRACTS_REGISTER_ABI)
    credit_managers = contracts_register.functions.getCreditManagers().call(**call_kwargs)
    
    print(f"Found {len(credit_managers)} Credit Managers")
    
    results = []
    
    # Step 3: Query each Credit Manager
    for cm_addr in credit_managers:
        cm_addr = Web3.to_checksum_address(cm_addr)
        credit_manager = web3.eth.contract(address=cm_addr, abi=CREDIT_MANAGER_ABI)
        
        try:
            # Get pool
            pool_addr = credit_manager.functions.pool().call(**call_kwargs)
            pool_addr = Web3.to_checksum_address(pool_addr)
            pool = web3.eth.contract(address=pool_addr, abi=POOL_ABI)
            
            # Get underlying token
            underlying_addr = pool.functions.underlyingToken().call(**call_kwargs)
            underlying_addr = Web3.to_checksum_address(underlying_addr)
            
            # Get token metadata
            underlying = web3.eth.contract(address=underlying_addr, abi=ERC20_ABI)
            underlying_symbol = _safe_call(lambda: underlying.functions.symbol().call(**call_kwargs), "UNKNOWN")
            underlying_decimals = _safe_call(lambda: underlying.functions.decimals().call(**call_kwargs), 18)
            
            # Get pool state
            total_assets = pool.functions.totalAssets().call(**call_kwargs)
            total_borrowed = pool.functions.totalBorrowed().call(**call_kwargs)
            available_liquidity = total_assets - total_borrowed
            
            results.append({
                'credit_manager': cm_addr,
                'pool': pool_addr,
                'underlying_token': underlying_addr,
                'underlying_symbol': underlying_symbol,
                'underlying_decimals': underlying_decimals,
                'total_assets_raw': total_assets,
                'total_borrowed_raw': total_borrowed,
                'available_liquidity_raw': available_liquidity,
            })
            
        except Exception:
            # Silently skip Credit Managers that fail (deprecated/inactive)
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
    
    # Gearbox AddressProvider on Ethereum
    address_provider = '0xcF64698AFF7E5f27A11dff868AF228653ba53be0'
    
    print("Testing Gearbox TVL extraction...")
    results = get_gearbox_tvl(w3, address_provider)
    
    print(f"\n✅ Found {len(results)} Credit Managers")
    if results:
        print("\nFirst Credit Manager:")
        first = results[0]
        print(f"  Credit Manager: {first['credit_manager']}")
        print(f"  Pool: {first['pool']}")
        print(f"  Underlying: {first['underlying_symbol']}")
        print(f"  Total Assets: {first['total_assets_raw'] / 10**first['underlying_decimals']:.2f}")
        print(f"  Total Borrowed: {first['total_borrowed_raw'] / 10**first['underlying_decimals']:.2f}")
