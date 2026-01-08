#!/usr/bin/env python3
"""
Aave V3 (Ethereum) Liquidations → Events + Daily Aggregates (standardized schema)

Usage examples:
  export RPC_URL="https://eth-mainnet.your-provider.example/v2/KEY"
  # Option 1: provide Aave V3 Pool address directly (recommended to avoid ambiguity)
  python aave_v3_liquidations_eth.py --pool 0x... --from-block 16500000 --to-block latest

  # Option 2: resolve Pool via AddressesProvider.getPool() (if you know the provider address)
  python aave_v3_liquidations_eth.py --address-provider 0x... --from-block 16500000 --to-block latest

  # Optional: restrict by date range instead of block range (script will map to blocks using binary search)
  python aave_v3_liquidations_eth.py --pool 0x... --from-date 2023-01-01 --to-date 2023-12-31

Outputs (in ./out/):
  - events.parquet  : one row per liquidation event (standard schema)
  - events.csv
  - daily.parquet   : daily aggregates per (protocol, chain, version, date, collateral_token, debt_token)
  - daily.csv

Standard Event Schema (per row):
{
  "protocol": "aave",
  "version": "v3",
  "chain": "ethereum",
  "tx_hash": "0x...",
  "log_index": 123,
  "block_number": 123456,
  "timestamp": 1699999999,
  "borrower": "0x...",
  "liquidator": "0x...",
  "collateral_token": "0x...",
  "debt_token": "0x...",
  "collateral_amount": "123456789",   # raw units (stringified)
  "debt_repaid": "987654321",         # raw units (stringified)
  "receive_a_token": true/false,
  "usd_value": null                    # fill later if you add pricing
}

Notes:
- You *must* provide the Pool or the AddressesProvider. This script does not hardcode addresses.
- Chunked eth_getLogs to stay within RPC limits; adjustable via --chunk-blocks.
- Decimals lookup is included (ERC20), but USD pricing is left as a post-process step.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any

from web3 import Web3, HTTPProvider
from web3._utils.events import get_event_data
from eth_abi import decode as abi_decode  # not strictly needed with ABI-based decode
from hexbytes import HexBytes

import pandas as pd

# -----------------------------
# ABIs
# -----------------------------

# Minimal ABI for Aave V3 PoolAddressesProvider to resolve Pool
ADDRESSES_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# Minimal ABI for the Aave V3 Pool's LiquidationCall event
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

ERC20_DECIMALS_ABI = [{
    "constant": True,
    "inputs": [],
    "name": "decimals",
    "outputs": [{"name": "", "type": "uint8"}],
    "payable": False,
    "stateMutability": "view",
    "type": "function"
}]

# -----------------------------
# Utils
# -----------------------------

def die(msg: str, code: int = 1):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(code)

def now_ts() -> int:
    return int(time.time())

def to_checksum(w3: Web3, addr: str) -> str:
    return Web3.to_checksum_address(addr)

def is_hex_address(x: str) -> bool:
    try:
        Web3.to_checksum_address(x)
        return True
    except Exception:
        return False

def ensure_out_dir():
    os.makedirs("out", exist_ok=True)

def get_block_timestamp(w3: Web3, block_number: int) -> int:
    return int(w3.eth.get_block(block_number)["timestamp"])

def date_from_ts(ts: int) -> datetime.date:
    return datetime.fromtimestamp(ts, tz=timezone.utc).date()

def find_block_by_timestamp(w3: Web3, target_ts: int, lo: int, hi: int) -> int:
    """
    Binary search approximate block whose timestamp >= target_ts.
    Assumes timestamps increase with block number.
    """
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
# Core
# -----------------------------

def resolve_pool_address(w3: Web3, address_provider: str) -> str:
    contract = w3.eth.contract(address=to_checksum(w3, address_provider), abi=ADDRESSES_PROVIDER_ABI)
    pool = contract.functions.getPool().call()
    if int(pool, 16) == 0:
        die("getPool() returned zero address – is the address provider correct for Ethereum mainnet?")
    return to_checksum(w3, pool)

def fetch_liquidations(
    w3: Web3,
    pool_addr: str,
    from_block: int,
    to_block: int,
    chunk: int = 120_000
):
    """
    Yield decoded LiquidationCall events from Aave V3 Pool in [from_block, to_block]
    """
    pool = w3.eth.contract(address=to_checksum(w3, pool_addr), abi=[{"type": "event", **POOL_LIQUIDATION_EVENT_ABI}])
    ev = pool.events.LiquidationCall()

    start = from_block
    while start <= to_block:
        end = min(to_block, start + chunk)
        logs = ev.get_logs(from_block=start, to_block=end)
        for log in logs:
            yield log
        start = end + 1

def normalize_event(w3: Web3, log) -> Dict[str, Any]:
    decoded = get_event_data(w3.codec, POOL_LIQUIDATION_EVENT_ABI, log)
    args = decoded["args"]
    block = log["blockNumber"]
    ts = get_block_timestamp(w3, block)

    return {
        "protocol": "aave",
        "version": "v3",
        "chain": "ethereum",
        "tx_hash": log["transactionHash"].hex(),
        "log_index": int(log["logIndex"]),
        "block_number": int(block),
        "timestamp": int(ts),
        "borrower": str(args["user"]),
        "liquidator": str(args["liquidator"]),
        "collateral_token": to_checksum(w3, args["collateralAsset"]),
        "debt_token": to_checksum(w3, args["debtAsset"]),
        "collateral_amount": str(int(args["liquidatedCollateralAmount"])),
        "debt_repaid": str(int(args["debtToCover"])),
        "receive_a_token": bool(args["receiveAToken"]),
        "usd_value": None,  # fill in a separate pricing step
    }

def lookup_decimals(w3: Web3, token_addr: str, cache: Dict[str, int]) -> int:
    if token_addr in cache:
        return cache[token_addr]
    try:
        erc = w3.eth.contract(address=to_checksum(w3, token_addr), abi=ERC20_DECIMALS_ABI)
        dec = erc.functions.decimals().call()
        cache[token_addr] = int(dec)
        return int(dec)
    except Exception:
        cache[token_addr] = 18  # default guess
        return 18

def aggregate_daily(events_df: pd.DataFrame) -> pd.DataFrame:
    if events_df.empty:
        return pd.DataFrame(columns=[
            "protocol", "version", "chain", "date",
            "collateral_token", "debt_token",
            "liquidations_count", "sum_collateral_raw", "sum_debt_repaid_raw"
        ])

    events_df["date"] = pd.to_datetime(events_df["timestamp"], unit="s", utc=True).dt.date
    grp = (
        events_df
        .groupby(["protocol","version","chain","date","collateral_token","debt_token"], as_index=False)
        .agg(
            liquidations_count=("tx_hash","nunique"),
            sum_collateral_raw=("collateral_amount", lambda s: s.astype("int64").sum() if len(s) else 0),
            sum_debt_repaid_raw=("debt_repaid", lambda s: s.astype("int64").sum() if len(s) else 0),
        )
    )
    return grp

def main():
    ap = argparse.ArgumentParser(description="Fetch Aave V3 (Ethereum) liquidation events and aggregate daily.")
    ap.add_argument("--rpc", default=os.environ.get("RPC_URL"), help="Ethereum RPC URL (env RPC_URL if omitted)")
    ap.add_argument("--pool", help="Aave V3 Pool address (preferred).")
    ap.add_argument("--address-provider", dest="addr_provider", help="PoolAddressesProvider (if you want to resolve Pool).")
    ap.add_argument("--from-block", type=str, help="Start block (int) or 'latest' (mutually exclusive with --from-date).")
    ap.add_argument("--to-block", type=str, default="latest", help="End block (int) or 'latest' (mutually exclusive with --to-date).")
    ap.add_argument("--from-date", type=str, help="YYYY-MM-DD (UTC). Mutually exclusive with --from-block.")
    ap.add_argument("--to-date", type=str, help="YYYY-MM-DD (UTC). Mutually exclusive with --to-block.")
    ap.add_argument("--chunk-blocks", type=int, default=120_000, help="Blocks per getLogs chunk.")
    ap.add_argument("--write-csv", action="store_true", help="Also write CSV alongside Parquet.")
    args = ap.parse_args()

    if not args.rpc:
        die("Missing RPC URL. Pass --rpc or set RPC_URL env var.")

    w3 = Web3(HTTPProvider(args.rpc, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        die("Web3 connection failed. Check RPC URL / key.")

    pool_addr = None
    if args.pool:
        if not is_hex_address(args.pool):
            die("--pool is not a valid hex address.")
        pool_addr = to_checksum(w3, args.pool)
    elif args.addr_provider:
        if not is_hex_address(args.addr_provider):
            die("--address-provider is not a valid hex address.")
        pool_addr = resolve_pool_address(w3, args.addr_provider)
        print(f"[info] Resolved Pool via AddressesProvider: {pool_addr}")
    else:
        die("Provide either --pool or --address-provider.")

    # Determine block range
    latest = w3.eth.block_number
    # Optional: estimate earliest safe historical block to constrain binary searches
    earliest = 12_000_000  # rough default; edit if needed

    if args.from_block and args.from_date:
        die("Use either --from-block or --from-date, not both.")
    if args.to_block and args.to_date:
        # allow both if to_block is default 'latest' and to_date supplied; we'll override
        pass

    if args.from_date:
        ts = int(datetime.fromisoformat(args.from_date).replace(tzinfo=timezone.utc).timestamp())
        from_block = find_block_by_timestamp(w3, ts, earliest, latest)
    else:
        from_block = latest if args.from_block == "latest" else int(args.from_block)

    if args.to_date:
        ts2 = int(datetime.fromisoformat(args.to_date).replace(tzinfo=timezone.utc).timestamp())
        to_block = find_block_by_timestamp(w3, ts2, from_block, latest)
    else:
        to_block = latest if args.to_block == "latest" else int(args.to_block)

    if from_block > to_block:
        die(f"from_block {from_block} > to_block {to_block}")

    print(f"[info] Scanning LiquidationCall on Pool {pool_addr} blocks [{from_block}, {to_block}] ...")

    ensure_out_dir()

    # Fetch
    logs_iter = fetch_liquidations(
        w3=w3,
        pool_addr=pool_addr,
        from_block=from_block,
        to_block=to_block,
        chunk=args.chunk_blocks,
    )

    rows = []
    seen = set()  # (tx_hash, log_index)
    for log in logs_iter:
        row = normalize_event(w3, log)
        key = (row["tx_hash"], row["log_index"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)

    events_df = pd.DataFrame(rows, columns=[
        "protocol","version","chain","tx_hash","log_index","block_number","timestamp",
        "borrower","liquidator","collateral_token","debt_token",
        "collateral_amount","debt_repaid","receive_a_token","usd_value"
    ])

    # Persist raw events
    events_path_parquet = "out/events.parquet"
    events_df.to_parquet(events_path_parquet, index=False)
    if args.write_csv:
        events_df.to_csv("out/events.csv", index=False)
    print(f"[ok] Wrote {len(events_df)} events → {events_path_parquet}")

    # Aggregate daily
    daily_df = aggregate_daily(events_df)
    daily_path_parquet = "out/daily.parquet"
    daily_df.to_parquet(daily_path_parquet, index=False)
    if args.write_csv:
        daily_df.to_csv("out/daily.csv", index=False)
    print(f"[ok] Wrote daily aggregates ({len(daily_df)} rows) → {daily_path_parquet}")

    print("\nNext steps:")
    print("  • (Optional) Join per-token decimals/symbols and compute human units.")
    print("  • (Optional) Add USD pricing by day/block and compute USD liquidation volume per day.")
    print("  • Reuse this schema for other CSUs (protocol×chain×version) by swapping adapter/addresses.")

if __name__ == "__main__":
    main()
