"""
Lista Lending TVL Adapter (Morpho-style)

Architecture:
- Moolah core contract (registry)
- Vaults that reference market IDs via withdrawQueue
- Each market has loanToken and collateralToken
- Market state includes totalSupplyAssets and totalBorrowAssets

Discovery:
1. Enumerate vaults from config
2. Read withdrawQueue from each vault to get market IDs
3. Query Moolah for market params and state
"""

from typing import Dict, List, Any, Optional, Set
from web3 import Web3

# Moolah ABI - market discovery and state
MOOLAH_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "id", "type": "bytes32"}],
        "name": "idToMarketParams",
        "outputs": [
            {"internalType": "address", "name": "loanToken", "type": "address"},
            {"internalType": "address", "name": "collateralToken", "type": "address"},
            {"internalType": "address", "name": "oracle", "type": "address"},
            {"internalType": "address", "name": "irm", "type": "address"},
            {"internalType": "uint256", "name": "lltv", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "id", "type": "bytes32"}],
        "name": "market",
        "outputs": [
            {"internalType": "uint128", "name": "totalSupplyAssets", "type": "uint128"},
            {"internalType": "uint128", "name": "totalSupplyShares", "type": "uint128"},
            {"internalType": "uint128", "name": "totalBorrowAssets", "type": "uint128"},
            {"internalType": "uint128", "name": "totalBorrowShares", "type": "uint128"},
            {"internalType": "uint128", "name": "lastUpdate", "type": "uint128"},
            {"internalType": "uint128", "name": "fee", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# Vault ABI - withdrawQueue discovery
VAULT_ABI = [
    {
        "inputs": [],
        "name": "withdrawQueueLength",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "withdrawQueue",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
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


def _discover_market_ids(web3: Web3, vault_addresses: List[str]) -> Set[bytes]:
    """Discover all market IDs referenced by vaults."""
    market_ids: Set[bytes] = set()
    
    for vault_addr in vault_addresses:
        vault_addr = Web3.to_checksum_address(vault_addr)
        vault = web3.eth.contract(address=vault_addr, abi=VAULT_ABI)
        
        try:
            queue_len = vault.functions.withdrawQueueLength().call()
        except Exception:
            continue
        
        for i in range(int(queue_len)):
            try:
                market_id = vault.functions.withdrawQueue(i).call()
                if isinstance(market_id, (bytes, bytearray)) and len(market_id) == 32:
                    market_ids.add(bytes(market_id))
            except Exception:
                continue
    
    return market_ids


def get_lista_tvl(
    web3: Web3,
    moolah_address: str,
    vault_addresses: List[str],
    block: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract TVL from Lista Lending at a given block.
    
    Args:
        web3: Web3 instance
        moolah_address: Moolah core contract address
        vault_addresses: List of vault addresses
        block: Block number (None = latest)
        
    Returns:
        List of dicts, one per market:
        {
            'market_id': bytes32 hex,
            'loan_token': address,
            'loan_symbol': symbol,
            'loan_decimals': decimals,
            'collateral_token': address,
            'collateral_symbol': symbol,
            'collateral_decimals': decimals,
            'total_supply_assets_raw': uint128,
            'total_borrow_assets_raw': uint128,
            'lltv': loan-to-value ratio (in basis points),
        }
    """
    moolah_address = Web3.to_checksum_address(moolah_address)
    moolah = web3.eth.contract(address=moolah_address, abi=MOOLAH_ABI)
    
    call_kwargs = {'block_identifier': block} if block is not None else {}
    
    # Step 1: Discover market IDs from vaults
    print(f"Discovering market IDs from {len(vault_addresses)} vaults...")
    market_ids = _discover_market_ids(web3, vault_addresses)
    print(f"Found {len(market_ids)} unique market IDs")
    
    results = []
    
    # Step 2: Query each market
    for market_id_bytes in market_ids:
        try:
            # Get market params
            params = moolah.functions.idToMarketParams(market_id_bytes).call(**call_kwargs)
            loan_token = Web3.to_checksum_address(params[0])
            collateral_token = Web3.to_checksum_address(params[1])
            lltv = params[4]
            
            # Get market state
            state = moolah.functions.market(market_id_bytes).call(**call_kwargs)
            total_supply_assets = state[0]
            total_borrow_assets = state[2]
            
            # Get token metadata
            loan_erc20 = web3.eth.contract(address=loan_token, abi=ERC20_ABI)
            loan_symbol = _safe_call(lambda: loan_erc20.functions.symbol().call(**call_kwargs), "UNKNOWN")
            loan_decimals = _safe_call(lambda: loan_erc20.functions.decimals().call(**call_kwargs), 18)
            
            collateral_erc20 = web3.eth.contract(address=collateral_token, abi=ERC20_ABI)
            collateral_symbol = _safe_call(lambda: collateral_erc20.functions.symbol().call(**call_kwargs), "UNKNOWN")
            collateral_decimals = _safe_call(lambda: collateral_erc20.functions.decimals().call(**call_kwargs), 18)
            
            results.append({
                'market_id': '0x' + market_id_bytes.hex(),
                'loan_token': loan_token,
                'loan_symbol': loan_symbol,
                'loan_decimals': loan_decimals,
                'collateral_token': collateral_token,
                'collateral_symbol': collateral_symbol,
                'collateral_decimals': collateral_decimals,
                'total_supply_assets_raw': total_supply_assets,
                'total_borrow_assets_raw': total_borrow_assets,
                'lltv': lltv,
            })
            
        except Exception as e:
            market_id_hex = '0x' + market_id_bytes.hex()
            print(f"Warning: Failed to process market {market_id_hex}: {e}")
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
    
    # Lista addresses on BSC
    moolah = '0x8F73b65B4caAf64FBA2aF91cC5D4a2A1318E5D8C'
    vaults = [
        '0x834e8641d7422fe7c19a56d05516ed877b3d01e0',
        '0x3036929665c69358fc092ee726448ed9c096014f',
        '0x724205704cd9384793e0baf3426d5dde8cf9b1b4',
    ]
    
    print("Testing Lista TVL extraction...")
    results = get_lista_tvl(w3, moolah, vaults)
    
    print(f"\n✅ Found {len(results)} markets")
    if results:
        print("\nFirst market:")
        first = results[0]
        print(f"  Market ID: {first['market_id']}")
        print(f"  Loan: {first['loan_symbol']}")
        print(f"  Collateral: {first['collateral_symbol']}")
        print(f"  Supply: {first['total_supply_assets_raw'] / 10**first['loan_decimals']:.2f}")
        print(f"  Borrow: {first['total_borrow_assets_raw'] / 10**first['loan_decimals']:.2f}")
