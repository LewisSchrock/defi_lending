from web3 import Web3

# Minimal ERC20 ABI
ERC20_ABI_MIN = [
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
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    },
]

# ContractsRegister v3 – we only need pools list
CONTRACTS_REGISTER_ABI_MIN = [
    {
        "inputs": [],
        "name": "getPoolsCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "i", "type": "uint256"}],
        "name": "pools",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Pool ABI – minimal: liquidity, debt, underlying
POOL_ABI_MIN = [
    {
        "inputs": [],
        "name": "expectedLiquidity",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalBorrowed",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "underlyingToken",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class GearboxTVLAdapter:
    def __init__(self, web3, chain, config, outputs_dir):
        self.web3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir

        register_addr = Web3.to_checksum_address(config["contracts_register"])
        self.register = self.web3.eth.contract(
            address=register_addr, abi=CONTRACTS_REGISTER_ABI_MIN
        )

        self._token_meta = {}

    #
    # Helpers
    #
    def _get_token_meta(self, token_addr: str) -> dict:
        token_addr = Web3.to_checksum_address(token_addr)
        if token_addr in self._token_meta:
            return self._token_meta[token_addr]

        c = self.web3.eth.contract(address=token_addr, abi=ERC20_ABI_MIN)

        try:
            symbol = c.functions.symbol().call()
        except Exception:
            symbol = None

        try:
            decimals = c.functions.decimals().call()
        except Exception:
            decimals = 18  # fallback
        meta = {"symbol": symbol, "decimals": int(decimals)}
        self._token_meta[token_addr] = meta
        return meta

    def _safe_call(self, fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    #
    # Core: discover pools via ContractsRegister
    #
    def get_pools(self):
        pools = []
        count = self._safe_call(self.register.functions.getPoolsCount().call, 0)
        if not count:
            print("No pools discovered from ContractsRegister.")
            return pools

        for i in range(int(count)):
            pool_addr = self._safe_call(self.register.functions.pools(i).call)
            if not pool_addr or int(pool_addr, 16) == 0:
                continue
            pools.append(Web3.to_checksum_address(pool_addr))

        print(f"Discovered {len(pools)} Gearbox pools")
        return pools

    #
    # TVL / balances
    #
    def get_tvl_raw(self, block_number: int):
        """
        Return one row per pool: supplied/borrowed in underlying units.
        You can aggregate per-asset in the aggregator if you want.
        """
        rows = []
        pools = self.get_pools()

        for pool_addr in pools:
            pool = self.web3.eth.contract(address=pool_addr, abi=POOL_ABI_MIN)

            # We don't bother with `block_identifier` yet; you can add it later if needed
            expected_liquidity = self._safe_call(pool.functions.expectedLiquidity().call, 0)
            total_borrowed = self._safe_call(pool.functions.totalBorrowed().call, 0)
            underlying_token = self._safe_call(pool.functions.underlyingToken().call)

            if not underlying_token:
                continue

            meta = self._get_token_meta(underlying_token)
            decimals = meta["decimals"]
            factor = 10 ** decimals

            supplied = expected_liquidity / factor if factor else None
            borrowed = total_borrowed / factor if factor else None

            row = {
                "protocol": "gearbox",
                "version": "v3",
                "chain": self.chain,
                "block": block_number,
                "pool": pool_addr,
                "underlying_token": underlying_token,
                "underlying_symbol": meta["symbol"],
                "underlying_decimals": decimals,
                "supplied_raw": int(expected_liquidity),
                "supplied": supplied,
                "borrowed_raw": int(total_borrowed),
                "borrowed": borrowed,
            }
            rows.append(row)

        return rows