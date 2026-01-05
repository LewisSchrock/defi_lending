
# https://avax-mainnet.g.alchemy.com/v2/cEHzRdgL5rGydq_YIokK2
# https://base-mainnet.g.alchemy.com/v2/cEHzRdgL5rGydq_YIokK2


# sandbox.py

from pathlib import Path
import yaml
import pprint
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from tvl.adapters.fluid import get_fluid_lending_tvl_raw
from tvl.adapters.capyfi import get_capyfi_tvl_raw
from tvl.adapters.venus import get_venus_core_tvl_raw
from tvl.adapters.euler import EulerV2TVLAdapter
from tvl.adapters.lista import ListaMoolahTVLAdapter
from tvl.adapters.cap import CapTVLAdapter
from tvl.adapters.gearbox import GearboxTVLAdapter
from tvl.adapters.tectonic import (
    discover_markets,
    read_market_state,
    read_underlying_decimals,
    compute_totals_underlying,
)

from tvl.adapters.kinetic import KineticTVLAdapter
from tvl.adapters.tydro import TydroTVLAdapter




from liquid.adapters.fluid import FluidLiquidationAdapter
from liquid.adapters.venus import VenusLiquidationAdapter
from liquid.adapters.euler import EulerV2LiquidationAdapter
from liquid.adapters.lista import ListaLiquidationAdapter
from liquid.adapters.cap import CapLiquidationAdapter
from liquid.adapters.gearbox import GearboxLiquidationAdapter
from liquid.adapters.tectonic import TectonicLiquidationAdapter
from liquid.adapters.kinetic import KineticLiquidationAdapter, ScanParams
from liquid.adapters.tydro import TydroLiquidationAdapter, ScanParams
from liquid.adapters.sumermoney import SumerLiquidationAdapter


def load_csus():
    """
    Load csu_config.yaml and return the 'csus' mapping.
    """
    config_path = Path(__file__).resolve().parent / "config" / "csu_config.yaml"
    with config_path.open("r") as f:
        data = yaml.safe_load(f)
    # Expect top-level 'csus:' block in YAML
    return data["csus"]

