"""
Morpho Blue TVL Adapter

Architecture:
- Singleton contract deployed at 0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb on all chains
- Markets identified by bytes32 IDs
- Each market has: loanToken, collateralToken, oracle, irm, lltv
- Market state: totalSupplyAssets, totalSupplyShares, totalBorrowAssets, totalBorrowShares

TVL Extraction:
1. Discover market IDs via CreateMarket events (emitted from genesis to target block)
2. For each market, query idToMarketParams() for token addresses
3. Query market() for supply/borrow state
4. Return raw token amounts

Note: This same adapter pattern also works for Lista (Moolah) on chains where
Lista uses the Morpho Blue singleton (e.g., Base, Ethereum).
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from web3 import Web3

# Morpho Blue singleton ABI
MORPHO_ABI = [
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

# CreateMarket event topic0:
# CreateMarket(bytes32 indexed id, (address,address,address,address,uint256) marketParams)
# keccak256("CreateMarket(bytes32,(address,address,address,address,uint256))")
CREATE_MARKET_TOPIC = '0xac4b2400f169220b0c0afdde7a0b32e775ba727ea1cb30b35f935cdaab8683ac'

# Morpho Blue deployment blocks per chain (to limit event scanning)
DEPLOYMENT_BLOCKS = {
    'ethereum': 18883124,   # Morpho Blue deployed Jan 2024
    'base': 11842838,       # Morpho Blue on Base
    'arbitrum': 200000000,  # Morpho Blue on Arbitrum (approximate)
}

# Module-level cache for discovered market IDs and token metadata.
# Key: (morpho_address, chain_id) -> {max_block_scanned, market_ids, token_info}
_MARKET_CACHE: Dict[tuple, Dict] = {}


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


def _discover_market_ids(web3: Web3, morpho_address: str, block: Optional[int] = None) -> Set[bytes]:
    """
    Discover all market IDs by scanning CreateMarket events.

    Uses a module-level cache so that across multiple snapshots (dates),
    we only scan new blocks incrementally rather than re-scanning from deployment.
    """
    import time

    morpho_address = Web3.to_checksum_address(morpho_address)
    chain_id = web3.eth.chain_id
    cache_key = (morpho_address.lower(), chain_id)

    chain_id_map = {1: 'ethereum', 8453: 'base', 42161: 'arbitrum'}
    chain_name = chain_id_map.get(chain_id, 'ethereum')
    deployment_block = DEPLOYMENT_BLOCKS.get(chain_name, 0)
    to_block = block if block is not None else web3.eth.block_number

    # Check cache
    if cache_key in _MARKET_CACHE:
        cached = _MARKET_CACHE[cache_key]
        if cached['max_block'] >= to_block:
            return cached['market_ids']
        # Incremental scan from where we left off
        from_block = cached['max_block'] + 1
        market_ids = set(cached['market_ids'])
    else:
        from_block = deployment_block
        market_ids = set()

    # Scan in chunks
    chunk_size = 50_000
    current = from_block

    while current <= to_block:
        end = min(current + chunk_size - 1, to_block)
        for attempt in range(3):
            try:
                logs = web3.eth.get_logs({
                    'address': morpho_address,
                    'topics': [CREATE_MARKET_TOPIC],
                    'fromBlock': current,
                    'toBlock': end,
                })
                for log in logs:
                    if len(log['topics']) >= 2:
                        market_ids.add(bytes(log['topics'][1]))
                break
            except Exception as e:
                error_str = str(e).lower()
                if attempt < 2 and ('connection' in error_str or 'remote' in error_str
                                    or 'timeout' in error_str or '429' in error_str
                                    or 'too many' in error_str):
                    time.sleep(1 * (attempt + 1))
                    continue
                if chunk_size > 5_000:
                    chunk_size = chunk_size // 2
                    break
                raise
        current = end + 1

    # Update cache
    _MARKET_CACHE[cache_key] = {
        'max_block': to_block,
        'market_ids': market_ids,
        'token_info': _MARKET_CACHE.get(cache_key, {}).get('token_info', {}),
    }

    return market_ids


def get_morpho_tvl(web3: Web3, morpho_address: str, block: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract TVL from Morpho Blue at a given block.

    Args:
        web3: Web3 instance
        morpho_address: Morpho Blue singleton contract address
        block: Block number (None = latest)

    Returns:
        List of dicts, one per market:
        {
            'market_id': bytes32 hex string,
            'loan_token': address,
            'loan_symbol': symbol,
            'loan_decimals': decimals,
            'collateral_token': address,
            'collateral_symbol': symbol,
            'collateral_decimals': decimals,
            'total_supply_assets_raw': uint128,
            'total_borrow_assets_raw': uint128,
            'lltv': loan-to-value ratio,
        }
    """
    morpho_address = Web3.to_checksum_address(morpho_address)
    morpho = web3.eth.contract(address=morpho_address, abi=MORPHO_ABI)

    call_kwargs = {'block_identifier': block} if block is not None else {}

    # Step 1: Discover all market IDs via CreateMarket events
    market_ids = _discover_market_ids(web3, morpho_address, block)
    print(f"Discovered {len(market_ids)} Morpho Blue markets")

    results = []

    # Step 2: Query each market
    for market_id_bytes in market_ids:
        try:
            # Get market params
            params = morpho.functions.idToMarketParams(market_id_bytes).call(**call_kwargs)
            loan_token = Web3.to_checksum_address(params[0])
            collateral_token = Web3.to_checksum_address(params[1])
            lltv = params[4]

            # Get market state
            state = morpho.functions.market(market_id_bytes).call(**call_kwargs)
            total_supply_assets = state[0]
            total_borrow_assets = state[2]

            # Skip empty markets (no supply and no borrows)
            if total_supply_assets == 0 and total_borrow_assets == 0:
                continue

            # Get token metadata (cached across snapshots)
            cache_key = (morpho_address.lower(), web3.eth.chain_id)
            token_cache = _MARKET_CACHE.get(cache_key, {}).get('token_info', {})

            if loan_token in token_cache:
                loan_symbol, loan_decimals = token_cache[loan_token]
            else:
                loan_erc20 = web3.eth.contract(address=loan_token, abi=ERC20_ABI)
                loan_symbol = _safe_call(lambda: loan_erc20.functions.symbol().call(), "UNKNOWN")
                loan_decimals = _safe_call(lambda: loan_erc20.functions.decimals().call(), 18)
                token_cache[loan_token] = (loan_symbol, loan_decimals)

            if collateral_token in token_cache:
                collateral_symbol, collateral_decimals = token_cache[collateral_token]
            else:
                collateral_erc20 = web3.eth.contract(address=collateral_token, abi=ERC20_ABI)
                collateral_symbol = _safe_call(lambda: collateral_erc20.functions.symbol().call(), "UNKNOWN")
                collateral_decimals = _safe_call(lambda: collateral_erc20.functions.decimals().call(), 18)
                token_cache[collateral_token] = (collateral_symbol, collateral_decimals)

            # Persist token cache
            if cache_key in _MARKET_CACHE:
                _MARKET_CACHE[cache_key]['token_info'] = token_cache

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
            print(f"Warning: Failed to process Morpho market {market_id_hex}: {e}")
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

    # Morpho Blue singleton on Ethereum
    morpho = '0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb'

    print("Testing Morpho Blue TVL extraction...")
    print(f"Latest block: {w3.eth.block_number:,}")

    results = get_morpho_tvl(w3, morpho)

    print(f"\nFound {len(results)} active markets")
    if results:
        print("\nFirst market:")
        first = results[0]
        print(f"  Market ID: {first['market_id'][:18]}...")
        print(f"  Loan: {first['loan_symbol']}")
        print(f"  Collateral: {first['collateral_symbol']}")
        print(f"  Supply: {first['total_supply_assets_raw'] / 10**first['loan_decimals']:.2f}")
        print(f"  Borrow: {first['total_borrow_assets_raw'] / 10**first['loan_decimals']:.2f}")
