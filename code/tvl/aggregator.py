import csv
from datetime import datetime, timezone
from web3 import Web3
from importlib import import_module
from .config import PROVIDERS, POOL_ABI, ORACLE_ABI, DATA_PROVIDER_ABI, ERC20_ABI
from .classification import classify_asset
from .blockchain_utils import connect_rpc, get_pool_addresses, get_total_supply
from pathlib import Path
from .price_cache_connect import CachePriceSource

def run_chain(
    protocol,
    chain,
    rpc_url,
    provider_addr,
    out_root: str = "data/out",
    no_write: bool = False,
    price_mode: str = "oracle",
    registry_path: str = "price_cache/token_registry.yaml",
    price_cache_dir: str = "price_cache/pricing",
    price_requests_dir: str = "price_cache/pricing/requests",
    asof_ts: int | None = None,
    asof_tolerance_sec: int = 3600,
):
    w3 = connect_rpc(rpc_url)
    provider_addr = provider_addr or PROVIDERS.get(chain)
    assert provider_addr, f"No provider address for chain '{chain}'."

    adapter_module = f"tvl.adapters.{protocol.lower().replace(' ', '_')}_adapter"
    adapter = import_module(adapter_module)

    addrs = get_pool_addresses(w3, provider_addr)
    oracle = w3.eth.contract(address=addrs["oracle"], abi=ORACLE_ABI)
    reserves = adapter.get_reserves(w3, provider_addr)
    meta = adapter.get_protocol_metadata()

    print(f"🔹 {chain.upper()}: provider={provider_addr} oracle={addrs['oracle']}")
    print(f"   Reserves found: {len(reserves)}")

    rows = []
    total_tvl, base_tvl = 0.0, 0.0
    missing_assets = []
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")
    ts = int((now_utc if asof_ts is None else datetime.fromtimestamp(asof_ts, tz=timezone.utc)).timestamp())

    cache_ps = None
    if price_mode == "cache":
        cache_ps = CachePriceSource(
            chain=chain,
            registry_path=Path(registry_path),
            cache_dir=Path(price_cache_dir),
            requests_dir=Path(price_requests_dir),
            tolerance_sec=asof_tolerance_sec,
        )

    
    for reserve in reserves:
        try:
            # --- Extract and normalize addresses ---
            asset_addr = reserve.get("asset")
            a_addr = reserve.get("aToken")
            vd_addr = reserve.get("variableDebt")
            sd_addr = reserve.get("stableDebt")

            if not isinstance(asset_addr, str):
                print(f"{chain} ⚠️ bad asset address type for {reserve}")
                continue

            asset_addr = Web3.to_checksum_address(asset_addr)

            # --- ERC20 contract for underlying token ---
            under = w3.eth.contract(address=asset_addr, abi=ERC20_ABI)
            try:
                sym = reserve.get("symbol") or under.functions.symbol().call()
            except Exception:
                sym = "(unknown)"

            # --- Price lookup (cache-only when price_mode == 'cache') ---
            price = None
            if price_mode == "cache" and cache_ps is not None:
                price = cache_ps.get(asset_addr, ts)
                if price is None:
                    # Leave this asset in an incomplete state and record that it needs backfill.
                    print(
                        f"{chain} ⚠️ missing cached/as-of price for {sym} ({asset_addr}); "
                        f"timestamp {ts} queued in pricing/requests."
                    )
                    missing_assets.append(
                        {
                            "date": date_str,
                            "chain": chain,
                            "protocol": protocol,
                            "symbol": sym,
                            "asset": asset_addr,
                            "timestamp": ts,
                            "price_mode": price_mode,
                        }
                    )
            else:
                # Pure oracle mode: always compute a price
                price = adapter.get_oracle_price(w3, oracle, asset_addr)

            # --- Get supplies ---
            a_supply = get_total_supply(w3, a_addr)
            vd_supply = get_total_supply(w3, vd_addr)
            sd_supply = get_total_supply(w3, sd_addr)

            # --- Compute USD values (or leave as None if price is missing) ---
            if price is None:
                collateral_usd = None
                debt_usd = None
                net_usd = None
            else:
                collateral_usd = a_supply * price
                debt_usd = (vd_supply + sd_supply) * price
                net_usd = collateral_usd - debt_usd

            # --- Classify asset type ---
            asset_class, source = classify_asset([], sym)
            category = "manual"
            tags = ""

            if collateral_usd is not None:
                total_tvl += collateral_usd
                if asset_class == "base":
                    base_tvl += collateral_usd

            # --- Append results ---
            rows.append({
                "date": date_str,
                "chain": chain,
                "protocol": protocol,
                "symbol": sym,
                "asset": asset_addr,
                "aToken": a_addr,
                "aToken_supply": a_supply,
                "variableDebt_supply": vd_supply,
                "stableDebt_supply": sd_supply,
                "price_usd": price,
                "collateral_usd": collateral_usd,
                "debt_usd": debt_usd,
                "net_usd": net_usd,
                "category": category,
                "tags": tags,
                "asset_class": asset_class,
                "category_source": source,
                "missing_price": price is None,
            })

        except Exception as e:
            print(f"{chain} ⚠️ reserve {reserve.get('symbol', '(unknown)')}: {e}")

    # --- Write outputs (assets + summary) in standardized locations ---
    protocol_slug = protocol.lower().replace(" ", "_")
    out_dir = Path(out_root) / "tvl" / f"{protocol_slug}_{chain}"
    out_dir.mkdir(parents=True, exist_ok=True)

    assets_csv = out_dir / f"tvl_assets_{date_str}.csv"
    summary_csv = out_dir / f"tvl_summary_{date_str}.csv"

    # Assets CSV
    assets_fields = [
        "date","chain","protocol","symbol","asset","aToken",
        "aToken_supply","variableDebt_supply","stableDebt_supply",
        "price_usd","collateral_usd","debt_usd","net_usd",
        "category","tags","asset_class","category_source",
        "missing_price",
    ]

    if not no_write:
        with open(assets_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=assets_fields)
            writer.writeheader()
            writer.writerows(rows)

    # Summary CSV
    summary_fields = ["date","chain","protocol","tvl_usd","base_component_usd","n_assets","price_mode"]
    summary_row = {
        "date": date_str,
        "chain": chain,
        "protocol": protocol,
        "tvl_usd": total_tvl,
        "base_component_usd": base_tvl,
        "n_assets": len(rows),
        "price_mode": price_mode,
    }

    if not no_write:
        with open(summary_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=summary_fields)
            writer.writeheader()
            writer.writerow(summary_row)

    # Console prints
    excluded_share = (1 - base_tvl/total_tvl) if total_tvl > 0 else 0.0
    print(f"✅ {chain}: Total ${total_tvl:,.2f} | Base ${base_tvl:,.2f} | Excluded {excluded_share*100:.2f}%")
    if not no_write:
        print(f"💾 Wrote assets → {assets_csv}")
        print(f"💾 Wrote summary → {summary_csv}")

    # Log missing-price assets to a persistent CSV and print a summary.
    if missing_assets and not no_write:
        log_dir = Path(out_root) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "tvl_missing_prices.csv"
        log_fields = ["date", "chain", "protocol", "symbol", "asset", "timestamp", "price_mode"]

        write_header = not log_path.exists()
        with open(log_path, "a", newline="") as lf:
            lw = csv.DictWriter(lf, fieldnames=log_fields)
            if write_header:
                lw.writeheader()
            for m in missing_assets:
                lw.writerow(m)

        print(
            f"⚠ {chain}: {len(missing_assets)} assets missing cached prices. "
            f"Logged to {log_path}"
        )
        for m in missing_assets:
            print(f"   - {m['symbol']} ({m['asset']}) @ ts={m['timestamp']}")