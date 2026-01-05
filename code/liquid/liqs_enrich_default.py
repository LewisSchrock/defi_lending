# liqs_enrich_default.py
# Calls into pricing_cache to ensure price_ids, emit request files, seed cache,
# then runs your existing liqs_to_daily_usd.py for enrichment + daily USD.

import sys, subprocess
from pathlib import Path
from pricing_cache import (
    load_registry,
    ensure_price_ids,
    discover_addresses_from_events,
    emit_missing_requests_for_events,
    seed_requests_from_folder,
)

ROOT = Path.cwd()
EVENTS   = ROOT / "out" / "aave_v3_ethereum" / "liquidation_events.csv"
TOKENREG = ROOT / "token_registry.yaml"
CHAIN    = "ethereum"
ENRICHED = ROOT / "out" / "aave_v3_ethereum" / "liquidation_events_enriched.csv"
DAILY    = ROOT / "out" / "aave_v3_ethereum" / "liquidations_daily_usd.csv"

CACHE_DIR    = ROOT / "pricing"
REQUESTS_DIR = ROOT / "pricing" / "requests"
ASOF_TOLERANCE_SEC = 3600

def main():
    if not EVENTS.exists():
        print(f"[error] expected events at {EVENTS} but not found.")
        sys.exit(1)

    # -------- PRICING HOOKS (independent & reusable) --------
    reg = load_registry(TOKENREG)

    # (1) Discover any token addresses in events and ensure price_id in registry
    addrs = discover_addresses_from_events(EVENTS)
    if addrs:
        reg = ensure_price_ids(TOKENREG, reg, CHAIN, addrs)

    # (2) Emit/refresh missing_* request files based on events & existing cache
    emit_missing_requests_for_events(
        events_csv=EVENTS,
        cache_dir=CACHE_DIR,
        requests_dir=REQUESTS_DIR,
        chain=CHAIN,
    )

    # (3) Seed pricing cache for all request files for this chain
    seed_requests_from_folder(
        reg=reg,
        reg_path=TOKENREG,
        requests_dir=REQUESTS_DIR,
        cache_dir=CACHE_DIR,
        chain=CHAIN,
        base_tolerance_sec=ASOF_TOLERANCE_SEC,
    )
    # -------- End PRICING HOOKS --------

    # Now call your existing enrichment → daily aggregation
    cmd = [
        sys.executable,
        str(ROOT / "liqs_to_daily_usd.py"),
        "--events_csv", str(EVENTS),
        "--token_registry", str(TOKENREG),
        "--chain", CHAIN,
        "--out_enriched_csv", str(ENRICHED),
        "--out_daily_csv", str(DAILY),
        "--tolerance_sec", str(ASOF_TOLERANCE_SEC),
    ]
    print("[info] running:", " ".join(map(str, cmd)))
    rc = subprocess.call(cmd)
    sys.exit(rc)

if __name__ == "__main__":
    main()