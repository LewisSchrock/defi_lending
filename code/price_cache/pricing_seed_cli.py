# pricing_seed_cli.py
# CLI to (a) optionally emit missing_* request files from an events CSV,
# then (b) seed the pricing cache from pricing/requests using CoinGecko.

import argparse
from pathlib import Path
from pricing_cache import (
    load_registry,
    write_registry_atomic,
    discover_addresses_from_events,
    ensure_price_ids,
    emit_missing_requests_for_events,
    seed_requests_from_folder,
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events_csv", type=Path, help="optional: events CSV to scan for tokens/timestamps")
    ap.add_argument("--token_registry", type=Path, default=Path("token_registry.yaml"))
    ap.add_argument("--chain", required=True)
    ap.add_argument("--cache_dir", type=Path, default=Path("pricing"))
    ap.add_argument("--requests_dir", type=Path, default=Path("pricing/requests"))
    ap.add_argument("--tolerance_sec", type=int, default=3600, help="asof tolerance for seeding cache")
    ap.add_argument("--emit_missing", action="store_true", help="emit missing_*.csv from events first")
    args = ap.parse_args()

    reg = load_registry(args.token_registry)

    if args.events_csv and args.emit_missing:
        # ensure price_ids for discovered addresses (helps avoid repeats)
        addrs = discover_addresses_from_events(args.events_csv)
        if addrs:
            reg = ensure_price_ids(args.token_registry, reg, args.chain, addrs)
        emit_missing_requests_for_events(
            events_csv=args.events_csv,
            cache_dir=args.cache_dir,
            requests_dir=args.requests_dir,
            chain=args.chain,
        )

    # Now seed all request files for this chain
    seed_requests_from_folder(
        reg=reg,
        reg_path=args.token_registry,
        requests_dir=args.requests_dir,
        cache_dir=args.cache_dir,
        chain=args.chain,
        base_tolerance_sec=args.tolerance_sec,
    )

if __name__ == "__main__":
    main()