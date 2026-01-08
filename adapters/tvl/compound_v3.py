"""
Compound V3 (Comet) TVL Adapter

Architecture:
- Each market is a single "Comet" contract
- Registry address IS the Comet contract itself
- One base asset (borrowable, e.g., USDC)
- Multiple collateral assets (cannot be borrowed)

TVL Extraction:
1. Read base asset: totalSupply() and totalBorrow()
2. Read collateral assets: getAssetInfo() + collateralBalanceOf()
3. Return raw token amounts

Key Difference from V2:
- V2: Multiple cTokens per Comptroller
- V3: One Comet = one market
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# Minimal Comet ABI
COMET_ABI = [
    {
        "inputs": [],
        "name": "baseToken",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
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
        "name": "totalBorrow",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "numAssets",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint8", "name": "i", "type": "uint8"}],
        "name": "getAssetInfo",
        "outputs": [
            {
                "components": [
                    {"internalType": "uint8", "name": "offset", "type": "uint8"},
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "address", "name": "priceFeed", "type": "address"},
                    {"internalType": "uint64", "name": "scale", "type": "uint64"},
                    {"internalType": "uint64", "name": "borrowCollateralFactor", "type": "uint64"},
                    {"internalType": "uint64", "name": "liquidateCollateralFactor", "type": "uint64"},
                    {"internalType": "uint64", "name": "liquidationFactor", "type": "uint64"},
                    {"internalType": "uint128", "name": "supplyCap", "type": "uint128"},
                ],
                "internalType": "struct CometCore.AssetInfo",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
        "name": "totalsCollateral",
        "outputs": [
            {"internalType": "uint128", "name": "totalSupplyAsset", "type": "uint128"},
            {"internalType": "uint128", "name": "_reserved", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
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
]


def _safe_call(func, default=None):
    """Safely call a contract function."""
    try:
        return func()
    except Exception:
        return default


def get_compound_v3_tvl(web3: Web3, comet_address: str, block: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract TVL from Compound V3 (Comet) at a given block.
    
    Args:
        web3: Web3 instance
        comet_address: Comet contract address (this IS the market)
        block: Block number (None = latest)
        
    Returns:
        List of dicts with TVL data:
        - Base asset (borrowable): supply and borrow
        - Collateral assets: supply only
    """
    comet_address = Web3.to_checksum_address(comet_address)
    comet = web3.eth.contract(address=comet_address, abi=COMET_ABI)
    
    call_kwargs = {'block_identifier': block} if block is not None else {}
    
    results = []
    
    # Step 1: Get base asset (the borrowable asset, e.g., USDC)
    base_token_address = comet.functions.baseToken().call(**call_kwargs)
    base_token_address = Web3.to_checksum_address(base_token_address)
    
    base_token = web3.eth.contract(address=base_token_address, abi=ERC20_ABI)
    base_symbol = _safe_call(lambda: base_token.functions.symbol().call(**call_kwargs), "UNKNOWN")
    base_decimals = _safe_call(lambda: base_token.functions.decimals().call(**call_kwargs), 18)
    
    # Base asset supply and borrow
    total_supply = _safe_call(lambda: comet.functions.totalSupply().call(**call_kwargs), 0)
    total_borrow = _safe_call(lambda: comet.functions.totalBorrow().call(**call_kwargs), 0)
    
    results.append({
        'asset_type': 'base',
        'underlying': base_token_address,
        'symbol': base_symbol,
        'decimals': base_decimals,
        'supplied_raw': total_supply,
        'borrowed_raw': total_borrow,
    })
    
    # Step 2: Get collateral assets
    num_assets = _safe_call(lambda: comet.functions.numAssets().call(**call_kwargs), 0)
    
    for i in range(num_assets):
        try:
            asset_info = comet.functions.getAssetInfo(i).call(**call_kwargs)
            
            # asset_info is a tuple: (offset, asset, priceFeed, scale, borrowCF, liquidateCF, liquidationFactor, supplyCap)
            collateral_address = Web3.to_checksum_address(asset_info[1])
            
            # Get collateral metadata
            collateral_token = web3.eth.contract(address=collateral_address, abi=ERC20_ABI)
            symbol = _safe_call(lambda: collateral_token.functions.symbol().call(**call_kwargs), f"COLLATERAL_{i}")
            decimals = _safe_call(lambda: collateral_token.functions.decimals().call(**call_kwargs), 18)
            
            # Get total collateral supplied
            collateral_totals = comet.functions.totalsCollateral(collateral_address).call(**call_kwargs)
            total_supply_collateral = collateral_totals[0]  # First element is totalSupplyAsset
            
            results.append({
                'asset_type': 'collateral',
                'underlying': collateral_address,
                'symbol': symbol,
                'decimals': decimals,
                'supplied_raw': total_supply_collateral,
                'borrowed_raw': 0,  # Collateral cannot be borrowed in V3
            })
            
        except Exception as e:
            print(f"Warning: Failed to get collateral asset {i}: {e}")
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
    
    # Compound V3 USDC market on Ethereum
    comet = '0xc3d688B66703497DAA19211EEdff47f25384cdc3'
    
    print("Testing Compound V3 TVL extraction...")
    print(f"Latest block: {w3.eth.block_number:,}")
    
    results = get_compound_v3_tvl(w3, comet)
    
    print(f"\n✅ Found {len(results)} assets")
    if results:
        print("\nBase asset:")
        base = results[0]
        print(f"  Symbol: {base['symbol']}")
        print(f"  Supplied: {base['supplied_raw'] / 10**base['decimals']:.2f}")
        print(f"  Borrowed: {base['borrowed_raw'] / 10**base['decimals']:.2f}")
        
        if len(results) > 1:
            print(f"\nCollateral assets ({len(results)-1}):")
            for coll in results[1:]:
                print(f"  {coll['symbol']}: {coll['supplied_raw'] / 10**coll['decimals']:.2f}")
