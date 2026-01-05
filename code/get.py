#!/usr/bin/env python3
"""
Orchestrator: run TVL + liquidations for a single protocol/chain combo.
"""

import subprocess
from datetime import datetime, timedelta

# === CONFIG YOU WILL EDIT ===
PROTOCOL = "Aave V3"
CHAIN = "polygon"
RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/cEHzRdgL5rGydq_YIokK2"

# How many days of liquidations you want (back from today, inclusive of today)
DAYS_BACK = 3
# ============================


def main():
    today = datetime.utcnow().date()
    from_date = today - timedelta(days=DAYS_BACK)
    to_date = today

    # --- 1) TVL run ---
    # This just uses your existing tvl CLI; no dates needed because tvl.py
    # uses as-of pricing (asof_ts) internally.
    tvl_cmd = [
        "python3",
        "tvl.py",
        "--protocol", PROTOCOL,
        "--chain", CHAIN,
        "--rpc", RPC_URL,
        # Uncomment if you want to avoid writing until you’re happy:
        # "--no-write",
    ]

    print("\n=== Running TVL ===")
    print(" ".join(tvl_cmd))
    subprocess.run(tvl_cmd, check=True)

    # --- 2) Liquidations run ---
    # Adjust the flag names here to match liquid/main.py exactly.
    # I’m assuming it wants --from and --to as YYYY-MM-DD.
    liq_cmd = [
        "python3",
        "liquid/main.py",
        "--protocol", PROTOCOL,
        "--chain", CHAIN,
        "--rpc", RPC_URL,
        "--from", from_date.isoformat(),
        "--to", to_date.isoformat(),
        # Add any other flags your liquid main expects, e.g.:
        # "--no-write",
    ]

    print("\n=== Running liquidations ===")
    print(" ".join(liq_cmd))
    subprocess.run(liq_cmd, check=True)

    print("\n✅ Done: TVL + liquid run finished.")


if __name__ == "__main__":
    main()