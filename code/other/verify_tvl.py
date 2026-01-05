#!/usr/bin/env python3
"""
Verify chain-level TVL for each protocol chain CSU using DeFiLlama.

Inputs:
  - data/meta/units.yaml   # your CSU roster
  - data/meta/llama_slugs.yaml  # optional: map protocol names to DeFiLlama slugs

Outputs:
  - data/meta/tvl_verification.parquet (and .csv)

Notes:
  - DeFiLlama endpoint used: https://api.llama.fi/protocol/{slug}
  - We attempt to read chain-level TVL from "chainTvls".
  - If a chain isn't present or TVL can't be parsed, we mark it "missing".
  - Threshold is configurable via CLI flag or DEFAULT_THRESHOLD below.
"""

import os
import sys
import json
import argparse
import requests
import pandas as pd
import yaml
from typing import Dict, Any

DEFAULT_UNITS_PATH = "data/meta/units.yaml"
DEFAULT_SLUGS_PATH = "data/meta/llama_slugs.yaml"
DEFAULT_OUT_DIR = "data/meta"
DEFAULT_THRESHOLD = 100_000_000  # $100m

LLAMA_PROTOCOL_ENDPOINT = "https://api.llama.fi/protocol/{slug}"

def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def save_df(df: pd.DataFrame, out_dir: str, basename: str):
    os.makedirs(out_dir, exist_ok=True)
    parquet_path = os.path.join(out_dir, f"{basename}.parquet")
    csv_path = os.path.join(out_dir, f"{basename}.csv")
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)
    print(f"[ok] wrote: {parquet_path}\n[ok] wrote: {csv_path}")

def get_llama_payload(slug: str) -> Dict[str, Any]:
    url = LLAMA_PROTOCOL_ENDPOINT.format(slug=slug)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()

def latest_chain_tvl_from_payload(payload: Dict[str, Any], chain_name: str):
    """
    DeFiLlama payload typically has a 'chainTvls' object where each key is a chain
    and the value is either:
      - number (current TVL), or
      - dict with keys like 'tvl' (a time series list of {date, totalLiquidityUSD} or similar)
    We try to coerce to a float.
    """
    chainTvls = payload.get("chainTvls") or {}
    if chain_name not in chainTvls:
        # Try case-insensitive match
        for k in list(chainTvls.keys()):
            if k.lower() == chain_name.lower():
                chain_name = k
                break
        else:
            return None  # not found

    v = chainTvls[chain_name]
    try:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, dict):
            # Some payloads have 'tvl' -> list of points, take the last non-null 'totalLiquidityUSD' or 'tvl'
            if "tvl" in v and isinstance(v["tvl"], list) and len(v["tvl"]) > 0:
                # entries might be like {'date': 1687737600, 'totalLiquidityUSD': 12345.0}
                # or [ts, value] pairs; handle both
                last = None
                for item in reversed(v["tvl"]):
                    if isinstance(item, dict):
                        val = item.get("totalLiquidityUSD") or item.get("tvl") or item.get("totalLiquidity")
                    elif isinstance(item, (list, tuple)) and len(item) >= 2:
                        val = item[1]
                    else:
                        val = None
                    if val is not None:
                        last = float(val)
                        break
                return last
            # Some payloads expose a direct number at v.get('tvl') or v.get('tvlUsd')
            for key in ("tvlUsd", "tvl", "totalLiquidityUSD", "totalLiquidity"):
                if key in v and isinstance(v[key], (int, float)):
                    return float(v[key])
        # Fallback: None if we can't interpret it
        return None
    except Exception:
        return None

def normalize_chain_label(ch: str) -> str:
    """Make chain labels consistent with DeFiLlama conventions where possible."""
    # Common normalizations
    m = {
        "ethereum": "Ethereum",
        "polygon": "Polygon",
        "arbitrum": "Arbitrum",
        "optimism": "Optimism",
        "base": "Base",
        "bsc": "BSC",
        "binance smart chain": "BSC",
        "avalanche": "Avalanche",
        "fantom": "Fantom",
        "tron": "Tron",
        "solana": "Solana",
    }
    return m.get(ch.lower(), ch)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", default=DEFAULT_UNITS_PATH, help="Path to units.yaml")
    ap.add_argument("--slugs", default=DEFAULT_SLUGS_PATH, help="Path to llama_slugs.yaml (protocol→slug)")
    ap.add_argument("--outdir", default=DEFAULT_OUT_DIR, help="Output directory for results")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="USD threshold for 'active'")
    args = ap.parse_args()

    # Load config files
    units_cfg = load_yaml(args.units)
    slug_map = {}
    if os.path.exists(args.slugs):
        slug_map = load_yaml(args.slugs) or {}

    units = units_cfg.get("units", [])
    rows = []

    for u in units:
        protocol = u["protocol"]
        variant  = u.get("variant", "")
        chain    = normalize_chain_label(u["chain"])
        key      = u["key"]

        # Lookup slug
        slug = slug_map.get(protocol)
        if not slug:
            # default guess: protocol name as slug
            slug = protocol.lower().replace(" ", "-")

        # Pull payload
        tvl_usd = None
        payload_ok = True
        try:
            payload = get_llama_payload(slug)
        except Exception as e:
            payload_ok = False
            payload = {"error": str(e)}

        if payload_ok:
            tvl_usd = latest_chain_tvl_from_payload(payload, chain)

        status = "active" if (tvl_usd is not None and tvl_usd >= args.threshold) else "review"

        rows.append({
            "unit_key": key,
            "protocol": protocol,
            "variant": variant,
            "chain": chain,
            "llama_slug": slug,
            "current_chain_tvl_usd": float(tvl_usd) if tvl_usd is not None else None,
            "status": status,
            "payload_ok": payload_ok
        })

    df = pd.DataFrame(rows).sort_values(["status", "protocol", "chain"])
    save_df(df, args.outdir, "tvl_verification")

    # Quick console summary
    active = (df["status"] == "active").sum()
    total  = len(df)
    print(f"\nSummary: {active}/{total} units >= ${args.threshold:,.0f} TVL (active).")
    missing = df["current_chain_tvl_usd"].isna().sum()
    if missing:
        print(f"Note: {missing} units missing chain-level TVL; inspect 'payload_ok' and 'llama_slug' mapping.")

if __name__ == "__main__":
    main()
