#!/usr/bin/env python3
#cEHzRdgL5rGydq_YIokK2

"""
RPC-centric pull of Aave v3 (Ethereum) liquidation events for a UTC date window.
- Uses known Pool proxy (no registry).
- Converts date → block via binary search.
- Calls eth_getLogs with hex fromBlock/toBlock, chunked.
- Decodes LiquidationCall via ABI, fetches block timestamps, writes CSV.
"""

import os, sys, argparse, csv, math, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from web3 import Web3, HTTPProvider
from eth_utils import keccak

PACE_S = float(os.environ.get("PACE_S", "0"))  # set >0 (e.g., 0.01) if you want gentle pacing

# ---- Config ----
POOL = Web3.to_checksum_address("0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2")  # Aave v3 Pool proxy (ETH)
EVENT_SIG = "LiquidationCall(address,address,address,uint256,uint256,address,bool)"
TOPIC0 = keccak(text=EVENT_SIG).hex()
CHUNK = 10  # Alchemy Free tier requires <=10-block ranges for eth_getLogs
RPC = os.environ.get("ETH_RPC", "").strip()

# Minimal ABI only for decoding the event
EVENT_ABI = [{
    "anonymous": False,
    "inputs": [
        {"indexed": True,  "name": "collateralAsset", "type": "address"},
        {"indexed": True,  "name": "debtAsset",       "type": "address"},
        {"indexed": True,  "name": "user",            "type": "address"},
        {"indexed": False, "name": "debtToCover",     "type": "uint256"},
        {"indexed": False, "name": "liquidatedCollateralAmount", "type": "uint256"},
        {"indexed": False, "name": "liquidator",      "type": "address"},
        {"indexed": False, "name": "receiveAToken",   "type": "bool"},
    ],
    "name": "LiquidationCall",
    "type": "event",
}]

def die(msg): print(msg, file=sys.stderr); sys.exit(1)

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-date", help="UTC, inclusive (YYYY-MM-DD). Default: yesterday", default=None)
    ap.add_argument("--to-date",   help="UTC, exclusive (YYYY-MM-DD). Default: today",     default=None)
    ap.add_argument("--decode-from-raw", help="Path to raw NDJSON to decode instead of doing RPC fetch", default=None)
    return ap.parse_args()

def utc_midnight(d): return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

def compute_window(args):
    if args.from_date and args.to_date:
        d0 = datetime.fromisoformat(args.from_date).date()
        d1 = datetime.fromisoformat(args.to_date).date()
    else:
        today = datetime.now(timezone.utc).date()
        d0 = today - timedelta(days=1)
        d1 = today
    t0 = int(utc_midnight(d0).timestamp())
    t1 = int(utc_midnight(d1).timestamp())
    return (d0, d1, t0, t1)

def connect():
    if not RPC:
        die("[error] ETH_RPC not set. export ETH_RPC='https://eth-mainnet.g.alchemy.com/v2/KEY'")
    w3 = Web3(HTTPProvider(RPC, request_kwargs={"timeout": 30}))
    if not w3.is_connected(): die("[error] Web3 not connected; check ETH_RPC/key.")
    if w3.eth.chain_id != 1: die(f"[error] Wrong chainId={w3.eth.chain_id}; need 1 (Ethereum).")
    return w3

def block_for_ts(w3, ts):
    lo, hi = 1, w3.eth.block_number
    ans = hi
    while lo <= hi:
        mid = (lo + hi) // 2
        t = w3.eth.get_block(mid)["timestamp"]
        if t >= ts:
            ans = mid
            hi = mid - 1
        else:
            lo = mid + 1
    return ans

def hex0(x): return hex(int(x))

def get_logs_chunked(w3, addr, topic0, b0, b1, raw_out_path, progress_path):
    got = []
    start = b0
    import json
    raw_f = open(raw_out_path, "a", buffering=1)
    def write_progress(_start, _end, _accum):
        try:
            with open(progress_path, "w") as pf:
                pf.write(json.dumps({
                    "from_block": b0,
                    "to_block": b1,
                    "current_start": _start,
                    "current_end": _end,
                    "accumulated_logs": _accum,
                    "ts": int(time.time())
                }))
        except Exception:
            pass
    while start <= b1:
        end = min(start + CHUNK - 1, b1)
        if (start - b0) % (200 * CHUNK) == 0:
            print(f"[info] scanning window {start}-{end} (accumulated logs: {len(got)})")
            write_progress(start, end, len(got))
        flt = {
            "fromBlock": hex0(start),
            "toBlock":   hex0(end),
            "address":   addr,
            "topics":    [topic0]
        }
        r = w3.provider.make_request("eth_getLogs", [flt])
        if "error" in r:
            msg = r["error"].get("message", "")
            print(f"[warn] getLogs error on {start}-{end}: {msg}")
            # Enforce 10-block maximum per request (Alchemy Free)
            if (end - start + 1) > 10:
                end = start + 9
                continue
            # Already at 10-block window and still failing: advance and continue
            start = end + 1
            if PACE_S > 0:
                time.sleep(PACE_S)
            continue
        res = r.get("result", [])
        # Persist raw logs immediately (NDJSON) to avoid data loss
        for L in res:
            raw_f.write(json.dumps(L) + "\n")
        got.extend(res)
        # Advance window
        start = end + 1
        # Optional pacing
        if PACE_S > 0:
            time.sleep(PACE_S)
    try:
        raw_f.close()
    except Exception:
        pass
    return got

