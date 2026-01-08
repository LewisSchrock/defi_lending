from enum import IntEnum
from web3 import Web3

# ---------- Shared ERC20 + constants ----------

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


class CollateralCalcTask(IntEnum):
    # Assumed enum order from Gearbox source:
    # enum CollateralCalcTask {
    #     GENERIC_PARAMS,
    #     DEBT_ONLY,
    #     DEBT_COLLATERAL,
    #     DEBT_COLLATERAL_SAFE_PRICES,
    #     FULL_COLLATERAL_CHECK_LAZY
    # }
    GENERIC_PARAMS = 0
    DEBT_ONLY = 1
    DEBT_COLLATERAL = 2
    DEBT_COLLATERAL_SAFE_PRICES = 3


# topic0 for Gearbox V3 facade liquidation event:
# event LiquidateCreditAccount(
#     address indexed creditAccount,
#     address indexed liquidator,
#     address to,
#     uint256 remainingFunds
# );
LIQUIDATE_TOPIC0 = "0x" + Web3.keccak(
    text="LiquidateCreditAccount(address,address,address,uint256)"
).hex()

USD_1E8 = 10**8

# ---------- Minimal ABIs for Gearbox infra ----------

ADDRESS_PROVIDER_ABI_MIN = [
    {
        "name": "getContractsRegister",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

CONTRACTS_REGISTER_ABI_MIN = [
    {
        "name": "getCreditManagers",
        "inputs": [],
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

CREDIT_MANAGER_ABI_MIN = [
    {
        "name": "calcDebtAndCollateral",
        "inputs": [
            {"name": "creditAccount", "type": "address"},
            {"name": "task", "type": "uint8"},
        ],
        "outputs": [
            {
                "components": [
                    {"name": "debt", "type": "uint256"},
                    {"name": "cumulativeIndexNow", "type": "uint256"},
                    {"name": "cumulativeIndexLastUpdate", "type": "uint256"},
                    {"name": "cumulativeQuotaInterest", "type": "uint128"},
                    {"name": "accruedInterest", "type": "uint256"},
                    {"name": "accruedFees", "type": "uint256"},
                    {"name": "totalDebtUSD", "type": "uint256"},
                    {"name": "totalValue", "type": "uint256"},
                    {"name": "totalValueUSD", "type": "uint256"},
                    {"name": "twvUSD", "type": "uint256"},
                    {"name": "enabledTokensMask", "type": "uint256"},
                    {"name": "quotedTokensMask", "type": "uint256"},
                    {"name": "quotedTokens", "type": "address[]"},
                    {"name": "_poolQuotaKeeper", "type": "address"},
                ],
                "name": "cdd",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "underlying",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

CREDIT_FACADE_ABI_MIN = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "creditAccount",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "liquidator",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "to",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "remainingFunds",
                "type": "uint256",
            },
        ],
        "name": "LiquidateCreditAccount",
        "type": "event",
    },
    {
        "name": "creditManager",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class GearboxLiquidationAdapter:
    """
    Discovers all Gearbox Credit Facades via ContractsRegister,
    scans for LiquidateCreditAccount events, and enriches each
    with debt/collateral data from CreditManager.calcDebtAndCollateral.
    """

    def __init__(self, web3, chain, config, outputs_dir):
        self.web3 = web3
        self.chain = chain
        self.config = config
        self.outputs_dir = outputs_dir

        # ContractsRegister: prefer explicit config, else go via AddressProvider
        cr_addr = config.get("contracts_register")
        if cr_addr:
            cr_addr = Web3.to_checksum_address(cr_addr)
        else:
            ap_addr = Web3.to_checksum_address(config["address_provider"])
            address_provider = self.web3.eth.contract(
                address=ap_addr, abi=ADDRESS_PROVIDER_ABI_MIN
            )
            cr_addr = address_provider.functions.getContractsRegister().call()

        self.contracts_register = self.web3.eth.contract(
            address=cr_addr, abi=CONTRACTS_REGISTER_ABI_MIN
        )

        # Caches
        self._facades = None  # list of checksum addresses
        self._cm_for_facade = {}  # facade -> creditManager
        self._underlying_for_cm = {}  # creditManager -> underlying token
        self._token_meta = {}  # token -> {symbol, decimals}
        self._cm_contracts = {}  # creditManager -> contract instance

    # ---------- helpers ----------

    def get_credit_facades(self) -> list[str]:
        """
        Discover all CreditFacade addresses for this Gearbox deployment.

        Uses the existing _get_credit_managers() helper and a minimal
        CreditManager ABI with only the creditFacade() view. Returns a
        deduplicated list of checksum addresses.
        """
        # Reuse the discovery logic you already have
        credit_managers = self._get_credit_managers()

        # Minimal ABI just for creditFacade()
        CREDIT_MANAGER_ABI_MIN = [
            {
                "inputs": [],
                "name": "creditFacade",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "",
                        "type": "address",
                    },
                ],
                "stateMutability": "view",
                "type": "function",
            }
        ]

        facades: set[str] = set()
        for cm_addr in credit_managers:
            cm_address = Web3.to_checksum_address(cm_addr)
            cm = self.web3.eth.contract(
                address=cm_address,
                abi=CREDIT_MANAGER_ABI_MIN,
            )

            try:
                facade = cm.functions.creditFacade().call()
            except Exception:
                # Skip managers that don't expose creditFacade()
                continue

            # Skip zero address
            try:
                if int(facade, 16) == 0:
                    continue
            except Exception:
                # Malformed result; ignore
                continue

            facades.add(Web3.to_checksum_address(facade))

        return sorted(facades)

    def _get_credit_managers(self):
        try:
            cms = self.contracts_register.functions.getCreditManagers().call()
        except Exception as e:
            print("getCreditManagers() failed:", e)
            return []
        return [Web3.to_checksum_address(a) for a in cms]

    def _get_or_make_cm(self, cm_addr):
        cm_addr = Web3.to_checksum_address(cm_addr)
        if cm_addr in self._cm_contracts:
            return self._cm_contracts[cm_addr]
        cm = self.web3.eth.contract(address=cm_addr, abi=CREDIT_MANAGER_ABI_MIN)
        self._cm_contracts[cm_addr] = cm
        return cm

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
            decimals = 18

        meta = {"symbol": symbol, "decimals": int(decimals)}
        self._token_meta[token_addr] = meta
        return meta

    def _discover_facades(self):
        """
        Populate self._facades and self._cm_for_facade (facade -> creditManager).
        """
        if self._facades is not None:
            return self._facades

        cms = self._get_credit_managers()
        facades = set()

        for cm_addr in cms:
            cm = self._get_or_make_cm(cm_addr)
            try:
                # All v3 CMs expose this
                facade_addr = cm.functions.creditFacade().call()
            except Exception:
                continue

            facade_addr = Web3.to_checksum_address(facade_addr)
            facades.add(facade_addr)
            self._cm_for_facade[facade_addr] = cm_addr

        self._facades = sorted(facades)
        print(f"Discovered {len(self._facades)} Gearbox credit facades.")
        return self._facades

    # ---------- public API for sandbox/pipeline ----------

    def fetch_events(self, facade, from_block: int, to_block: int):
        """Fetch all LiquidateCreditAccount logs from the given facade (if provided),
        or from all discovered facades if facade is None, in [from_block, to_block]."""
        if facade is None:
            facades = self._discover_facades()
        else:
            facades = [Web3.to_checksum_address(facade)]
        all_logs = []
        for fac in facades:
            try:
                logs = self.web3.eth.get_logs({
                    "fromBlock": from_block,
                    "toBlock": to_block,
                    "address": fac,
                    "topics": [LIQUIDATE_TOPIC0],
                })
            except Exception as e:
                print(f"  get_logs error for facade {fac} in [{from_block},{to_block}]: {e}")
                continue
            if logs:
                print(
                    f"  Found {len(logs)} LiquidateCreditAccount logs for facade "
                    f"{fac} in [{from_block}, {to_block}]"
                )
                all_logs.extend(logs)
        return all_logs

    def normalize(self, log) -> dict:
        """
        Decode one LiquidateCreditAccount log and enrich with CM debt/collateral.
        """
        facade_addr = Web3.to_checksum_address(log["address"])
        cm_addr = self._cm_for_facade.get(facade_addr)
        if cm_addr is None:
            # Fallback: ask facade directly if mapping missing for some reason
            facade_contract = self.web3.eth.contract(
                address=facade_addr, abi=CREDIT_FACADE_ABI_MIN
            )
            cm_addr = facade_contract.functions.creditManager().call()
            cm_addr = Web3.to_checksum_address(cm_addr)
            self._cm_for_facade[facade_addr] = cm_addr

        # Decode event via facade ABI
        facade_contract = self.web3.eth.contract(
            address=facade_addr, abi=CREDIT_FACADE_ABI_MIN
        )
        evt = facade_contract.events.LiquidateCreditAccount().process_log(log)
        args = evt["args"]

        credit_account = Web3.to_checksum_address(args["creditAccount"])
        liquidator = Web3.to_checksum_address(args["liquidator"])
        to_addr = Web3.to_checksum_address(args["to"])
        remaining_funds = int(args["remainingFunds"])

        bn = log["blockNumber"]
        try:
            block = self.web3.eth.get_block(bn)
            ts = block["timestamp"]
        except Exception:
            ts = None

        # Enrich with CreditManager debt/collateral at this block
        cm = self._get_or_make_cm(cm_addr)
        try:
            cdd = cm.functions.calcDebtAndCollateral(
                credit_account,
                int(CollateralCalcTask.DEBT_COLLATERAL),
            ).call(block_identifier=bn)
        except Exception as e:
            print(f"    calcDebtAndCollateral() failed for {credit_account} @ {bn}: {e}")
            cdd = None

        if cdd is not None:
            debt_raw = int(cdd[0])
            total_debt_usd_raw = int(cdd[6])
            total_value_usd_raw = int(cdd[8])
            twv_usd_raw = int(cdd[9])
        else:
            debt_raw = total_debt_usd_raw = total_value_usd_raw = twv_usd_raw = None

        # Underlying token + metadata
        if cm_addr in self._underlying_for_cm:
            underlying = self._underlying_for_cm[cm_addr]
        else:
            try:
                underlying = cm.functions.underlying().call()
                underlying = Web3.to_checksum_address(underlying)
            except Exception:
                underlying = None
            self._underlying_for_cm[cm_addr] = underlying

        if underlying is not None:
            meta = self._get_token_meta(underlying)
            decimals = meta["decimals"]
            symbol = meta["symbol"]
        else:
            meta = {}
            decimals = 18
            symbol = None

        remaining_funds_norm = (
            remaining_funds / (10 ** decimals) if remaining_funds and decimals is not None else None
        )
        total_debt_usd_norm = (
            total_debt_usd_raw / USD_1E8 if total_debt_usd_raw is not None else None
        )

        row = {
            "protocol": "gearbox",
            "version": "v3",
            "chain": self.chain,
            "event_name": "LiquidateCreditAccount",
            "facade": facade_addr,
            "credit_manager": cm_addr,
            "credit_account": credit_account,
            "liquidator": liquidator,
            "to": to_addr,
            "underlying_token": underlying,
            "underlying_symbol": symbol,
            "underlying_decimals": decimals,
            "remaining_funds_raw": remaining_funds,
            "remaining_funds": remaining_funds_norm,
            "debt_raw": debt_raw,
            "total_debt_usd_raw": total_debt_usd_raw,
            "total_debt_usd": total_debt_usd_norm,
            "total_value_usd_raw": total_value_usd_raw,
            "twv_usd_raw": twv_usd_raw,
            "block_number": bn,
            "block_timestamp": ts,
            "tx_hash": log["transactionHash"].hex(),
            "log_index": log["logIndex"],
        }
        return row

    def get_liquidations_raw(
        self,
        from_block: int,
        to_block: int,
        window: int = 500,
    ):
        """
        Scan in block windows and return all decoded Gearbox liquidations.
        """
        rows = []
        current_from = from_block

        while current_from <= to_block:
            current_to = min(current_from + window - 1, to_block)
            logs = self.fetch_events(None, current_from, current_to)

            for log in logs:
                try:
                    row = self.normalize(log)
                except Exception as e:
                    print("    normalize() failed for a log:", e)
                    continue
                rows.append(row)

            current_from = current_to + 1

        return rows