def debug_capyfi():

    csus = load_csus()
    csu = csus["capyfi_ethereum"]

    rpc_url = csu["rpc"]
    chain = csu["chain"]

    COMPTROLLER_ABI_MIN = [
    {
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    ]

    CTOKEN_ABI_MIN = [
        {"constant": True, "inputs": [], "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [], "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [], "name": "getCash",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [], "name": "totalBorrows",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"},
        {"constant": True, "inputs": [], "name": "totalReserves",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view", "type": "function"},
    ]


    
    UNITROLLER = "0x0b9af1fd73885aD52680A1aeAa7A3f17AC702afA"
    RPC = rpc_url

    w3 = Web3(Web3.HTTPProvider(RPC))

    comp = w3.eth.contract(
        address=Web3.to_checksum_address(UNITROLLER),
        abi=COMPTROLLER_ABI_MIN,
    )

    print("Calling getAllMarkets on Unitroller...")
    markets = comp.functions.getAllMarkets().call()
    print(f"Number of markets from Unitroller: {len(markets)}")
    if not markets:
        return

    first = Web3.to_checksum_address(markets[0])
    print("First market address:", first)

    c = w3.eth.contract(address=first, abi=CTOKEN_ABI_MIN)
    sym = c.functions.symbol().call()
    dec = c.functions.decimals().call()
    cash = c.functions.getCash().call()
    borrows = c.functions.totalBorrows().call()
    reserves = c.functions.totalReserves().call()

    print("symbol:", sym)
    print("decimals:", dec)
    print("getCash:", cash)
    print("totalBorrows:", borrows)
    print("totalReserves:", reserves)
    print("tvl_underlying ~= getCash + totalBorrows - totalReserves:",
          cash + borrows - reserves)

def test_fluid_liq():
    csus = load_csus()
    csu = csus["fluid_lending_ethereum"]

    rpc_url = csu["rpc"]
    chain = csu["chain"]
    outputs_dir = csu["outputs_dir"]

    # liq_reg should be the FluidLiquidation contract (per deployments.md)
    liq_registry = csu["liq_reg"]

    # Build web3 + adapter config (adapter expects registry in config)
    cfg = dict(csu)
    cfg["registry"] = liq_registry

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    adapter = FluidLiquidationAdapter(
        web3=w3,
        chain=chain,
        config=cfg,
        outputs_dir=outputs_dir,
    )

    market = adapter.resolve_market()

    # Small test window; tweak as needed or add to YAML as test_from_block/test_to_block
    from_block = cfg.get("test_from_block", 20_000_000)
    to_block = cfg.get("test_to_block", from_block + 9)

    raw_events = list(adapter.fetch_events(market, from_block, to_block))
    print(f"Fluid liquidations in [{from_block}, {to_block}]: {len(raw_events)}")

    if raw_events:
        print("First normalized event:")
        pprint.pprint(adapter.normalize(raw_events[0]))  

def test_fluid_lending_ethereum():
    csus = load_csus()
    csu = csus["fluid_lending_ethereum"]

    rpc_url = csu["rpc"]
    registry = csu["registry"]

    rows = get_fluid_lending_tvl_raw(
        rpc_url=rpc_url,
        registry=registry,
    )

    print(f"Number of markets: {len(rows)}")
    pprint.pprint(rows[0])

def test_venus_core():
    csus = load_csus()
    csu = csus["venus_core_pool_binance"]  # whatever key you used
    rows = get_venus_core_tvl_raw(csu["rpc"], csu["registry"])
    print("Venus markets:", len(rows))
    if rows:
        pprint.pprint(rows[0])

def test_venus_liquidations():
    csus = load_csus()
    csu = csus["venus_core_pool_binance"]  # your key
    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = VenusLiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    latest = w3.eth.block_number
    from_block = (latest-10) - 19  # just a small window to test

    logs = list(adapter.fetch_events(market, from_block, latest))
    print("Raw logs:", len(logs))
    if logs:
        row = adapter.normalize(logs[0])
        from pprint import pprint
        pprint(row)

def test_euler_v2_tvl():
    csus = load_csus()
    csu = csus["euler_v2_ethereum"]  # or whatever key you choose

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = EulerV2TVLAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    print("Euler v2 vaults:", len(market["vaults"]))

    latest = w3.eth.block_number
    rows = adapter.get_tvl_raw(market, latest)

    print("TVL rows:", len(rows))
    if rows:
        pprint.pprint(rows)


    csus = load_csus()
    csu = csus["euler_v2_avalanche"]

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = EulerV2TVLAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    print("Euler v2 Avalanche vaults:", len(market["vaults"]))

    latest = w3.eth.block_number
    rows = adapter.get_tvl_raw(market, latest)
    print("TVL rows (Avalanche):", len(rows))
    if rows:
        pprint.pprint(rows)


    csus = load_csus()
    csu = csus["euler_v2_ethereum"]
    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = EulerV2LiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    print("Euler v2 vaults:", len(market["vaults"]))

    latest = w3.eth.block_number
    from_block = latest - 9  # small window

    logs = list(adapter.fetch_events(market, from_block, latest))
    print("Raw liquidation logs:", len(logs))

    if logs:
        from pprint import pprint
        row = adapter.normalize(logs[0])
        pprint(row)

def test_euler_v2_liquidations():
    csus = load_csus()
    csu = csus["euler_v2_ethereum"]
    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = EulerV2LiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    print("Euler v2 vaults:", len(market["vaults"]))

    latest = w3.eth.block_number
    window_size = 10

    # Allow CSU config to define earliest block
    min_block = int(csu.get("test_from_block", max(latest - 100_000, 0)))

    print(
        f"Scanning backwards for liquidation events "
        f"from block {latest} down to {min_block}..."
    )

    to_block = latest
    found_any = False

    while to_block >= min_block:
        from_block = max(to_block - (window_size - 1), min_block)

        logs = list(adapter.fetch_events(market, from_block, to_block))
        print(f"Range [{from_block}, {to_block}] → {len(logs)} liquidation logs")

        if logs:
            found_any = True
            from pprint import pprint
            print("First normalized event:")
            pprint(adapter.normalize(logs[0]))
            break

        to_block = from_block - 1

    if not found_any:
        print("No liquidation events found in scanned range.")

def test_lista_liquidations():
    csus = load_csus()
    csu = csus["lista_lending_binance"]

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    adapter = ListaLiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    print("Moolah core:", market["moolah"])

    latest = w3.eth.block_number
    window_size = 10

    # Focus search around the last known liquidation block to avoid scanning
    # millions of blocks. You can override these in the CSU YAML if needed.
    known_last_liq = int(csu.get("known_last_liq_block", 70844268))
    span_before = int(csu.get("liq_span_before", 500))   # blocks before
    span_after = int(csu.get("liq_span_after", 2_000))    # blocks after

    start_block = max(known_last_liq - span_before, 0)
    end_block = min(known_last_liq + span_after, latest)

    print(
        f"Scanning backwards for Lista liquidation events "
        f"from block {end_block} down to {start_block} in {window_size}-block chunks..."
    )

    to_block = end_block
    found_any = False

    while to_block >= start_block:
        from_block = max(to_block - (window_size - 1), start_block)

        logs = list(adapter.fetch_events(market, from_block, to_block))
        print(f"Range [{from_block}, {to_block}] → {len(logs)} liquidation logs")

        if logs:
            found_any = True
            from pprint import pprint
            print("First normalized Lista liquidation event:")
            pprint(adapter.normalize(logs[0]))
            break

        to_block = from_block - 1

    if not found_any:
        print("No Lista liquidation events found in scanned range.")

    # NEW: report any markets with liquidations that we DON'T yet model in TVL
    unknown_ids = adapter.get_unknown_market_ids_hex()
    if unknown_ids:
        print("\nUnknown market_ids seen in Liquidate events (not in config['market_ids']):")
        for mid in unknown_ids:
            print("  ", mid)



# # Minimal Vault ABI: ERC4626 + withdrawQueue
# LISTA_VAULT_ABI_MIN = [
#     {
#         "inputs": [],
#         "name": "asset",
#         "outputs": [{"internalType": "address", "name": "", "type": "address"}],
#         "stateMutability": "view",
#         "type": "function",
#     },
#     {
#         "inputs": [],
#         "name": "withdrawQueueLength",
#         "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
#         "stateMutability": "view",
#         "type": "function",
#     },
#     {
#         "inputs": [
#             {"internalType": "uint256", "name": "index", "type": "uint256"},
#         ],
#         "name": "withdrawQueue",
#         "outputs": [
#             {"internalType": "bytes32", "name": "", "type": "bytes32"},
#         ],
#         "stateMutability": "view",
#         "type": "function",
#     },
# ]

# # Minimal Moolah ABI: only providers(id, token)
# LISTA_MOOLAH_ABI_MIN = [
#     {
#         "inputs": [
#             {"internalType": "bytes32", "name": "id", "type": "bytes32"},
#             {"internalType": "address", "name": "token", "type": "address"},
#         ],
#         "name": "providers",
#         "outputs": [
#             {"internalType": "address", "name": "", "type": "address"},
#         ],
#         "stateMutability": "view",
#         "type": "function",
#     },
# # ]
# # def debug_lista_providers():
#     """
#     Debug helper:
#       - Pick one Lista vault
#       - Read its withdrawQueue entries (market Ids)
#       - For each Id, call Moolah.providers(id, vaultAsset)
#       - Print discovered Provider addresses

#     This is purely to confirm the provider mapping before we worry about
#     liquidation events.
#     """
#     csus = load_csus()
#     csu = csus["lista_lending_binance"]

#     rpc_url = csu["rpc"]
#     w3 = Web3(Web3.HTTPProvider(rpc_url))

#     # Use Moolah address from CSU config if present; otherwise fall back to known address
#     moolah_addr = Web3.to_checksum_address(
#         csu.get("moolah", "0x8F73b65B4caAf64FBA2aF91cC5D4a2A1318E5D8C")
#     )
#     moolah = w3.eth.contract(address=moolah_addr, abi=LISTA_MOOLAH_ABI_MIN)

#     # Pick one vault to debug – top of your list
#     vault_addr = Web3.to_checksum_address("0x57134a64B7cD9F9eb72F8255A671F5Bf2fe3E2d0")
#     vault = w3.eth.contract(address=vault_addr, abi=LISTA_VAULT_ABI_MIN)

#     print(f"Vault: {vault_addr}")
#     asset = vault.functions.asset().call()
#     qlen = vault.functions.withdrawQueueLength().call()
#     print(f"  asset(): {asset}")
#     print(f"  withdrawQueueLength(): {qlen}")

#     max_to_check = min(qlen, 10)  # don't spam; just first 10 entries
#     providers_seen = set()

#     for i in range(max_to_check):
#         try:
#             market_id = vault.functions.withdrawQueue(i).call()
#         except Exception as e:
#             print(f"  [idx {i}] withdrawQueue() failed: {e}")
#             continue

#         try:
#             provider_addr = moolah.functions.providers(market_id, asset).call()
#         except Exception as e:
#             print(
#                 f"  [idx {i}] providers(id, asset) failed "
#                 f"for id={Web3.to_hex(market_id)}: {e}"
#             )
#             continue

#         # Normalize
#         market_id_hex = Web3.to_hex(market_id)
#         if int(provider_addr, 16) == 0:
#             print(f"  [idx {i}] id={market_id_hex} → provider: ZERO (none configured)")
#             continue

#         provider_cs = Web3.to_checksum_address(provider_addr)
#         providers_seen.add(provider_cs)
#         print(f"  [idx {i}] id={market_id_hex} → provider: {provider_cs}")

#     print(f"\nUnique providers discovered from this vault: {len(providers_seen)}")
#     for p in providers_seen:
#         print(f"  - {p}")

def test_cap_tvl():
    csus = load_csus()
    csu = csus["cap_ethereum"]   # adjust key if needed

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = CapTVLAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    print("Vault:", market["vault"])
    print("Debt token:", market["debt_token"])

    latest = w3.eth.block_number
    rows = adapter.get_tvl_raw(market, latest)
    print("Rows:", len(rows))

    import pprint
    pprint.pprint(rows[0])

def test_cap_liquidations():
    csus = load_csus()
    csu = csus["cap_ethereum"]

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = CapLiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    print("Cap Lender:", market["lender"])

    # Block window around known liquidation
    known_last_liq = 23146145
    span_before = 100
    span_after = 300

    latest = w3.eth.block_number
    from_block = max(known_last_liq - span_before, 0)
    to_block = min(known_last_liq + span_after, latest)

    print(
        f"Scanning Cap Liquidate events on ethereum "
        f"from block {from_block} to {to_block} (window=10)..."
    )

    rows = adapter.get_liquidations_raw(
        market,
        from_block=from_block,
        to_block=to_block,
        window=10,
    )

    print(f"Total Cap liquidation rows: {len(rows)}")
    if rows:
        print("First Cap liquidation event:")
        pprint.pprint(rows[0])

def test_gearbox_tvl():
    csus = load_csus()
    csu = csus["gearbox_ethereum"]

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))
    adapter = GearboxTVLAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    latest = w3.eth.block_number
    rows = adapter.get_tvl_raw(latest)
    print("Gearbox TVL rows:", len(rows))
    if rows:
        from pprint import pprint
        pprint(rows)

def test_gearbox_liquidations():

    csus = load_csus()
    csu = csus["gearbox_ethereum"]

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = GearboxLiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    # Discover all current Credit Facades dynamically
    facades = adapter.get_credit_facades()
    print(f"Discovered {len(facades)} Gearbox credit facades:")
    for f in facades:
        print(f"  - {f}")

    latest = w3.eth.block_number

    # You can override these in the CSU YAML once you find a real example.
    # For now, we scan a configurable window.
    start_block = int(csu.get("known_liq_start_block", latest - 50_000))
    end_block = int(csu.get("known_liq_end_block", latest - 10_000))
    window_size = int(csu.get("liq_window_size", 10))

    print(
        f"from block {start_block} to {end_block} (window={window_size})..."
    )

    total_rows = 0
    current_from = start_block
    first_row_printed = False

    while current_from <= end_block:
        current_to = min(current_from + window_size - 1, end_block)

        for facade in facades:
            logs = adapter.fetch_events(facade, current_from, current_to)
            if logs:
                print(
                    f"  Found {len(logs)} liquidation logs in "
                    f"[{current_from}, {current_to}] for facade {facade}"
                )
                for log in logs:
                    try:
                        # If your normalize signature is normalize(log), drop the facade arg.
                        row = adapter.normalize(facade, log)
                    except TypeError:
                        # Fallback if normalize(log) is used instead
                        row = adapter.normalize(log)
                    except Exception as e:
                        print("    normalize() failed for a log:", e)
                        continue

                    total_rows += 1

                    # Print the first decoded liquidation row in full so you can inspect it
                    if not first_row_printed:
                        from pprint import pprint

                        print("\nFirst decoded Gearbox liquidation row:")
                        pprint(row)
                        first_row_printed = True

        current_from = current_to + 1

    print(f"\nTotal Gearbox liquidation rows: {total_rows}")

def test_tectonic_tvl(pool: str = "main"):
    """Quick TVL sanity test for Tectonic on Cronos.

    This mirrors the style of the other tests in this file:
    - load CSU config
    - connect Web3
    - discover markets
    - read a small number of markets and print a few rows

    Pool should match your CSU keys (main/veno/defi).
    Expected CSU keys:
      - tectonic_cronos_main
      - tectonic_cronos_veno
      - tectonic_cronos_defi
    """

    csus = load_csus()
    key = f"tectonic_cronos_{pool}"
    if key not in csus:
        raise KeyError(
            f"CSU key '{key}' not found in csu_config.yaml. "
            f"Available keys include: {', '.join(sorted(csus.keys())[:12])}..."
        )

    csu = csus[key]

    rpc_url = csu["rpc"]
    chain = csu.get("chain", "cronos")

    # Use the pool's socket (Unitroller/proxy) as the comptroller-like address.
    comptroller = csu.get("TectonicSocket")
    if not comptroller:
        # Backward compatible with older naming
        if pool == "main":
            comptroller = csu.get("TectonicSocket_Main")
        elif pool == "veno":
            comptroller = csu.get("TectonicSocket_Veno")
        elif pool == "defi":
            comptroller = csu.get("TectonicSocket_DeFi") or csu.get("TectonicSocket_Defi")

    if not comptroller:
        raise KeyError(
            f"No comptroller/socket address found in CSU '{key}'. "
            f"Expected 'TectonicSocket' (preferred) or legacy per-pool socket fields."
        )

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))

    print(f"Tectonic TVL test: key={key} chain={chain} rpc={rpc_url}")
    print(f"  comptroller/socket: {comptroller}")

    # Discover markets, then sample a subset to avoid RPC rate limits.
    markets = discover_markets(w3, comptroller)
    print(f"Discovered markets: {len(markets)}")

    max_markets = int(csu.get("test_max_markets", 8))
    sleep_s = float(csu.get("test_sleep_s", 0.2))

    rows = []
    for i, market in enumerate(markets[:max_markets], start=1):
        if sleep_s > 0:
            import time
            time.sleep(sleep_s)

        try:
            state = read_market_state(w3, market)
            underlying = state["underlying"]
            udec = read_underlying_decimals(w3, underlying)
            supply_u, borrows_u, reserves_u = compute_totals_underlying(state, udec)

            row = {
                "protocol": "tectonic",
                "chain": chain,
                "pool": pool,
                "market": market,
                "underlying": underlying,
                "underlying_decimals": udec,
                "is_native": bool(state.get("isNative", 0)),
                "supply_underlying": str(supply_u),
                "borrows_underlying": str(borrows_u),
                "reserves_underlying": str(reserves_u),
            }
            rows.append(row)

            print(f"[{i}] market={market} underlying={underlying} supply={supply_u} borrows={borrows_u}")

        except Exception as e:
            print(f"[{i}] market={market} ⚠️ failed: {e}")

    print(f"\nTVL rows collected (sample): {len(rows)}")
    if rows:
        print("First row:")
        pprint.pprint(rows)

    return rows

