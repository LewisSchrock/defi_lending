#!/usr/bin/env python3
"""
DeFi CSU Runner (config-driven)

Usage:
  python defi_runner.py --config csu_config.yaml --csu aave_v3_ethereum --dataset liquidation_daily --from-date 2024-06-01 --to-date 2024-06-02
  python defi_runner.py --config csu_config.yaml --csu aave_v3_ethereum --dataset liquidation_events --from-block 16500000 --to-block latest

Datasets supported (for now):
  - liquidation_events : raw Aave v3 LiquidationCall events
  - liquidation_daily  : per-day aggregates (counts + raw sums)

Notes:
  - Uses the Aave V3 PoolAddressesProvider (registry) to resolve the active Pool each run.
  - Extendable: add new CSUs to config; add new adapters in-code (e.g., for other protocols).
"""

import argparse, os, sys, time, json, math
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path

# Dependencies
import pandas as pd
from web3 import Web3, HTTPProvider
from web3._utils.events import get_event_data
try:
    import yaml  # pyyaml
except Exception:
    print("[hint] pip install pyyaml", file=sys.stderr)
    raise

# -----------------------------
# ABIs
# -----------------------------
ADDRESSES_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

POOL_LIQUIDATION_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True,  "name": "collateralAsset", "type": "address"},
        {"indexed": True,  "name": "debtAsset",       "type": "address"},
        {"indexed": False, "name": "user",            "type": "address"},
        {"indexed": False, "name": "debtToCover",     "type": "uint256"},
        {"indexed": False, "name": "liquidatedCollateralAmount", "type": "uint256"},
        {"indexed": False, "name": "liquidator",      "type": "address"},
        {"indexed": False, "name": "receiveAToken",   "type": "bool"},
    ],
    "name": "LiquidationCall",
    "type": "event",
}

# -----------------------------
# Helpers
# -----------------------------
def die(msg: str, code: int = 1):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(code)

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        if path.endswith(".json"):
            return json.load(f)
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

# -----------------------------
# Aave V3 via registry
# -----------------------------
def resolve_pool_from_registry(w3: Web3, registry_addr: str) -> str:
    contract = w3.eth.contract(address=Web3.to_checksum_address(registry_addr), abi=ADDRESSES_PROVIDER_ABI)
    pool = contract.functions.getPool().call()
    return Web3.to_checksum_address(pool)

def fetch_aave_v3_liquidations(w3: Web3, pool_addr: str, from_block: int, to_block: int, chunk: int = 120_000):
    pool = w3.eth.contract(address=Web3.to_checksum_address(pool_addr), abi=[{"type": "event", **POOL_LIQUIDATION_EVENT_ABI}])
    ev = pool.events.LiquidationCall()
    start = from_block
    while start <= to_block:
        end = min(to_block, start + chunk)
        logs = ev.get_logs(fromBlock=start, toBlock=end)
        for log in logs:
            yield log
        start = end + 1

def normalize_aave_v3_event(w3: Web3, log, meta: Dict[str,str]) -> Dict[str, Any]:
    decoded = get_event_data(w3.codec, POOL_LIQUIDATION_EVENT_ABI, log)
    args = decoded["args"]
    block = log["blockNumber"]
    ts = get_block_timestamp(w3, block)
    return {
        "protocol": meta["protocol"],
        "version": meta["version"],
        "chain": meta["chain"],
        "tx_hash": log["transactionHash"].hex(),
        "log_index": int(log["logIndex"]),
        "block_number": int(block),
        "timestamp": int(ts),
        "borrower": str(args["user"]),
        "liquidator": str(args["liquidator"]),
        "collateral_token": Web3.to_checksum_address(args["collateralAsset"]),
        "debt_token": Web3.to_checksum_address(args["debtAsset"]),
        "collateral_amount": str(int(args["liquidatedCollateralAmount"])),
        "debt_repaid": str(int(args["debtToCover"])),
        "receive_a_token": bool(args["receiveAToken"]),
        "usd_value": None,
    }

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
            sum_collateral_raw=("collateral_amount", lambda s: s.astype("int64").sum() if len(s) else 0),
            sum_debt_repaid_raw=("debt_repaid", lambda s: s.astype("int64").sum() if len(s) else 0),
        )
    )

