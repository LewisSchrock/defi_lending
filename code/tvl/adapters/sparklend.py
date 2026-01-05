from typing import Any, Dict, List, Optional

from web3 import Web3

# Minimal ABIs needed to query SparkLend (Aave v3-style) TVL via the PoolAddressesProvider
# These are intentionally small: only the functions we call are included.

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

POOL_DATA_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getAllReservesTokens",
        "outputs": [
            {
                "components": [
                    {"internalType": "string", "name": "symbol", "type": "string"},
                    {"internalType": "address", "name": "tokenAddress", "type": "address"},
                ],
                "internalType": "struct IPoolDataProvider.TokenData[]",
                "name": "",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
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
    },
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]


def _to_checksum(web3: Web3, addr: str) -> str:
    """Helper to safely checksum addresses, tolerating empty/zero."""
    if not addr:
        return addr
    return web3.to_checksum_address(addr)


def resolve_sparklend_pool_and_data_provider(
    web3: Web3,
    registry: str,
    block: Optional[int] = None,
) -> Dict[str, str]:
    """
    Given the SparkLend PoolAddressesProvider (registry), resolve:
      - pool: IPool implementation
      - data_provider: IPoolDataProvider implementation
    """

    provider = web3.eth.contract(
        address=_to_checksum(web3, registry),
        abi=ADDRESSES_PROVIDER_ABI,
    )

    call_args: Dict[str, Any] = {}
    if block is not None:
        call_args["block_identifier"] = block

    pool_addr = provider.functions.getPool().call(**call_args)
    data_provider_addr = provider.functions.getPoolDataProvider().call(**call_args)

    return {
        "pool": _to_checksum(web3, pool_addr),
        "data_provider": _to_checksum(web3, data_provider_addr),
    }


def get_sparklend_markets(
    web3: Web3,
    registry: str,
    block: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Discover all SparkLend markets (reserves) on Ethereum via the PoolDataProvider.

    Returns a list of dicts, each containing:
      - underlying: underlying asset address
      - symbol: underlying symbol (best-effort)
      - decimals: underlying decimals (int)
      - a_token: aToken address
    """
    resolved = resolve_sparklend_pool_and_data_provider(web3, registry, block)
    data_provider = web3.eth.contract(
        address=resolved["data_provider"],
        abi=POOL_DATA_PROVIDER_ABI,
    )

    call_args: Dict[str, Any] = {}
    if block is not None:
        call_args["block_identifier"] = block

    reserves = data_provider.functions.getAllReservesTokens().call(**call_args)

    markets: List[Dict[str, Any]] = []
    for token_data in reserves:
        # token_data is (symbol, tokenAddress)
        symbol, underlying = token_data
        underlying_cs = _to_checksum(web3, underlying)

        # Get aToken address from data provider
        a_token, _, _ = data_provider.functions.getReserveTokensAddresses(underlying_cs).call(
            **call_args
        )

        # Pull ERC20 metadata for underlying
        token_contract = web3.eth.contract(address=underlying_cs, abi=ERC20_ABI)
        try:
            decimals = token_contract.functions.decimals().call(**call_args)
        except Exception:
            decimals = 18  # sensible default

        # Best-effort confirm/override symbol from token if needed
        try:
            token_symbol = token_contract.functions.symbol().call(**call_args)
            if token_symbol:
                symbol = token_symbol
        except Exception:
            pass

        markets.append(
            {
                "underlying": underlying_cs,
                "symbol": symbol,
                "decimals": int(decimals),
                "a_token": _to_checksum(web3, a_token),
            }
        )

    return markets


def get_sparklend_tvl_raw(
    web3: Web3,
    registry: str,
    block: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Compute raw SparkLend TVL by reading aToken totalSupply for each market.

    Returns a list of dicts:
      - underlying: underlying asset address
      - symbol: underlying symbol
      - decimals: underlying decimals
      - a_token: aToken address
      - a_token_total_supply: int (raw base units)
    """
    markets = get_sparklend_markets(web3, registry, block)

    call_args: Dict[str, Any] = {}
    if block is not None:
        call_args["block_identifier"] = block

    results: List[Dict[str, Any]] = []
    for m in markets:
        a_token_contract = web3.eth.contract(address=m["a_token"], abi=ERC20_ABI)
        total_supply = a_token_contract.functions.totalSupply().call(**call_args)

        item = dict(m)
        item["a_token_total_supply"] = int(total_supply)
        results.append(item)

    return results
