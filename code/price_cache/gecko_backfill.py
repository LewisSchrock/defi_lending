# gecko_backfill.py
# Offline CoinGecko backfill: fulfill missing_* request files into the pricing cache.

import argparse
from pathlib import Path

from pricing_cache import load_registry, seed_requests_from_folder


def main():
    ap = argparse.ArgumentParser(
        description="Backfill CoinGecko prices from missing_* request files into the pricing cache."
    )
    ap.add_argument(
        "--chain",
        required=True,
        help="Chain name used in request/cache filenames (e.g. ethereum, polygon, arbitrum-one)",
    )
    ap.add_argument(
        "--registry",
        default="token_registry.yaml",
        help="Path to token registry YAML (default: token_registry.yaml)",
    )
    ap.add_argument(
        "--cache-dir",
        default="pricing",
        help="Directory where per-token price CSVs live (default: pricing)",
    )
    ap.add_argument(
        "--requests-dir",
        default="pricing/requests",
        help="Directory containing missing_* request CSVs (default: pricing/requests)",
    )
    ap.add_argument(
        "--tolerance-sec",
        type=int,
        default=3600,
        help="Base as-of tolerance in seconds (default: 3600)",
    )
    args = ap.parse_args()

    reg_path = Path(args.registry)
    cache_dir = Path(args.cache_dir)
    requests_dir = Path(args.requests_dir)

    print(f"[backfill] registry={reg_path} cache_dir={cache_dir} requests_dir={requests_dir} chain={args.chain}")

    # Load registry once; seed_requests_from_folder will update/write as needed.
    reg = load_registry(reg_path)

    seed_requests_from_folder(
        reg=reg,
        reg_path=reg_path,
        requests_dir=requests_dir,
        cache_dir=cache_dir,
        chain=args.chain,
        base_tolerance_sec=args.tolerance_sec,
    )

    print("[backfill] done")


if __name__ == "__main__":
    main()