def test_tectonic_tvl_all():
    """Run Tectonic TVL sanity tests for main/veno/defi pools."""

    for pool in ("main", "veno", "defi"):
        print("\n" + "=" * 80)
        print(f"Running Tectonic pool TVL test: {pool}")
        print("=" * 80)
        test_tectonic_tvl(pool)




    csus = load_csus()
    csu = csus["gearbox_ethereum"]

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = GearboxLiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    # Discover all current Credit Facades dynamically
    facades = adapter.get_credit_facades()
    print(f"Discovered {len(facades)} Gearbox credit facades:")
    for f in facades:
        print(f"  - {f}")

    latest = w3.eth.block_number

    # You can override these in the CSU YAML once you find a real example.
    # For now, we scan a configurable window.
    start_block = int(csu.get("known_liq_start_block", latest - 50_000))
    end_block = int(csu.get("known_liq_end_block", latest - 10_000))
    window_size = int(csu.get("liq_window_size", 10))

    print(
        f"from block {start_block} to {end_block} (window={window_size})..."
    )

    total_rows = 0
    current_from = start_block
    first_row_printed = False

    while current_from <= end_block:
        current_to = min(current_from + window_size - 1, end_block)

        for facade in facades:
            logs = adapter.fetch_events(facade, current_from, current_to)
            if logs:
                print(
                    f"  Found {len(logs)} liquidation logs in "
                    f"[{current_from}, {current_to}] for facade {facade}"
                )
                for log in logs:
                    try:
                        # If your normalize signature is normalize(log), drop the facade arg.
                        row = adapter.normalize(facade, log)
                    except TypeError:
                        # Fallback if normalize(log) is used instead
                        row = adapter.normalize(log)
                    except Exception as e:
                        print("    normalize() failed for a log:", e)
                        continue

                    total_rows += 1

                    # Print the first decoded liquidation row in full so you can inspect it
                    if not first_row_printed:
                        from pprint import pprint

                        print("\nFirst decoded Gearbox liquidation row:")
                        pprint(row)
                        first_row_printed = True

        current_from = current_to + 1

    print(f"\nTotal Gearbox liquidation rows: {total_rows}")

 # --- Tectonic liquidation test ---