def main():
    args = parse_args()
    d0, d1, t0, t1 = compute_window(args)
    print(f"[info] window UTC: {d0} → {d1}  (ts {t0}..{t1})")
    w3 = connect()

    # sanity: Pool has code
    code_len = len(w3.eth.get_code(POOL))
    print("[info] Pool code bytes:", code_len)
    if code_len == 0: die("[error] Pool has no code on this RPC. Check ETH_RPC.")

    # date → block
    b0 = block_for_ts(w3, t0)
    b1 = block_for_ts(w3, t1)
    # widen slightly to be safe on edges
    b0 = max(1, b0 - 500)
    b1 = min(w3.eth.block_number, b1 + 500)
    if b0 > b1: die(f"[error] bad block window: {b0}>{b1}")
    print(f"[info] scanning blocks {b0:,}..{b1:,}  (~{b1-b0+1:,} blocks)")

    outdir = Path("out/aave_v3_ethereum")
    outdir.mkdir(parents=True, exist_ok=True)
    raw_path = outdir / "liquidation_events.raw.ndjson"
    progress_path = outdir / "liquidation_events.progress.json"
    # Initialize progress file
    try:
        import json
        with open(progress_path, "w") as pf:
            pf.write(json.dumps({
                "from_block": b0,
                "to_block": b1,
                "current_start": b0,
                "current_end": b0,
                "accumulated_logs": 0,
                "ts": int(time.time())
            }))
    except Exception:
        pass

    logs = None
    if args.decode_from_raw:
        import json
        raw_file_to_read = args.decode_from_raw
        if raw_file_to_read == "auto":
            raw_file_to_read = str(Path("out/aave_v3_ethereum") / "liquidation_events.raw.ndjson")
        print(f"[info] decoding from raw file: {raw_file_to_read}")
        logs = []
        with open(raw_file_to_read, "r") as rf:
            for line in rf:
                if line.strip():
                    logs.append(json.loads(line))

    # fetch logs
    if logs is None:
        # fetch logs via RPC and persist raw incrementally
        logs = get_logs_chunked(w3, POOL, TOPIC0, b0, b1, str(raw_path), str(progress_path))
    print(f"[ok] logs fetched: {len(logs)}")

    # decode via ABI using Web3’s event processor (v6-safe, with v5 fallback)
    ev = w3.eth.contract(address=POOL, abi=[{"type":"event", **EVENT_ABI[0]}]).events.LiquidationCall()
    ts_cache = {}
    out_rows = []
    for i, L in enumerate(logs, 1):
        log_input = {
            # Prefer the actual address from the log (should be the Pool proxy, but we don't hardcode)
            "address": Web3.to_checksum_address(L.get("address", str(POOL))),
            "data": L["data"],
            "topics": L["topics"],
            # Convert common hex fields to ints for web3.py v6 event processor
            "blockNumber": int(L["blockNumber"], 16) if isinstance(L.get("blockNumber"), str) else L.get("blockNumber"),
            "logIndex": int(L["logIndex"], 16) if isinstance(L.get("logIndex"), str) else L.get("logIndex"),
            "transactionIndex": int(L["transactionIndex"], 16) if isinstance(L.get("transactionIndex"), str) else L.get("transactionIndex"),
            # Hashes can be hex strings; web3 will handle HexBytes internally
            "blockHash": L.get("blockHash"),
            "transactionHash": L.get("transactionHash"),
            # Optional but harmless; some providers include it
            "removed": L.get("removed", False),
        }
        try:
            decoded = ev.process_log(log_input)   # web3.py v6
        except Exception as e:
            # Most common here is a topic-count mismatch if ABI is wrong; skip and continue
            if (i % 50) == 0:
                print(f"[warn] decode skipped at block {log_input['blockNumber']} logIndex {log_input.get('logIndex')}: {e}")
            continue
        args = decoded["args"]
        blk = log_input["blockNumber"]
        if blk not in ts_cache:
            ts_cache[blk] = w3.eth.get_block(blk)["timestamp"]
        out_rows.append({
            "timestamp": ts_cache[blk],
            "block_number": blk,
            "tx_hash": log_input["transactionHash"],
            "collateral_token": args["collateralAsset"],
            "debt_token": args["debtAsset"],
            "user": args["user"],
            "debt_repaid": int(args["debtToCover"]),
            "collateral_amount": int(args["liquidatedCollateralAmount"]),
            "liquidator": args["liquidator"],
            "receive_a_token": bool(args["receiveAToken"]),
        })
        if i % 200 == 0:
            print(f"[info] decoded rows: {i}")

    outp = outdir / "liquidation_events.csv"
    with open(outp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "timestamp","block_number","tx_hash",
            "collateral_token","debt_token",
            "debt_repaid","collateral_amount",
            "user","liquidator","receive_a_token"
        ])
        w.writeheader()
        for r in out_rows: w.writerow(r)

    print(f"[ok] wrote {outp}  rows={len(out_rows)}")
    if not out_rows:
        print("[note] 0 logs in this window can be normal on quiet days. If needed, expand the window (e.g., --from-date 2025-11-01 --to-date 2025-11-06).")

if __name__ == "__main__":
    main()