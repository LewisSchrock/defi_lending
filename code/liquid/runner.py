# runner.py
"""
Generic config-driven DeFi runner with modular adapters.
- Reads YAML config of CSUs (protocol×version×chain)
- Builds the right adapter (e.g., AaveV3Adapter) for the CSU
- Fetches liquidation events and/or daily aggregates
"""

import argparse, os, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from web3 import Web3, HTTPProvider

try:
    import yaml
except Exception:
    print("[hint] pip install pyyaml", file=sys.stderr)
    raise

# Import adapters
from adapters.aave_v3 import AaveV3Adapter
from adapters.base import LiquidationAdapter

ADAPTER_REGISTRY = {
    ("aave","v3"): AaveV3Adapter,
    # add ("compound","v3"): CompoundV3Adapter, etc.
}

def die(msg: str, code: int = 1):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(code)

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def ensure_dir(p: str):
    Path(p).mkdir(parents=True, exist_ok=True)

def get_block_timestamp(w3: Web3, block_number: int) -> int:
    return int(w3.eth.get_block(block_number)["timestamp"])

def find_block_by_timestamp(w3: Web3, target_ts: int, lo: int, hi: int) -> int:
    best = hi
    while lo <= hi:
        mid = (lo + hi) // 2
        mts = get_block_timestamp(w3, mid)
        if mts >= target_ts:
            best = mid
            hi = mid - 1
        else:
            lo = mid + 1
    return best

def aggregate_daily(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame(columns=[
            "protocol","version","chain","date","collateral_token","debt_token",
            "liquidations_count","sum_collateral_raw","sum_debt_repaid_raw"
        ])
    events_df["date"] = pd.to_datetime(events_df["timestamp"], unit="s", utc=True).dt.date
    return (
        events_df.groupby(["protocol","version","chain","date","collateral_token","debt_token"], as_index=False)
        .agg(
            liquidations_count=("tx_hash","nunique"),
            sum_collateral_raw=(
                "collateral_amount",
                lambda s: sum(int(x) for x in s.dropna()) if len(s) else 0,
            ),
            sum_debt_repaid_raw=(
                "debt_repaid",
                lambda s: sum(int(x) for x in s.dropna()) if len(s) else 0,
            ),
        )
    )

def main():
    ap = argparse.ArgumentParser()
    # ap.add_argument("--config", required=True, help="YAML config with csus list")
    ap.add_argument("--csu", required=True, help="key under csus (e.g., aave_v3_ethereum)")
    ap.add_argument("--dataset", default="liquidation_daily", choices=["liquidation_events","liquidation_daily"])
    ap.add_argument("--from-date", type=str, help="YYYY-MM-DD UTC (exclusive with --from-block)")
    ap.add_argument("--to-date", type=str, help="YYYY-MM-DD UTC (exclusive with --to-block)")
    ap.add_argument("--from-block", type=str, help="int or 'latest' (exclusive with --from-date)")
    ap.add_argument("--to-block", type=str, default="latest", help="int or 'latest' (exclusive with --to-date)")
    ap.add_argument("--chunk-blocks", type=int, default=120_000)
    ap.add_argument("--write-csv", default="true", action="store_true")
    args = ap.parse_args()

    cfg_path = "config/csu_config.yaml"
    cfg = load_config(cfg_path)
    csus = cfg.get("csus", {})
    if args.csu not in csus:
        die(f"CSU '{args.csu}' not found in config.")
    c = csus[args.csu]

    required = ["protocol","version","chain","rpc","registry","outputs_dir"]
    missing = [k for k in required if k not in c]
    if missing:
        die(f"Missing keys in csu '{args.csu}': {missing}")

    protocol, version, chain = c["protocol"], c["version"], c["chain"]
    rpc_url, registry, outdir = c["rpc"], c["registry"], c["outputs_dir"]
    ensure_dir(outdir)

    key = (protocol, version)
    if key not in ADAPTER_REGISTRY:
        die(f"No adapter registered for {key}")
    AdapterCls = ADAPTER_REGISTRY[key]

    # build web3
    w3 = Web3(HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        die("Web3 connection failed; check RPC URL/key.")

    # instantiate adapter
    adapter: LiquidationAdapter = AdapterCls(web3=w3, chain=chain, config={"registry": registry}, outputs_dir=outdir)

    # Resolve market and determine block window
    market = adapter.resolve_market()

    latest = w3.eth.block_number
    earliest = 12_000_000 if chain == "ethereum" else 0  # simple default
    if args.from_date and args.from_block:
        die("Use either --from-date or --from-block, not both.")
    if args.to_date and args.to_block != "latest":
        die("Use either --to-date or --to-block, not both.")

    if not args.from_date and not args.from_block:
        die("Provide either --from-date or --from-block.")
    if not args.to_date and args.to_block is None:
        die("Provide either --to-date or --to-block.")

    if args.from_date:
        ts = int(datetime.fromisoformat(args.from_date).replace(tzinfo=timezone.utc).timestamp())
        from_block = find_block_by_timestamp(w3, ts, earliest, latest)
    else:
        from_block = latest if args.from_block == "latest" else int(args.from_block or latest)

    if args.to_date:
        ts2 = int(datetime.fromisoformat(args.to_date).replace(tzinfo=timezone.utc).timestamp())
        to_block = find_block_by_timestamp(w3, ts2, from_block, latest)
    else:
        to_block = latest if args.to_block == "latest" else int(args.to_block)

    if from_block > to_block:
        die(f"from_block {from_block} > to_block {to_block}")

    print(f"[info] {args.csu} → {protocol} {version} on {chain}")
    print(f"[info] Market: {market}")
    print(f"[info] Scanning blocks [{from_block}, {to_block}] for dataset '{args.dataset}'")

    # Fetch & normalize
    rows: List[Dict[str,Any]] = []
    seen = set()
    for raw in adapter.fetch_events(market, from_block, to_block):
        ev = adapter.normalize(raw)
        key = (ev["tx_hash"], ev["log_index"])
        if key in seen: 
            continue
        seen.add(key)
        rows.append(ev)

    # Persist
    events_df = pd.DataFrame(rows, columns=[
        "protocol","version","chain","tx_hash","log_index","block_number","timestamp",
        "borrower","liquidator","collateral_token","debt_token",
        "collateral_amount","debt_repaid","receive_a_token","usd_value"
    ])
    events_path_parquet = os.path.join(outdir, "liquidation_events.parquet")
    events_df.to_parquet(events_path_parquet, index=False)
    if args.write_csv:
        events_df.to_csv(os.path.join(outdir, "liquidation_events.csv"), index=False)
    print(f"[ok] events → {events_path_parquet} (rows={len(events_df)})")

    if args.dataset == "liquidation_daily":
        daily_df = aggregate_daily(events_df)
        # Avoid pyarrow int64 overflow on very large raw integer sums by storing as strings
        for col in ["sum_collateral_raw", "sum_debt_repaid_raw"]:
            if col in daily_df.columns:
                daily_df[col] = daily_df[col].astype(str)
        daily_path_parquet = os.path.join(outdir, "liquidation_daily.parquet")
        daily_df.to_parquet(daily_path_parquet, index=False)
        if args.write_csv:
            daily_df.to_csv(os.path.join(outdir, "liquidation_daily.csv"), index=False)
        print(f"[ok] daily → {daily_path_parquet} (rows={len(daily_df)})")

if __name__ == "__main__":
    main()