def test_tectonic_liquidations(pool: str = "main"):
    """Quick liquidation sanity test for Tectonic on Cronos.

    This mirrors the style of other liquidation tests in this file:
    - load CSU config
    - construct adapter
    - scan a small block window
    - print number of raw liquidation rows
    - pretty-print the first row (if any)

    Pool should be one of: main | veno | defi
    Expected CSU keys:
      - tectonic_cronos_main
      - tectonic_cronos_veno
      - tectonic_cronos_defi
    """

    csus = load_csus()
    key = f"tectonic_cronos_{pool}"
    if key not in csus:
        raise KeyError(
            f"CSU key '{key}' not found in csu_config.yaml. "
            f"Available keys include: {', '.join(sorted(csus.keys())[:12])}..."
        )

    csu = csus[key]

    adapter = TectonicLiquidationAdapter.from_csu(csu)

    w3 = Web3(Web3.HTTPProvider(csu["rpc"], request_kwargs={"timeout": 30}))
    latest = w3.eth.block_number

    # Small search window by default; override in CSU YAML if needed
    # Scan deeper history safely under Cronos limits
    window_blocks = int(csu.get("test_liq_window_blocks", 10_000))  # must be <= 10k
    max_windows = int(csu.get("test_liq_windows", 50))              # 50 * 10k = 500k blocks
    max_markets = int(csu.get("test_max_markets", 5))

    print(
        f"Tectonic liquidation test: key={key} pool={pool} "
        f"latest={latest} window_blocks={window_blocks} max_windows={max_windows} "
        f"max_markets={max_markets}"
    )

    found_rows = []
    to_block = latest

    for w in range(max_windows):
        from_block = max(to_block - window_blocks + 1, 0)

        # IMPORTANT: avoid timestamp lookups during wide search (saves RPC calls)
        rows = list(
            adapter.fetch_events(
                from_block=from_block,
                to_block=to_block,
                max_markets=max_markets,
                include_timestamp=False,
            )
        )

        print(f"Window {w+1}/{max_windows}: [{from_block}, {to_block}] → {len(rows)} liquidations")

        if rows:
            found_rows = rows
            break

        to_block = from_block - 1
        if to_block <= 0:
            break

    print(f"Liquidation rows found: {len(found_rows)}")

    if found_rows:
        print("First liquidation row:")
        from pprint import pprint
        pprint(found_rows[0])

        # If you want the timestamp for the first row only (1 extra RPC call):
        bn = int(found_rows[0]["block_number"])
        ts = w3.eth.get_block(bn)["timestamp"]
        print(f"First row timestamp: {ts}")

    return found_rows

