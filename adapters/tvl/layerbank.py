"""
LayerBank TVL Adapter

LayerBank is a Compound V2-style fork with key ABI differences:
- Market discovery: allMarkets() returns address[] (NOT getAllMarkets())
- Borrow function: totalBorrow() singular (NOT totalBorrows())
- No totalReserves() function
- underlying() returns 0x0 for native ETH markets
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# LayerBank Core/Controller ABI — uses allMarkets() not getAllMarkets()
CONTROLLER_ABI = [
    {
        "inputs": [],
        "name": "allMarkets",
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# LayerBank lToken ABI — uses totalBorrow() not totalBorrows()
LTOKEN_ABI = [
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
        "name": "totalBorrow",
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
    """Safely call a contract function with retries."""
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


def get_layerbank_tvl(
    web3: Web3,
    controller_address: str,
    block: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Extract TVL from LayerBank controller at a given block.

    Args:
        web3: Web3 instance
        controller_address: LayerBank Core/Controller contract address
        block: Block number (None = latest)

    Returns:
        List of dicts with same schema as compound_v2_style adapter.
    """
    controller_address = Web3.to_checksum_address(controller_address)
    controller = web3.eth.contract(address=controller_address, abi=CONTROLLER_ABI)

    call_kwargs = {'block_identifier': block} if block is not None else {}

    # Get all markets via allMarkets() — LayerBank's variant
    import time
    market_addresses = None
    for attempt in range(3):
        try:
            market_addresses = controller.functions.allMarkets().call(**call_kwargs)
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
        ltoken = web3.eth.contract(address=market_addr, abi=LTOKEN_ABI)

        try:
            market_symbol = _safe_call(lambda: ltoken.functions.symbol().call(**call_kwargs), "UNKNOWN")
            market_decimals = _safe_call(lambda: ltoken.functions.decimals().call(**call_kwargs), 18)

            # Get underlying asset — returns 0x0 for native ETH markets
            underlying_addr = _safe_call(lambda: ltoken.functions.underlying().call(**call_kwargs), None)
            underlying_symbol = None
            underlying_decimals = None

            if underlying_addr and underlying_addr != '0x0000000000000000000000000000000000000000':
                underlying_addr = Web3.to_checksum_address(underlying_addr)
                underlying = web3.eth.contract(address=underlying_addr, abi=ERC20_ABI)
                underlying_symbol = _safe_call(lambda: underlying.functions.symbol().call(**call_kwargs), "UNKNOWN")
                underlying_decimals = _safe_call(lambda: underlying.functions.decimals().call(**call_kwargs), 18)
            else:
                underlying_addr = None
                underlying_symbol = "NATIVE"
                underlying_decimals = 18

            # Get TVL — LayerBank uses totalBorrow() (singular)
            get_cash = _safe_call(lambda: ltoken.functions.getCash().call(**call_kwargs), 0)
            total_borrows = _safe_call(lambda: ltoken.functions.totalBorrow().call(**call_kwargs), 0)
            total_supply = _safe_call(lambda: ltoken.functions.totalSupply().call(**call_kwargs), 0)

            # TVL = cash + borrows (no reserves function on LayerBank)
            tvl_underlying = get_cash + total_borrows

            results.append({
                'market_token': market_addr,
                'market_symbol': market_symbol,
                'market_decimals': market_decimals,
                'underlying': underlying_addr,
                'underlying_symbol': underlying_symbol,
                'underlying_decimals': underlying_decimals,
                'get_cash_raw': get_cash,
                'total_borrows_raw': total_borrows,
                'total_reserves_raw': 0,
                'total_supply_raw': total_supply,
                'tvl_underlying_raw': tvl_underlying,
            })

        except Exception as e:
            print(f"Warning: Failed to process lToken {market_addr}: {e}")
            continue

    return results


if __name__ == '__main__':
    from web3 import Web3
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    rpc = 'https://rpc.scroll.io'
    w3 = Web3(Web3.HTTPProvider(rpc))

    controller = '0xEC53c830f4444a8A56455c6836b5D2aA794289Aa'

    print("Testing LayerBank TVL extraction on Scroll...")
    results = get_layerbank_tvl(w3, controller)

    print(f"Found {len(results)} markets")
    for r in results:
        sym = r['market_symbol']
        dec = r['underlying_decimals']
        cash = r['get_cash_raw'] / 10**dec
        borrows = r['total_borrows_raw'] / 10**dec
        supply = r['tvl_underlying_raw'] / 10**dec
        u_sym = r['underlying_symbol']
        print(f"  {sym} ({u_sym}): supply={supply:.4f} cash={cash:.4f} borrows={borrows:.4f}")
