#!/usr/bin/env python3
"""
add_cache_pricing.py

Ensure the local pricing cache has USD prices for ANY token that currently has
missing-timestamp requests. This is called after we pull liquidation data and
see gaps (i.e., files in pricing/requests/missing_{chain}_{addr}.csv).

Behavior:
- Scan pricing/requests/ for missing_*.csv files
- For each {chain, addr}, read price_id from token_registry.yaml
- Fetch ONE CoinGecko range [min_ts, max_ts] per token (polite rate limiting)
- Nearest-previous match to requested timestamps (integer tolerance)
- Merge into pricing/{chain}_{addr}.csv (dedup by timestamp)

Run from repo root:
    python3 add_cache_pricing.py
"""
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests
import yaml

# --------------------------- Paths & Settings -------------------------------
ROOT = Path.cwd()
REQUESTS_DIR = ROOT / "pricing" / "requests"
CACHE_DIR = ROOT / "pricing"
REG_PATH = ROOT / "token_registry.yaml"

ASOF_TOLERANCE_SEC = 3600  # 1h as-of tolerance for int-second joins

# polite rate limiting per domain (seconds between calls)
_LAST_CALL: Dict[str, float] = {}
_MIN_INTERVAL = {"coingecko": 1.2}

def _rate_limit(key: str) -> None:
    now = time.time()
    last = _LAST_CALL.get(key, 0.0)
    delay = max(0.0, _MIN_INTERVAL.get(key, 0.0) - (now - last))
    if delay > 0:
        time.sleep(delay)
    _LAST_CALL[key] = time.time()

# --------------------------- Helpers ---------------------------------------

def parse_request_filename(p: Path) -> Tuple[str, str]:
    """Parse pricing/requests/missing_{chain}_{addr}.csv robustly (no regex)."""
    name = p.name
    if not name.startswith("missing_") or not name.endswith(".csv"):
        raise ValueError(f"bad request filename: {p}")
    core = name[len("missing_"):-4]
    if "_" not in core:
        raise ValueError(f"bad request filename: {p}")
    chain, addr = core.split("_", 1)
    addr = addr.lower()
    if not (addr.startswith("0x") and len(addr) == 42 and all(c in "0123456789abcdef" for c in addr[2:])):
        raise ValueError(f"bad request filename: {p}")
    return chain, addr


def load_registry() -> Dict[str, dict]:
    if not REG_PATH.exists():
        print(f"[error] token registry not found: {REG_PATH}")
        sys.exit(1)
    reg = yaml.safe_load(REG_PATH.read_text()) or {}
    # normalize keys to lowercase addresses
    return {(k.lower() if isinstance(k, str) else k): v for k, v in reg.items()}


def get_price_source(reg: Dict[str, dict], addr: str) -> Tuple[str, str]:
    meta = reg.get(addr, {}) if isinstance(reg, dict) else {}
    pid = meta.get("price_id") if isinstance(meta, dict) else None
    if not pid or ":" not in pid:
        raise KeyError(f"no price_id for {addr}; add e.g. coingecko:weth in token_registry.yaml")
    src, ident = pid.split(":", 1)
    return src, ident


def fetch_coingecko_range(coin_id: str, t_from: int, t_to: int) -> pd.DataFrame:
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {"vs_currency": "usd", "from": int(t_from), "to": int(t_to)}
    _rate_limit("coingecko")
    r = requests.get(url, params=params, timeout=45)
    if r.status_code == 429:
        time.sleep(2.5)
        _rate_limit("coingecko")
        r = requests.get(url, params=params, timeout=45)
    r.raise_for_status()
    data = r.json()
    if "prices" not in data or not data["prices"]:
        return pd.DataFrame(columns=["timestamp", "price_usd"]).astype({"timestamp": "int64", "price_usd": "float64"})
    px = pd.DataFrame(data["prices"], columns=["ms", "price_usd"])  # ms precision
    px["timestamp"] = (px["ms"] // 1000).astype("int64")
    px = px[["timestamp", "price_usd"]].dropna().drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    return px


def asof_fill(need_ts: pd.Series, px: pd.DataFrame, tolerance_sec: int) -> pd.DataFrame:
    out = need_ts.to_frame(name="timestamp").dropna().astype({"timestamp": "int64"}).sort_values("timestamp")
    if px.empty:
        out["price_usd"] = pd.NA
        return out
    px_sorted = px.rename(columns={"timestamp": "px_ts"}).sort_values("px_ts")
    joined = pd.merge_asof(
        out,
        px_sorted,
        left_on="timestamp",
        right_on="px_ts",
        direction="backward",
        tolerance=int(tolerance_sec),  # integer tolerance for int keys
    ).drop(columns=["px_ts"])
    return joined


def merge_into_cache(chain: str, addr: str, filled: pd.DataFrame) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_cache = CACHE_DIR / f"{chain}_{addr.lower()}.csv"
    filled = filled.dropna(subset=["price_usd"]).astype({"timestamp": "int64"}).sort_values("timestamp")
    if out_cache.exists():
        existing = pd.read_csv(out_cache)
        if not existing.empty and not pd.api.types.is_integer_dtype(existing["timestamp"]):
            existing["timestamp"] = pd.to_datetime(existing["timestamp"], utc=True).astype("int64") // 10**9
        merged = pd.concat([existing, filled], ignore_index=True)
        merged = merged.drop_duplicates(subset=["timestamp"], keep="last").sort_values("timestamp")
    else:
        merged = filled
    merged.to_csv(out_cache, index=False)
    return out_cache

# --------------------------- Main ------------------------------------------

def main() -> None:
    reg = load_registry()
    if not REQUESTS_DIR.exists():
        print(f"[info] no request dir at {REQUESTS_DIR}; nothing to do")
        return
    req_files = sorted(REQUESTS_DIR.glob("missing_*.csv"))
    if not req_files:
        print("[info] no missing_* request files found; cache is up-to-date")
        return

    print(f"[info] found {len(req_files)} request file(s)")
    for p in req_files:
        try:
            chain, addr = parse_request_filename(p)
            need = pd.read_csv(p)
            if need.empty or "timestamp" not in need.columns:
                print(f"[skip] {p.name} has no timestamps")
                continue
            need_ts = need["timestamp"].dropna().astype("int64")
            t_from, t_to = int(need_ts.min()), int(need_ts.max())

            src, ident = get_price_source(reg, addr)
            if src == "coingecko":
                px = fetch_coingecko_range(ident, t_from, t_to)
            else:
                print(f"[warn] unsupported price source '{src}' for {addr}; skipping")
                continue

            filled = asof_fill(need_ts, px, ASOF_TOLERANCE_SEC)
            missing = int(filled["price_usd"].isna().sum())
            if missing:
                print(f"[warn] {p.name}: {missing} / {len(filled)} timestamps had no prior price within {ASOF_TOLERANCE_SEC}s")

            out = merge_into_cache(chain, addr, filled)
            wrote = len(filled) - missing
            print(f"[ok] cached {wrote} prices → {out}")
        except KeyError as e:
            print(f"[registry] {e}")
        except requests.HTTPError as e:
            print(f"[http] {p.name}: {e}")
        except Exception as e:
            print(f"[error] {p.name}: {e}")

if __name__ == "__main__":
    main()