def test_tectonic_liquidations_all():
    for pool in ("main", "veno", "defi"):
        print("\n" + "=" * 80)
        print(f"Running Tectonic liquidation test: {pool}")
        print("=" * 80)
        test_tectonic_liquidations(pool)

def test_kinetic_tvl():
    csus = load_csus()
    csu = csus["kinetic_flare"]

    rpc_url = csu["rpc"]
    unitroller = csu["unitroller"]  # Comptroller proxy
    chain = csu.get("chain", "flare")

    adapter = KineticTVLAdapter(
    rpc_url=rpc_url,
    unitroller=unitroller,
    chain="flare",
)
    rows = adapter.fetch()

    print(f"Kinetic markets sampled: {len(rows)}")
    if rows:
        pprint.pprint(rows[:3])

def test_kinetic_liquidations():
    csus = load_csus()
    csu = csus["kinetic_flare"]

    rpc_url = csu["rpc"]
    unitroller = csu["unitroller"]

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
    # Flare may be POA-like; this middleware is safe to inject.
    try:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except Exception:
        pass

    adapter = KineticLiquidationAdapter(
        rpc_url=rpc_url,
        unitroller=unitroller,
        chain=csu.get("chain", "flare"),
        protocol=csu.get("protocol", "kinetic"),
        version=csu.get("version", "v1"),
    )

    latest = w3.eth.block_number
    window_size = int(csu.get("liq_window_size", 30))

    # Focus search around an anchor to avoid scanning the entire chain.
    # You can override these in the CSU YAML once you find a real example.
    anchor = int(csu.get("known_last_liq_block", latest))
    span_before = int(csu.get("liq_span_before", 200_000))
    span_after = int(csu.get("liq_span_after", 0))

    start_block = max(anchor - span_before, 0)
    end_block = min(anchor + span_after, latest)

    print("Kinetic unitroller:", unitroller)
    try:
        markets = adapter.discover_markets()
        print(f"Kinetic markets: {len(markets)}")
    except Exception as e:
        print("Market discovery failed:", e)

    print(
        f"Scanning backwards for Kinetic liquidation events "
        f"from block {end_block} down to {start_block} in {window_size}-block chunks..."
    )

    to_block = end_block
    found_any = False

    while to_block >= start_block:
        from_block = max(to_block - (window_size - 1), start_block)

        scan = ScanParams(
            from_block=from_block,
            to_block=to_block,
            window=window_size,
            sleep_s=float(csu.get("liq_sleep_s", 0.15)),
        )

        rows = list(adapter.iter_liquidations(scan))
        print(f"Range [{from_block}, {to_block}] → {len(rows)} liquidation rows")

        if rows:
            found_any = True
            from pprint import pprint
            print("First decoded Kinetic liquidation row:")
            pprint(rows[0])

            # Optional: print timestamp for the first event only (1 extra RPC call)
            bn = int(rows[0]["block_number"])
            ts = w3.eth.get_block(bn)["timestamp"]
            print(f"First row timestamp: {ts}")
            break

        to_block = from_block - 1

    if not found_any:
        print("No Kinetic liquidation events found in scanned range.")

