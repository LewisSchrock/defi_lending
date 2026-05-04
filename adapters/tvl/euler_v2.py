"""
Euler V2 TVL Adapter

Architecture:
- GenericFactory: Deploys EVault proxies, tracks all deployed vaults
  - getProxyListLength() -> total number of deployed vaults
  - getProxyListSlice(start, end) -> batch fetch vault addresses
- EVault: ERC4626-style vault with additional debt tracking
  - asset() -> underlying token address
  - totalAssets() -> total supplied (underlying units)
  - totalBorrows() -> total borrowed (underlying units)
  - symbol() -> vault token symbol (e.g., "eUSDT-1")
  - decimals() -> vault token decimals

TVL Extraction:
1. Discover all EVault addresses from GenericFactory
2. For each vault, query asset(), totalAssets(), totalBorrows()
3. Get token metadata (symbol, decimals) from underlying
4. Return raw amounts

Factory addresses:
- Ethereum: 0x29a56a1b8214D9Cf7c5561811750D5cBDb45CC8e
- Base:     0x7F321498A801A191a93C840750ed637149dDf8D0
- Arbitrum: 0x78Df1CF5bf06a7f27f2ACc580B934238C1b80D50
- Sonic:    0xF075cC8660B51D0b8a4474e3f47eDAC5fA034cFB
"""

from typing import Dict, List, Any, Optional
from web3 import Web3

# GenericFactory ABI
FACTORY_ABI = [
    {
        "inputs": [],
        "name": "getProxyListLength",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "start", "type": "uint256"},
            {"internalType": "uint256", "name": "end", "type": "uint256"},
        ],
        "name": "getProxyListSlice",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# EVault ABI (ERC4626 + debt tracking)
EVAULT_ABI = [
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
        "name": "totalBorrows",
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

# ERC20 ABI for underlying token metadata
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


def _discover_vaults(web3: Web3, factory_address: str, block: Optional[int] = None) -> List[str]:
    """
    Discover all EVault addresses from the GenericFactory.

    Args:
        web3: Web3 instance
        factory_address: GenericFactory contract address
        block: Block number (None = latest)

    Returns:
        List of EVault addresses
    """
    import time

    factory_address = Web3.to_checksum_address(factory_address)
    factory = web3.eth.contract(address=factory_address, abi=FACTORY_ABI)

    call_kwargs = {'block_identifier': block} if block is not None else {}

    # Get total number of vaults
    total = None
    for attempt in range(3):
        try:
            total = factory.functions.getProxyListLength().call(**call_kwargs)
            break
        except Exception as e:
            error_str = str(e).lower()
            if attempt < 2 and ('connection' in error_str or 'remote' in error_str or 'timeout' in error_str):
                time.sleep(1 * (attempt + 1))
                continue
            raise

    if total is None or total == 0:
        return []

    print(f"Euler V2 factory: {total} vaults deployed")

    # Fetch in batches
    vaults = []
    batch_size = 100
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        for attempt in range(3):
            try:
                batch = factory.functions.getProxyListSlice(start, end).call(**call_kwargs)
                vaults.extend([Web3.to_checksum_address(v) for v in batch])
                break
            except Exception as e:
                error_str = str(e).lower()
                if attempt < 2 and ('connection' in error_str or 'remote' in error_str or 'timeout' in error_str):
                    time.sleep(1 * (attempt + 1))
                    continue
                print(f"Warning: Failed to fetch vault batch {start}-{end}: {e}")
                break

    return vaults


def get_euler_v2_tvl(web3: Web3, factory_address: str, block: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Extract TVL from Euler V2 at a given block.

    Args:
        web3: Web3 instance
        factory_address: GenericFactory contract address
        block: Block number (None = latest)

    Returns:
        List of dicts, one per active vault:
        {
            'vault': EVault address,
            'vault_symbol': vault token symbol,
            'vault_decimals': vault token decimals,
            'underlying': underlying asset address,
            'underlying_symbol': symbol,
            'underlying_decimals': decimals,
            'total_assets_raw': total supplied in underlying,
            'total_borrows_raw': total borrowed in underlying,
            'vault_supply_raw': vault token totalSupply,
        }
    """
    # Step 1: Discover all vaults from factory
    vault_addresses = _discover_vaults(web3, factory_address, block)

    if not vault_addresses:
        print("No Euler V2 vaults found")
        return []

    call_kwargs = {'block_identifier': block} if block is not None else {}

    results = []
    skipped = 0

    # Step 2: Query each vault
    for vault_addr in vault_addresses:
        vault = web3.eth.contract(address=vault_addr, abi=EVAULT_ABI)

        try:
            # Get vault metadata
            vault_symbol = _safe_call(lambda: vault.functions.symbol().call(**call_kwargs), None)
            if vault_symbol is None:
                # Not a valid EVault (factory may contain non-vault proxies)
                skipped += 1
                continue

            # Get underlying asset
            underlying_addr = _safe_call(lambda: vault.functions.asset().call(**call_kwargs), None)
            if underlying_addr is None:
                skipped += 1
                continue
            underlying_addr = Web3.to_checksum_address(underlying_addr)

            # Get TVL data
            total_assets = _safe_call(lambda: vault.functions.totalAssets().call(**call_kwargs), 0)
            total_borrows = _safe_call(lambda: vault.functions.totalBorrows().call(**call_kwargs), 0)
            vault_supply = _safe_call(lambda: vault.functions.totalSupply().call(**call_kwargs), 0)

            # Skip inactive vaults (no supply or borrows)
            if total_assets == 0 and total_borrows == 0:
                skipped += 1
                continue

            vault_decimals = _safe_call(lambda: vault.functions.decimals().call(**call_kwargs), 18)

            # Get underlying token metadata
            underlying = web3.eth.contract(address=underlying_addr, abi=ERC20_ABI)
            underlying_symbol = _safe_call(lambda: underlying.functions.symbol().call(**call_kwargs), "UNKNOWN")
            underlying_decimals = _safe_call(lambda: underlying.functions.decimals().call(**call_kwargs), 18)

            results.append({
                'vault': vault_addr,
                'vault_symbol': vault_symbol,
                'vault_decimals': vault_decimals,
                'underlying': underlying_addr,
                'underlying_symbol': underlying_symbol,
                'underlying_decimals': underlying_decimals,
                'total_assets_raw': total_assets,
                'total_borrows_raw': total_borrows,
                'vault_supply_raw': vault_supply,
            })

        except Exception as e:
            # Silently skip vaults that fail (many are inactive/deprecated)
            skipped += 1
            continue

    print(f"Euler V2: {len(results)} active vaults, {skipped} skipped")
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

    # Euler V2 factory on Ethereum
    factory = '0x29a56a1b8214D9Cf7c5561811750D5cBDb45CC8e'

    print("Testing Euler V2 TVL extraction...")
    print(f"Latest block: {w3.eth.block_number:,}")

    results = get_euler_v2_tvl(w3, factory)

    print(f"\nFound {len(results)} active vaults")
    if results:
        print("\nTop 5 vaults by total assets:")
        sorted_results = sorted(results, key=lambda x: x['total_assets_raw'], reverse=True)[:5]
        for r in sorted_results:
            assets = r['total_assets_raw'] / 10**r['underlying_decimals']
            borrows = r['total_borrows_raw'] / 10**r['underlying_decimals']
            print(f"  {r['vault_symbol']} ({r['underlying_symbol']}): "
                  f"assets={assets:,.2f}  borrows={borrows:,.2f}")
