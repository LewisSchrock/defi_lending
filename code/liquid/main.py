# liquid/main.py
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from liquid.adapters.aave_v3 import fetch_events # your extractor
from liquid.liqs_to_daily_usd import main as enrich_daily_cli  # reuse logic
from liquid.liqs_to_daily_usd import NY_TZ               # for consistency

def parse_date(d): return int(datetime.fromisoformat(d).replace(tzinfo=timezone.utc).timestamp())

def main():
    ap = argparse.ArgumentParser("Liquidations pipeline (extract → enrich → daily)")
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--chain", required=True)
    ap.add_argument("--rpc", required=True)
    ap.add_argument("--from", dest="from_date", required=True, help="YYYY-MM-DD (UTC)")
    ap.add_argument("--to", dest="to_date", required=True, help="YYYY-MM-DD (UTC)")
    ap.add_argument("--out-root", default="data/out")
    ap.add_argument("--token-registry", default="price_cache/token_registry.yaml")
    ap.add_argument("--tolerance-sec", type=int, default=600)
    ap.add_argument("--price-mode", choices=["cache"], default="cache")  # keep simple for now
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    ts_from, ts_to = parse_date(args.from_date), parse_date(args.to_date)
    # 1) Extract raw events (returns DataFrame)
    ev = fetch_events(rpc=args.rpc, chain=args.chain, ts_from=ts_from, ts_to=ts_to)

    # 2) Save to a temp CSV (reuse existing enrichment code as-is)
    tmp = Path(".tmp_events.csv")
    ev.to_csv(tmp, index=False)

    # 3) Call the enrichment/daily code through its CLI entry point
    import sys
    sys.argv = [
        "liqs_to_daily_usd.py",
        "--events_csv", str(tmp),
        "--protocol", args.protocol,
        "--token_registry", args.token_registry,
        "--chain", args.chain,
        "--tolerance_sec", str(args.tolerance_sec),
        "--out-root", args.out_root,
    ] + (["--no-write"] if args.no_write else [])
    enrich_daily_cli()

if __name__ == "__main__":
    main()