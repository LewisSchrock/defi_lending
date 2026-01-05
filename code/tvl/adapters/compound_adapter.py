from web3 import Web3
from ..config import COMPTROLLER_ABI, CTOKEN_ABI, ERC20_ABI

# ABI for Compound's price oracle getUnderlyingPrice function
COMPOUND_ORACLE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "cToken", "type": "address"}],
        "name": "getUnderlyingPrice",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# Mainnet Comptroller (Unitroller proxy) for Compound v2
# If you want to make it generic, you can also pass this via config/yaml
MAINNET_COMPTROLLER = Web3.to_checksum_address(
    "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B"
)

# Canonical cETH address on mainnet
CETH_ADDRESS = Web3.to_checksum_address(
    "0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5"
)


def _checksummed(addr: str | bytes | None) -> str | None:
    """
    Helper to normalize addresses like in aave_adapter._cs().
    """
    if addr is None:
        return None
    a = addr if isinstance(addr, str) else str(addr)
    if a.lower() == "0x0000000000000000000000000000000000000000":
        return a
    return Web3.to_checksum_address(a)


def get_reserves(w3, provider_addr):
    """
    Fetch markets from Compound v2 in the same *style* as Aave's get_reserves.

    Arguments
    ---------
    w3 : Web3
    provider_addr : str
        For Aave this is the PoolAddressesProvider.
        For Compound we treat this as the Comptroller (Unitroller) address.

    Returns
    -------
    list[dict]
        Each dict has keys:
          - symbol:       cToken symbol (e.g., "cUSDC")
          - asset:        the cToken address (used as key for pricing)
          - aToken:       the cToken address (acts like the interest-bearing token)
          - stableDebt:   None (Compound has no separate stable debt token)
          - variableDebt: None (Compound has no separate variable debt token)
    """
    comptroller_addr = Web3.to_checksum_address(provider_addr or MAINNET_COMPTROLLER)
    comptroller = w3.eth.contract(address=comptroller_addr, abi=COMPTROLLER_ABI)

    # getAllMarkets returns the list of cToken addresses
    markets = comptroller.functions.getAllMarkets().call()

    data = []
    for ctoken_addr in markets:
        ctoken_cs = _checksummed(ctoken_addr)
        ctoken = w3.eth.contract(address=ctoken_cs, abi=CTOKEN_ABI)

        # cToken symbol, e.g., "cUSDC"
        try:
            sym = ctoken.functions.symbol().call()
        except Exception:
            sym = "(unknown)"

        # For price queries, Compound oracles take the cToken address.
        # We store that as "asset". To fit your existing TVL pipeline,
        # we also set "aToken" = cToken, analogous to Aave's aToken.
        data.append(
            {
                "symbol": sym,
                "asset": ctoken_cs,
                "aToken": ctoken_cs,
                "stableDebt": None,
                "variableDebt": None,
            }
        )

    return data


def get_oracle_price(w3, oracle, asset):
    """
    Return the USD price of the underlying for a given cToken address (asset),
    as a float, similar to Aave's get_oracle_price.

    Aave:
      price = getAssetPrice(underlying) / 1e8

    Compound:
      underlyingPrice = getUnderlyingPrice(cToken)
        = (usdPrice * 1e36) / 10**underlyingDecimals

      => usdPrice = underlyingPrice * 10**underlyingDecimals / 1e36
    """
    ctoken_addr = Web3.to_checksum_address(asset)
    ctoken = w3.eth.contract(address=ctoken_addr, abi=CTOKEN_ABI)

    # Figure out underlying + decimals
    if ctoken_addr == CETH_ADDRESS:
        underlying_decimals = 18
    else:
        # Most cTokens expose underlying()
        try:
            underlying_addr = ctoken.functions.underlying().call()
            underlying = w3.eth.contract(
                address=Web3.to_checksum_address(underlying_addr),
                abi=ERC20_ABI,
            )
            underlying_decimals = underlying.functions.decimals().call()
        except Exception:
            # Fallback: assume 18 decimals if something weird happens
            underlying_decimals = 18

    raw_price = oracle.functions.getUnderlyingPrice(ctoken_addr).call()

    # Convert to actual USD price
    # usdPrice = raw_price * 10**underlying_decimals / 1e36
    scale_underlying = 10 ** underlying_decimals
    usd_price = (raw_price * scale_underlying) / (10**36)

    return usd_price  # float-like (Python will promote to float automatically if needed)


def get_protocol_metadata():
    return {
        "price_scale": None,  # we already return a float price, not a fixed 1e8 scale
        "description": "Compound V2 lending market",
        "version": "v2",
    }