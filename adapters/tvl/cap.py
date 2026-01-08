"""
Cap TVL Adapter (Perpetual DEX Lending)

Architecture:
- Single ERC4626-style vault
- Has a debt token that tracks borrowing
- totalAssets() - total supplied to vault
- debtToken.totalSupply() - total borrowed
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# Vault ABI
VAULT_ABI = [
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalIdle",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalDebt",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "asset",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "debtToken",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ERC20 ABI (for debt token and underlying)
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


def _safe_call(func, default=None):
    """Safely call a contract function."""
    try:
        return func()
    except Exception:
        return default


def get_cap_tvl(
    web3: Web3,
    vault_address: str,
    block: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract TVL from Cap vault at a given block.
    
    Args:
        web3: Web3 instance
        vault_address: Cap vault contract address
        block: Block number (None = latest)
        
    Returns:
        List with single dict:
        {
            'vault': vault address,
            'underlying_token': asset address,
            'underlying_symbol': asset symbol,
            'underlying_decimals': asset decimals,
            'debt_token': debt token address,
            'debt_token_symbol': debt token symbol,
            'total_assets_raw': totalAssets() in underlying,
            'total_borrowed_raw': debtToken.totalSupply(),
            'available_liquidity_raw': totalAssets - totalBorrowed,
        }
    """
    vault_address = Web3.to_checksum_address(vault_address)
    vault = web3.eth.contract(address=vault_address, abi=VAULT_ABI)
    
    call_kwargs = {'block_identifier': block} if block is not None else {}
    
    try:
        # Get vault state (matching sandbox implementation)
        total_assets = vault.functions.totalAssets().call(**call_kwargs)
        total_idle = vault.functions.totalIdle().call(**call_kwargs)
        total_debt = vault.functions.totalDebt().call(**call_kwargs)
        
        underlying_addr = vault.functions.asset().call(**call_kwargs)
        underlying_addr = Web3.to_checksum_address(underlying_addr)
        debt_token_addr = vault.functions.debtToken().call(**call_kwargs)
        debt_token_addr = Web3.to_checksum_address(debt_token_addr)
        
        # Get underlying token metadata
        underlying = web3.eth.contract(address=underlying_addr, abi=ERC20_ABI)
        underlying_symbol = _safe_call(lambda: underlying.functions.symbol().call(**call_kwargs), "UNKNOWN")
        underlying_decimals = _safe_call(lambda: underlying.functions.decimals().call(**call_kwargs), 18)
        
        # Get debt token metadata and supply
        debt_token = web3.eth.contract(address=debt_token_addr, abi=ERC20_ABI)
        debt_token_symbol = _safe_call(lambda: debt_token.functions.symbol().call(**call_kwargs), "UNKNOWN")
        total_borrowed = debt_token.functions.totalSupply().call(**call_kwargs)
        
        # Calculate available liquidity
        available_liquidity = total_assets - total_borrowed if total_assets >= total_borrowed else 0
        
        return [{
            'vault': vault_address,
            'underlying_token': underlying_addr,
            'underlying_symbol': underlying_symbol,
            'underlying_decimals': underlying_decimals,
            'debt_token': debt_token_addr,
            'debt_token_symbol': debt_token_symbol,
            'total_assets_raw': total_assets,
            'total_idle_raw': total_idle,
            'total_debt_raw': total_debt,
            'total_borrowed_raw': total_borrowed,
            'available_liquidity_raw': available_liquidity,
        }]
        
    except Exception as e:
        print(f"Error processing Cap vault {vault_address}: {e}")
        return []


if __name__ == '__main__':
    # Quick test
    from web3 import Web3
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.rpc_config import get_rpc_url
    
    rpc = get_rpc_url('ethereum')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    # Cap vault on Ethereum (USDC vault)
    vault = '0x3Ed6aa32c930253fc990dE58fF882B9186cd0072'
    
    print("Testing Cap TVL extraction...")
    results = get_cap_tvl(w3, vault)
    
    if results:
        print("\n✅ Cap vault data:")
        first = results[0]
        print(f"  Vault: {first['vault']}")
        print(f"  Underlying: {first['underlying_symbol']}")
        print(f"  Total Assets: {first['total_assets_raw'] / 10**first['underlying_decimals']:.2f}")
        print(f"  Total Borrowed: {first['total_borrowed_raw'] / 10**first['underlying_decimals']:.2f}")
        print(f"  Available Liquidity: {first['available_liquidity_raw'] / 10**first['underlying_decimals']:.2f}")
    else:
        print("❌ Failed to extract Cap TVL")