def test_tydro_tvl():
    """Quick TVL sanity test for Tydro (Aave v3-style) on Ink.

    Mirrors other tests:
      - load CSU config
      - connect Web3
      - construct adapter
      - resolve market
      - fetch TVL raw at latest block
      - print a few rows
    """

    csus = load_csus()
    csu = csus["tydro_ink"]

    w3 = Web3(Web3.HTTPProvider(csu["rpc"], request_kwargs={"timeout": 30}))


    adapter = TydroTVLAdapter(
        web3=w3,
        chain=csu.get("chain", "ink"),
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()

    if isinstance(market, dict):
        if "pool" in market:
            print("Resolved Pool:", market["pool"])
        if "reserves" in market:
            print("Reserves:", len(market["reserves"]))

    # Keep the market = adapter.resolve_market() and prints as-is; fetch TVL rows using correct call
    rows = adapter.get_tvl_rows()

    print("TVL rows:", len(rows))
    if rows:
        from pprint import pprint
        print("First 3 rows:")
        pprint(rows[:3])

    return rows

def test_tydro_liquidations():
    csus = load_csus()
    csu = csus["tydro_ink"]  # <-- whatever your CSU key is

    w3 = Web3(Web3.HTTPProvider(csu["rpc"]))

    adapter = TydroLiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    market = adapter.resolve_market()
    print("Tydro Pool:", market["pool"])

    latest = w3.eth.block_number

    # Just scan last N blocks (no known liquidation block yet)
    n_blocks = int(csu.get("liq_n_blocks", 250_000))
    window_size = int(csu.get("liq_window", 10_000))

    start_block = max(latest - n_blocks, 0)
    end_block = latest

    print(
        f"Scanning Tydro Pool liquidation events from block {end_block} down to {start_block} "
        f"in {window_size}-block chunks..."
    )

    # Scan backwards like your Lista test
    to_block = end_block
    found_any = False

    while to_block >= start_block:
        from_block = max(to_block - (window_size - 1), start_block)

        logs = list(adapter.fetch_events(market, from_block, to_block))
        print(f"Range [{from_block}, {to_block}] → {len(logs)} liquidation logs")

        if logs:
            found_any = True
            print("First normalized Tydro liquidation event:")
            pprint.pprint(adapter.normalize(logs[0]))
            break

        to_block = from_block - 1

    if not found_any:
        print("No Tydro liquidation events found in scanned range.")

def test_sumer_liquidations():
    """Scan backwards in chunks until we find at least one Sumer liquidation.

    This mirrors the style of the other liquidation tests in this file:
      - load CSU config
      - connect Web3
      - build adapter
      - scan backwards in windows and print progress
      - stop at first window that returns rows, print the first row

    Notes:
      - Meter chainId is 82. We print chainId + code-bytes for comptroller for sanity.
      - You can override scan params in csu_config.yaml:
          test_liq_window_blocks:  (default 10_000)
          test_liq_max_windows:    (default 50)
          test_liq_chunk_size:     (default 5_000)
    """

    csus = load_csus()
    csu = csus["sumermoney_meter"]

    w3 = Web3(Web3.HTTPProvider(csu["rpc"], request_kwargs={"timeout": 30}))

    # POA-like middleware is safe to inject for many non-ETH chains (harmless if not needed)
    try:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except Exception:
        pass

    adapter = SumerLiquidationAdapter(
        web3=w3,
        chain=csu["chain"],
        config=csu,
        outputs_dir=csu["outputs_dir"],
    )

    latest = w3.eth.block_number
    chain_id = w3.eth.chain_id

    comptroller = csu.get("comptroller")
    comp_code_bytes = None
    if comptroller:
        try:
            comp_code_bytes = len(w3.eth.get_code(Web3.to_checksum_address(comptroller)))
        except Exception:
            comp_code_bytes = None

    print(
        f"Sumer liquidation scan: chain={csu.get('chain')} chainId={chain_id} "
        f"latest={latest} rpc={csu.get('rpc')}\n"
        f"  comptroller={comptroller} code_bytes={comp_code_bytes}"
    )

    window_blocks = int(csu.get("test_liq_window_blocks", 10_000))
    max_windows = int(csu.get("test_liq_max_windows", 50))
    chunk_size = int(csu.get("test_liq_chunk_size", 5_000))

    # Optional anchor controls to avoid scanning entire history.
    # If you set these in YAML, we'll only scan [anchor - span_before, anchor + span_after]
    anchor = csu.get("known_last_liq_block")
    span_before = int(csu.get("liq_span_before", 500_000))
    span_after = int(csu.get("liq_span_after", 0))

    if anchor is not None:
        anchor = int(anchor)
        start_block = max(anchor - span_before, 0)
        end_block = min(anchor + span_after, latest)
    else:
        # Default: scan back max_windows * window_blocks blocks
        start_block = max(latest - (window_blocks * max_windows), 0)
        end_block = latest

    print(
        f"Scanning backwards from {end_block} down to {start_block} "
        f"in windows of {window_blocks} blocks (max_windows={max_windows}, chunk_size={chunk_size})"
    )

    found_rows = []
    to_block = end_block

    for i in range(max_windows):
        if to_block < start_block:
            break

        from_block = max(to_block - window_blocks + 1, start_block)

        print(f"  Window {i+1}/{max_windows}: [{from_block}, {to_block}] ...", end="")

        try:
            rows = adapter.get_liquidation_rows(
                from_block=from_block,
                to_block=to_block,
                chunk_size=chunk_size,
            )
        except Exception as e:
            print(f" ERROR: {e}")
            # step back one window and keep going
            to_block = from_block - 1
            continue

        print(f" {len(rows)} rows")

        if rows:
            found_rows = rows
            break

        # move the window back
        to_block = from_block - 1

    print(f"Done. Liquidation rows found: {len(found_rows)}")

    assert isinstance(found_rows, list)

    if not found_rows:
        print(
            "No liquidation events found in the scanned range. "
            "This can mean: (1) no liquidations in that period, "
            "(2) wrong comptroller/markets for Meter, or "
            "(3) adapter is fetching logs from the wrong contract(s)."
        )
        return []

    # Print first row as proof of life
    r0 = found_rows[0]
    from pprint import pprint
    print("First decoded Sumer liquidation row:")
    pprint(r0)

    # Sanity checks
    assert "tx_hash" in r0 and r0["tx_hash"].startswith("0x")
    assert "ctoken_borrowed" in r0 and Web3.is_address(r0["ctoken_borrowed"])
    assert "repay_amount_raw" in r0 and isinstance(r0["repay_amount_raw"], int)

    return found_rows

if __name__ == "__main__":
    load_csus()
    # test_fluid_lending_ethereum()
    # test_fluid_liq()
    # debug_capyfi()
    # test_capyfi_tvl()
    # test_venus_core()
    # test_venus_liquidations()
    # test_euler_v2_tvl()
    # test_euler_v2_liquidations()
    # test_lista_tvl()
    # test_lista_liquidations()
    # debug_lista_providers()
    # test_cap_tvl()
    # test_cap_liquidations()
    # test_gearbox_tvl()
    # test_tectonic_tvl_all()
    # test_tectonic_liquidations_all()
    # test_gearbox_liquidations()
    # other()
    # test_kinetic_tvl()
    # test_kinetic_liquidations()
    # test_tydro_tvl()
    # test_tydro_liquidations()
    test_sumer_liquidations()