# -----------------------------
# Runner
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="YAML or JSON config with csus: {...}")
    ap.add_argument("--csu", required=True, help="Key under csus (e.g., aave_v3_ethereum)")
    ap.add_argument("--dataset", required=True, choices=["liquidation_events","liquidation_daily"])
    ap.add_argument("--from-date", type=str, help="YYYY-MM-DD UTC (exclusive with --from-block)")
    ap.add_argument("--to-date", type=str, help="YYYY-MM-DD UTC (exclusive with --to-block)")
    ap.add_argument("--from-block", type=str, help="int or 'latest' (exclusive with --from-date)")
    ap.add_argument("--to-block", type=str, default="latest", help="int or 'latest' (exclusive with --to-date)")
    ap.add_argument("--chunk-blocks", type=int, default=120_000)
    ap.add_argument("--write-csv", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
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

    # Connect web3
    w3 = Web3(HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        die("Web3 connection failed; check RPC URL/key.")
    print(f"[info] Connected to {chain}. Resolving Aave v3 Pool from registry: {registry}")

    # Resolve current Pool
    pool = resolve_pool_from_registry(w3, registry)
    print(f"[info] Resolved Pool: {pool}")

    # Date/Block window
    latest = w3.eth.block_number
    earliest = 12_000_000  # rough default for Eth mainnet; adjust if needed
    if args.from_date and args.from_block:
        die("Use either --from-date or --from-block, not both.")
    if args.to_date and args.to_block != "latest":
        die("Use either --to-date or --to-block, not both.")

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

    print(f"[info] Scanning blocks [{from_block}, {to_block}] for dataset '{args.dataset}'")

    # Fetch & normalize
    rows: List[Dict[str,Any]] = []
    seen = set()
    meta = {"protocol":protocol, "version":version, "chain":chain}

    for log in fetch_aave_v3_liquidations(w3, pool, from_block, to_block, chunk=args.chunk_blocks):
        ev = normalize_aave_v3_event(w3, log, meta)
        key = (ev["tx_hash"], ev["log_index"])
        if key in seen: 
            continue
        seen.add(key)
        rows.append(ev)

    events_df = pd.DataFrame(rows, columns=[
        "protocol","version","chain","tx_hash","log_index","block_number","timestamp",
        "borrower","liquidator","collateral_token","debt_token",
        "collateral_amount","debt_repaid","receive_a_token","usd_value"
    ])

    # Write events
    events_path_parquet = os.path.join(outdir, "liquidation_events.parquet")
    events_df.to_parquet(events_path_parquet, index=False)
    if args.write_csv:
        events_df.to_csv(os.path.join(outdir, "liquidation_events.csv"), index=False)
    print(f"[ok] events → {events_path_parquet} (rows={len(events_df)})")

    if args.dataset == "liquidation_daily":
        daily_df = aggregate_daily(events_df)
        daily_path_parquet = os.path.join(outdir, "liquidation_daily.parquet")
        daily_df.to_parquet(daily_path_parquet, index=False)
        if args.write_csv:
            daily_df.to_csv(os.path.join(outdir, "liquidation_daily.csv"), index=False)
        print(f"[ok] daily → {daily_path_parquet} (rows={len(daily_df)})")

    # Quick summary
    if len(events_df):
        t0, t1 = int(events_df["timestamp"].min()), int(events_df["timestamp"].max())
        print(f"[summary] events={len(events_df)}  time_window_utc=({datetime.utcfromtimestamp(t0)} → {datetime.utcfromtimestamp(t1)})")
    else:
        print("[summary] No liquidation events found in the selected window.")

if __name__ == "__main__":
    main()
