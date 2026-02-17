"""
Fluid Lending TVL Adapter

Architecture:
- Registry: FluidLendingResolver contract (uses getAllFTokens)
- Markets: fTokens (like aTokens)
- Each fToken wraps an underlying ERC20
- Borrow data: FluidLiquidityResolver (getOverallTokenData per underlying)

TVL Extraction:
1. Call getAllFTokens() on FluidLendingResolver
2. For each fToken, read:
   - asset() - underlying token
   - totalAssets() - total supplied in underlying
   - totalSupply() - fToken supply
   - symbol(), decimals()
3. Query FluidLiquidityResolver.getOverallTokenData(underlying) for borrow amounts
4. Return raw amounts including total_borrow_raw

Note: Supply data comes from fTokens (FluidLendingResolver, deployed 2024).
Borrow data comes from FluidLiquidityResolver (getOverallTokenData).
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# Map FluidLendingResolver -> FluidLiquidityResolver per chain
# The collector passes the LendingResolver address as 'registry',
# so we use it to look up the corresponding LiquidityResolver.
LIQUIDITY_RESOLVER_MAP = {
    # Ethereum
    '0xC215485C572365AE87f908ad35233EC2572A3BEC': '0xD7588F6c99605Ab274C211a0AFeC60947668A8Cb',
    # Arbitrum
    '0xdF4d3272FfAE8036d9a2E1626Df2Db5863b4b302': '0x46859d33E662d4bF18eEED88f74C36256E606e44',
    # Base
    '0x264786EF916af64a1DB19F513F24a3681734ce92': '0x35A915336e2b3349FA94c133491b915eD3D3b0cd',
}

# FluidLendingResolver ABI (2024 version)
RESOLVER_ABI = [
    {
        "inputs": [],
        "name": "getAllFTokens",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# FluidLiquidityResolver ABI - getOverallTokenData
LIQUIDITY_RESOLVER_ABI = [
    {
        "inputs": [{"name": "token_", "type": "address"}],
        "name": "getOverallTokenData",
        "outputs": [{
            "type": "tuple",
            "components": [
                {"name": "borrowRate", "type": "uint256"},
                {"name": "supplyRate", "type": "uint256"},
                {"name": "fee", "type": "uint256"},
                {"name": "lastStoredUtilization", "type": "uint256"},
                {"name": "storageUpdateThreshold", "type": "uint256"},
                {"name": "lastUpdateTimestamp", "type": "uint256"},
                {"name": "supplyExchangePrice", "type": "uint256"},
                {"name": "borrowExchangePrice", "type": "uint256"},
                {"name": "supplyRawInterest", "type": "uint256"},
                {"name": "supplyInterestFree", "type": "uint256"},
                {"name": "borrowRawInterest", "type": "uint256"},
                {"name": "borrowInterestFree", "type": "uint256"},
                {"name": "totalSupply", "type": "uint256"},
                {"name": "totalBorrow", "type": "uint256"},
                {"name": "revenue", "type": "uint256"},
            ]
        }],
        "stateMutability": "view",
        "type": "function",
    }
]

# fToken ABI
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


def _get_token_borrow(liquidity_resolver, underlying_addr: str, call_kwargs: dict) -> int:
    """
    Query FluidLiquidityResolver for total borrow of a specific token.

    Returns total borrow amount in underlying token units, or 0 on failure.
    """
    try:
        data = liquidity_resolver.functions.getOverallTokenData(
            Web3.to_checksum_address(underlying_addr)
        ).call(**call_kwargs)
        # Index 13 = totalBorrow
        return data[13]
    except Exception:
        return 0


def get_fluid_tvl(web3: Web3, resolver_address: str, block: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract TVL from Fluid Lending at a given block.

    Uses FluidLendingResolver for fToken discovery and supply data,
    and FluidLiquidityResolver for per-token borrow amounts.

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
            'total_borrow_raw': total borrowed for underlying token,
        }
    """
    resolver_address = Web3.to_checksum_address(resolver_address)
    resolver = web3.eth.contract(address=resolver_address, abi=RESOLVER_ABI)

    call_kwargs = {'block_identifier': block} if block is not None else {}

    # Set up FluidLiquidityResolver for borrow data
    liq_resolver_addr = LIQUIDITY_RESOLVER_MAP.get(resolver_address)
    liquidity_resolver = None
    if liq_resolver_addr:
        liquidity_resolver = web3.eth.contract(
            address=Web3.to_checksum_address(liq_resolver_addr),
            abi=LIQUIDITY_RESOLVER_ABI
        )

    # Step 1: Get all fTokens
    ftoken_addresses = resolver.functions.getAllFTokens().call(**call_kwargs)

    results = []

    # Track which underlying tokens we've already queried for borrows
    # (multiple fTokens can share the same underlying)
    borrow_cache = {}

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

            # Get supply values from fToken
            total_assets = _safe_call(lambda: ftoken.functions.totalAssets().call(**call_kwargs), 0)
            ftoken_supply = _safe_call(lambda: ftoken.functions.totalSupply().call(**call_kwargs), 0)

            # Get borrow from FluidLiquidityResolver (cached per underlying)
            total_borrow = 0
            if liquidity_resolver is not None:
                if underlying_addr not in borrow_cache:
                    borrow_cache[underlying_addr] = _get_token_borrow(
                        liquidity_resolver, underlying_addr, call_kwargs
                    )
                total_borrow = borrow_cache[underlying_addr]

            results.append({
                'ftoken': ftoken_addr,
                'ftoken_symbol': ftoken_symbol,
                'ftoken_decimals': ftoken_decimals,
                'underlying': underlying_addr,
                'underlying_symbol': underlying_symbol,
                'underlying_decimals': underlying_decimals,
                'total_assets_raw': total_assets,
                'ftoken_supply_raw': ftoken_supply,
                'total_borrow_raw': total_borrow,
            })

        except Exception as e:
            print(f"Warning: Failed to process fToken {ftoken_addr}: {e}")
            continue

    return results


if __name__ == '__main__':
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    rpc_key = os.environ.get('ALCHEMY_KEY_1', '')
    if not rpc_key:
        print("Set ALCHEMY_KEY_1 environment variable")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(f'https://eth-mainnet.g.alchemy.com/v2/{rpc_key}'))

    # FluidLendingResolver on Ethereum
    resolver = '0xC215485C572365AE87f908ad35233EC2572A3BEC'

    print("Testing Fluid TVL extraction (with borrow data)...")
    print(f"Latest block: {w3.eth.block_number:,}")

    results = get_fluid_tvl(w3, resolver)

    print(f"\nFound {len(results)} fTokens")
    for r in results:
        supply = r['total_assets_raw'] / 10**r['underlying_decimals']
        borrow = r['total_borrow_raw'] / 10**r['underlying_decimals']
        util = borrow / supply if supply > 0 else 0
        print(f"  {r['ftoken_symbol']} ({r['underlying_symbol']}): "
              f"supply={supply:,.2f}  borrow={borrow:,.2f}  util={util:.1%}")
