from web3 import Web3

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

LENDER_ABI_MIN = [
    {
        "anonymous": False,
        "inputs": [
            # Only owner is indexed in the actual logs
            {
                "indexed": True,
                "internalType": "address",
                "name": "owner",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "yieldToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "underlyingToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "shares",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "credit",
                "type": "uint256",
            },
        ],
        "name": "Liquidate",
        "type": "event",
    },
]

LIQUIDATE_TOPIC0 = (
    "0x8246cc71ab01533b5bebc672a636df812f10637ad720797319d5741d5ebb3962"
)


class CapLiquidationAdapter:
    def __init__(self, web3, chain, config, outputs_dir):
        self.web3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir

        lender_addr = Web3.to_checksum_address(
            config.get("lender", "0x15622c3dbbc5614E6DFa9446603c1779647f01FC")
        )
        self.lender = self.web3.eth.contract(address=lender_addr, abi=LENDER_ABI_MIN)
        self._token_meta = {}

    def _get_token_meta(self, token_addr: str) -> dict:
        token_addr = Web3.to_checksum_address(token_addr)
        if token_addr in self._token_meta:
            return self._token_meta[token_addr]

        contract = self.web3.eth.contract(address=token_addr, abi=ERC20_ABI_MIN)

        try:
            symbol = contract.functions.symbol().call()
        except Exception:
            symbol = None

        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            decimals = int(self.config.get("underlying_decimals", 6))

        meta = {"symbol": symbol, "decimals": int(decimals)}
        self._token_meta[token_addr] = meta
        return meta

    def resolve_market(self) -> dict:
        """
        For now we just surface the lender + underlying asset from config.
        You've already wired this up for TVL, so we piggyback on it.
        """
        return {
            "lender": self.lender.address,
            "underlying_symbol": self.config.get("underlying_symbol", "USDC"),
            "underlying_name": self.config.get("underlying_name", "USD Coin"),
            "underlying_decimals": int(self.config.get("underlying_decimals", 6)),
        }

    def fetch_events(self, market: dict, from_block: int, to_block: int):
        """
        Thin wrapper around eth_getLogs. No filtering beyond topic0 + lender address.
        """
        try:
            logs = self.web3.eth.get_logs(
                {
                    "fromBlock": from_block,
                    "toBlock": to_block,
                    "address": market["lender"],
                    "topics": [LIQUIDATE_TOPIC0],
                }
            )
        except Exception as e:
            print(f"  get_logs error in [{from_block}, {to_block}]: {e}")
            return []

        if logs:
            print(
                f"  Found {len(logs)} Liquidate logs in "
                f"[{from_block}, {to_block}]"
            )
        return logs

    def normalize(self, log) -> dict:
        """
        Decode a single Liquidate log into a normalized dict.

        We *do not* rely on the ABI here because the indexed flags on-chain
        clearly don't match what Etherscan shows. Instead we decode manually:

        event Liquidate(
            address owner,
            address yieldToken,
            address underlyingToken,
            uint256 shares,
            uint256 credit
        )

        - topics[0] = keccak("Liquidate(address,address,address,uint256,uint256)")
        - topics[1] = indexed owner
        - topics[2] = indexed yieldToken
        - data      = underlyingToken | shares | credit
        """
        topics = log["topics"]
        if len(topics) < 3:
            raise ValueError(f"Unexpected topics length: {len(topics)}")

        # owner is the first indexed arg
        owner = Web3.to_checksum_address("0x" + topics[1].hex()[-40:])
        # yield_token is the second indexed arg
        yield_token = Web3.to_checksum_address("0x" + topics[2].hex()[-40:])

        # Decode data into 3 x 32-byte words
        raw_data = log["data"]
        if isinstance(raw_data, (bytes, bytearray)):
            data_bytes = bytes(raw_data)
        else:
            data_bytes = Web3.to_bytes(hexstr=raw_data)
        if len(data_bytes) < 32 * 3:
            raise ValueError(f"Unexpected data length: {len(data_bytes)}")

        def word(i: int) -> int:
            start = 32 * i
            end = start + 32
            return int.from_bytes(data_bytes[start:end], byteorder="big")

        def addr_from_word(x: int) -> str:
            # last 20 bytes of the 32-byte word
            return Web3.to_checksum_address("0x" + x.to_bytes(32, "big").hex()[-40:])

        underlying_token = addr_from_word(word(0))
        shares = word(1)
        credit = word(2)

        bn = log["blockNumber"]
        try:
            block = self.web3.eth.get_block(bn)
            ts = block["timestamp"]
        except Exception:
            ts = None

        meta = self._get_token_meta(underlying_token)
        decimals = meta.get("decimals", int(self.config.get("underlying_decimals", 6)))
        credit_norm = credit / (10 ** decimals)

        row = {
            "protocol": "cap",
            "version": "v1",
            "chain": self.chain,
            "event_name": "Liquidate",
            "lender": self.lender.address,
            "block_number": bn,
            "block_timestamp": ts,
            "tx_hash": log["transactionHash"].hex(),
            "log_index": log["logIndex"],
            "owner": owner,
            "yield_token": yield_token,
            "underlying_token": underlying_token,
            "underlying_symbol": meta.get("symbol"),
            "underlying_decimals": decimals,
            "shares": shares,
            "credit_raw": credit,
            "credit": credit_norm,
        }
        return row

    def get_liquidations_raw(
        self,
        market: dict,
        from_block: int,
        to_block: int,
        window: int = 500,
    ):
        """
        Scan in block windows and return *all* decoded Liquidate events.
        No extra filtering, so rows should match the logs you see in the scan.
        """
        rows = []
        current_from = from_block

        while current_from <= to_block:
            current_to = min(current_from + window - 1, to_block)

            logs = self.fetch_events(market, current_from, current_to)

            for log in logs:
                try:
                    row = self.normalize(log)
                except Exception as e:
                    print("    normalize() failed for a log:", e)
                    continue
                rows.append(row)

            current_from = current_to + 1

        return rows