"""
Aave V3 TVL Adapter

Architecture:
- Registry: PoolAddressesProvider (0x2f39... on Ethereum, different per chain)
- Pool: Main lending pool contract
- DataProvider: Provides reserve metadata (aToken, debt token addresses)

TVL Extraction:
1. Resolve Pool and DataProvider from registry
2. Get list of reserves (underlying assets)
3. For each reserve, get associated tokens (aToken, stableDebtToken, variableDebtToken)
4. Read totalSupply from each token
5. Return raw token amounts (no USD conversion yet)
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# Minimal ABIs - only what we need
ADDRESSES_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getPoolDataProvider",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

POOL_ABI = [
    {
        "inputs": [],
        "name": "getReservesList",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

DATA_PROVIDER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "getReserveTokensAddresses",
        "outputs": [
            {"internalType": "address", "name": "aTokenAddress", "type": "address"},
            {"internalType": "address", "name": "stableDebtTokenAddress", "type": "address"},
            {"internalType": "address", "name": "variableDebtTokenAddress", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

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
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def _safe_call(func, default=None, retries=2):
    """Safely call a contract function, return default on error. Retries on connection errors."""
    import time
    for attempt in range(retries + 1):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()
            # Retry on connection errors
            if attempt < retries and ('connection' in error_str or 'remote' in error_str or 'timeout' in error_str):
                time.sleep(0.5 * (attempt + 1))
                continue
            return default


def get_aave_v3_tvl(web3: Web3, registry: str, block: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract TVL from Aave V3 at a given block.
    
    Args:
        web3: Web3 instance
        registry: PoolAddressesProvider address
        block: Block number (None = latest)
        
    Returns:
        List of dicts, one per reserve:
        {
            'underlying': asset address,
            'symbol': asset symbol,
            'decimals': asset decimals,
            'a_token': aToken address,
            'stable_debt': stableDebtToken address,
            'variable_debt': variableDebtToken address,
            'supplied_raw': aToken totalSupply (integer),
            'stable_debt_raw': stableDebt totalSupply (integer),
            'variable_debt_raw': variableDebt totalSupply (integer),
        }
    """
    registry = Web3.to_checksum_address(registry)
    
    # Step 1: Resolve Pool and DataProvider from registry
    provider_contract = web3.eth.contract(address=registry, abi=ADDRESSES_PROVIDER_ABI)
    
    call_kwargs = {'block_identifier': block} if block is not None else {}
    
    pool_address = provider_contract.functions.getPool().call(**call_kwargs)
    data_provider_address = provider_contract.functions.getPoolDataProvider().call(**call_kwargs)
    
    pool_address = Web3.to_checksum_address(pool_address)
    data_provider_address = Web3.to_checksum_address(data_provider_address)
    
    # Step 2: Get list of reserves
    pool_contract = web3.eth.contract(address=pool_address, abi=POOL_ABI)
    reserves = pool_contract.functions.getReservesList().call(**call_kwargs)
    
    # Step 3: For each reserve, get token addresses and balances
    data_provider = web3.eth.contract(address=data_provider_address, abi=DATA_PROVIDER_ABI)
    
    results = []
    
    for asset in reserves:
        asset = Web3.to_checksum_address(asset)
        
        # Get associated token addresses with retry
        token_addresses = None
        for attempt in range(3):
            try:
                a_token, stable_debt, variable_debt = data_provider.functions.getReserveTokensAddresses(asset).call(**call_kwargs)
                a_token = Web3.to_checksum_address(a_token)
                stable_debt = Web3.to_checksum_address(stable_debt)
                variable_debt = Web3.to_checksum_address(variable_debt)
                token_addresses = (a_token, stable_debt, variable_debt)
                break
            except Exception as e:
                error_str = str(e).lower()
                if attempt < 2 and ('connection' in error_str or 'remote' in error_str or 'timeout' in error_str):
                    import time
                    time.sleep(0.5 * (attempt + 1))
                    continue
                # Skip this reserve on persistent failure
                break

        if token_addresses is None:
            continue

        a_token, stable_debt, variable_debt = token_addresses
        
        # Get underlying asset metadata
        underlying_contract = web3.eth.contract(address=asset, abi=ERC20_ABI)
        symbol = _safe_call(lambda: underlying_contract.functions.symbol().call(**call_kwargs), "UNKNOWN")
        decimals = _safe_call(lambda: underlying_contract.functions.decimals().call(**call_kwargs), 18)
        
        # Get token supplies
        a_token_contract = web3.eth.contract(address=a_token, abi=ERC20_ABI)
        stable_debt_contract = web3.eth.contract(address=stable_debt, abi=ERC20_ABI)
        variable_debt_contract = web3.eth.contract(address=variable_debt, abi=ERC20_ABI)
        
        supplied_raw = _safe_call(lambda: a_token_contract.functions.totalSupply().call(**call_kwargs), 0)
        stable_debt_raw = _safe_call(lambda: stable_debt_contract.functions.totalSupply().call(**call_kwargs), 0)
        variable_debt_raw = _safe_call(lambda: variable_debt_contract.functions.totalSupply().call(**call_kwargs), 0)
        
        results.append({
            'underlying': asset,
            'symbol': symbol,
            'decimals': decimals,
            'a_token': a_token,
            'stable_debt': stable_debt,
            'variable_debt': variable_debt,
            'supplied_raw': supplied_raw,
            'stable_debt_raw': stable_debt_raw,
            'variable_debt_raw': variable_debt_raw,
        })
    
    return results


if __name__ == '__main__':
    # Quick test
    from web3 import Web3
    import sys
    import os
    
    # Add parent to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.rpc_config import get_rpc_url
    
    rpc = get_rpc_url('ethereum')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    registry = '0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e'  # Ethereum mainnet
    
    print("Testing Aave V3 TVL extraction...")
    print(f"Latest block: {w3.eth.block_number:,}")
    
    results = get_aave_v3_tvl(w3, registry)
    
    print(f"\n✅ Found {len(results)} reserves")
    if results:
        print("\nFirst reserve:")
        first = results[0]
        print(f"  Symbol: {first['symbol']}")
        print(f"  Underlying: {first['underlying']}")
        print(f"  Decimals: {first['decimals']}")
        print(f"  Supplied: {first['supplied_raw'] / 10**first['decimals']:.2f}")
        print(f"  Borrowed (stable): {first['stable_debt_raw'] / 10**first['decimals']:.2f}")
        print(f"  Borrowed (variable): {first['variable_debt_raw'] / 10**first['decimals']:.2f}")
