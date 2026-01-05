# pricing_cache.py
# Reusable CoinGecko-backed pricing cache with API-key auth, rate limiting,
# atomic registry writes, contract->price_id discovery, request-file seeding,
# and robust as-of joins.

from __future__ import annotations
import os, time, random
from pathlib import Path
from typing import Dict, Tuple, Iterable, Optional
from collections import OrderedDict
from collections.abc import Mapping

import pandas as pd
import numpy as np
# ---------- Request pruning ----------

def _prune_request_file(chain: str, addr: str, cache_dir: Path, requests_dir: Path) -> tuple[Path, int, int]:
    """Prune fulfilled timestamps from pricing/requests/missing_<chain>_<addr>.csv.
    A requested ts is fulfilled if the cache has any price with timestamp <= ts.
    Returns: (req_path, requested_count, remaining_count)
    """
    req_path = requests_dir / f"missing_{chain}_{addr}.csv"
    cache_path = cache_dir / f"{chain}_{addr}.csv"

    if not req_path.exists() or not cache_path.exists():
        return (req_path, 0, 0)

    try:
        req = pd.read_csv(req_path)
    except Exception:
        return (req_path, 0, 0)
    if "timestamp" not in req.columns or req.empty:
        return (req_path, 0, 0)

    try:
        cached = pd.read_csv(cache_path)
    except Exception:
        return (req_path, len(req), len(req))
    if cached.empty or "timestamp" not in cached.columns:
        return (req_path, len(req), len(req))

    r = pd.to_numeric(req["timestamp"], errors="coerce").dropna().astype("int64").to_numpy()
    c = pd.to_numeric(cached["timestamp"], errors="coerce").dropna().astype("int64").to_numpy()
    if c.size == 0:
        return (req_path, int(r.size), int(r.size))

    c.sort()
    # fulfilled if any cached ts <= r[i]
    idx = np.searchsorted(c, r, side="right")
    fulfilled_mask = idx > 0

    remaining_ts = r[~fulfilled_mask]

    if remaining_ts.size == 0:
        req_path.unlink(missing_ok=True)
        print(f"[cleanup] removed {req_path.name} (all timestamps fulfilled)")
        return (req_path, int(r.size), 0)

    remaining_df = (
        pd.DataFrame({"timestamp": remaining_ts})
        .drop_duplicates()
        .sort_values("timestamp")
    )
    tmp = req_path.with_suffix(req_path.suffix + ".tmp")
    remaining_df.to_csv(tmp, index=False)
    tmp.replace(req_path)
    print(f"[cleanup] updated {req_path.name}: {len(remaining_df)} timestamps remain")
    return (req_path, int(r.size), int(len(remaining_df)))
import requests
import yaml

# Ensure PyYAML can serialize OrderedDict cleanly
yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_dict(data.items()))

# ---------- Configuration ----------
COINGECKO_PLATFORM = {
    "ethereum": "ethereum",
    "polygon": "polygon-pos",
    "polygon-pos": "polygon-pos",
    "arbitrum": "arbitrum-one",
    "arbitrum-one": "arbitrum-one",
    "optimism": "optimistic-ethereum",
    "base": "base",
    "avalanche": "avalanche",
    "bsc": "binance-smart-chain",
}

 # Load CoinGecko API configuration from config/api.yaml, with env as fallback.
from pathlib import Path as _Path

def _load_cg_config():
    """
    Load CoinGecko configuration from config/api.yaml.
    Precedence:
      1) Environment variables (if set)
      2) config/api.yaml values
      3) Hardcoded defaults
    """
    # Start from environment (so you can still override config if needed)
    pro  = os.getenv("COINGECKO_PRO_API_KEY", "").strip()
    demo = os.getenv("COINGECKO_DEMO_API_KEY", "").strip()
    min_interval = None
    env_min = os.getenv("COINGECKO_MIN_INTERVAL_SEC", "").strip()
    if env_min:
        try:
            min_interval = float(env_min)
        except Exception:
            min_interval = None

    cfg_path = _Path(__file__).resolve().parent.parent / "config" / "api.yaml"
    try:
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text()) or {}
            # Config wins over env if present
            if "coingecko_pro_api_key" in cfg:
                pro = (cfg.get("coingecko_pro_api_key") or "").strip()
            if "coingecko_demo_api_key" in cfg:
                demo = (cfg.get("coingecko_demo_api_key") or "").strip()
            if "coingecko_min_interval_sec" in cfg and min_interval is None:
                try:
                    min_interval = float(cfg["coingecko_min_interval_sec"])
                except Exception:
                    pass
    except Exception as e:
        print(f"[warn] failed to read {cfg_path}: {e}")

    return pro, demo, min_interval

CG_PRO_KEY, CG_DEMO_KEY, _MIN_PER_CALL = _load_cg_config()

CG_BASE = "https://pro-api.coingecko.com/api/v3" if CG_PRO_KEY else "https://api.coingecko.com/api/v3"

# Default pacing: Demo ≈ 30/min → ~2.2s; Pro Analyst 250/min → ~0.24s.
_MIN_INTERVAL = (
    _MIN_PER_CALL
    if _MIN_PER_CALL is not None
    else (0.24 if CG_PRO_KEY else 2.2)
)

_LAST_CALL: Dict[str, float] = {}

def _rate_limit(key: str = "coingecko") -> None:
    now = time.time()
    last = _LAST_CALL.get(key, 0.0)
    delay = max(0.0, _MIN_INTERVAL - (now - last))
    if delay > 0:
        time.sleep(delay)
    _LAST_CALL[key] = time.time()

def _cg_headers() -> dict:
    if CG_PRO_KEY:
        return {"x-cg-pro-api-key": CG_PRO_KEY}
    if CG_DEMO_KEY:
        return {"x-cg-demo-api-key": CG_DEMO_KEY}
    return {}

# ---------- Registry helpers ----------
def load_registry(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    reg_raw = yaml.safe_load(path.read_text()) or {}
    # Force all keys to lowercase strings and values to plain dicts to avoid mixed-type and representer issues
    reg: Dict[str, dict] = {str(k).lower(): (dict(v) if isinstance(v, Mapping) else v) for k, v in reg_raw.items()}
    return reg

def write_registry_atomic(path: Path, reg: Dict[str, dict]) -> None:
    # Clean keys and values: keys -> lowercase strings; values -> plain dicts
    cleaned: Dict[str, dict] = {str(k).lower(): (dict(v) if isinstance(v, Mapping) else v) for k, v in reg.items()}
    # Produce a stable order but dump as a plain dict to YAML
    ordered = OrderedDict(sorted(cleaned.items(), key=lambda kv: kv[0]))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(dict(ordered), sort_keys=False))
    os.replace(tmp, path)

# ---------- Filename parsing ----------
def parse_request_filename(p: Path) -> Tuple[str, str]:
    """
    Expect: pricing/requests/missing_{chain}_{address}.csv
    """
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

# ---------- Data fetchers ----------
def _get_json(url: str, params: Optional[dict] = None, max_tries: int = 6) -> dict:
    headers = _cg_headers()
    data = None
    for attempt in range(max_tries):
        _rate_limit()
        try:
            r = requests.get(url, params=params, headers=headers, timeout=45)
        except requests.RequestException:
            sleep_s = min(60, 2 ** attempt + random.random())
            print(f"[net] GET {url} attempt {attempt+1} failed; sleeping {sleep_s:.1f}s")
            time.sleep(sleep_s)
            continue

        if r.status_code == 404:
            # caller decides what to do with missing
            return {"__404__": True}
        if r.status_code == 429 or 500 <= r.status_code < 600:
            sleep_s = min(60, 2 ** attempt + random.random())
            print(f"[rate] {r.status_code} on {url}; sleeping {sleep_s:.1f}s and retrying")
            time.sleep(sleep_s)
            continue

        r.raise_for_status()
        data = r.json()
        break

    if data is None:
        raise requests.HTTPError(f"GET failed after retries: {url}")
    return data

def fetch_coingecko_id_for_contract(chain: str, addr: str) -> Optional[str]:
    platform = COINGECKO_PLATFORM.get(chain.lower())
    if not platform:
        return None
    url = f"{CG_BASE}/coins/{platform}/contract/{addr.lower()}"
    data = _get_json(url)
    if data.get("__404__"):
        return None
    return data.get("id")

def fetch_coingecko_range(coin_id: str, t_from: int, t_to: int) -> pd.DataFrame:
    url = f"{CG_BASE}/coins/{coin_id}/market_chart/range"
    params = {"vs_currency": "usd", "from": int(t_from), "to": int(t_to)}
    data = _get_json(url, params=params)
    if "prices" not in data or not data["prices"]:
        return pd.DataFrame(columns=["timestamp", "price_usd"]).astype({"timestamp": "int64", "price_usd": "float64"})
    px = pd.DataFrame(data["prices"], columns=["ms", "price_usd"])
    px["timestamp"] = (px["ms"] // 1000).astype("int64")
    px = px[["timestamp", "price_usd"]].dropna().drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    return px

# ---------- Cache + as-of ----------
def merge_into_cache(chain: str, addr: str, filled: pd.DataFrame, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_cache = cache_dir / f"{chain}_{addr.lower()}.csv"
    if filled.empty:
        # create empty file (or leave existing) so we don't refetch needlessly
        if not out_cache.exists():
            pd.DataFrame(columns=["timestamp", "price_usd"]).to_csv(out_cache, index=False)
        return out_cache
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

def asof_fill(need_ts: pd.Series, px: pd.DataFrame, base_tolerance_sec: int = 3600) -> pd.DataFrame:
    """
    Map each timestamp in need_ts to the nearest-previous price in px
    using base tolerance, then 3h, then 34h. Returns DataFrame(timestamp, price_usd).
    """
    base_tol = int(base_tolerance_sec)
    tol_3h   = max(base_tol, 3 * 3600)
    tol_34h  = 34 * 3600

    out = need_ts.to_frame(name="timestamp").dropna().astype({"timestamp": "int64"})
    out["__ord"] = range(len(out))
    out = out.sort_values("timestamp")

    if px.empty:
        print("[info] asof_fill: empty price series")
        out["price_usd"] = pd.NA
        return out.sort_values("__ord")[["timestamp", "price_usd"]]

    px_sorted = px.rename(columns={"timestamp": "px_ts"}).sort_values("px_ts")
    result = out.copy()
    result["price_usd"] = pd.NA

    def _try(tol: int) -> int:
        mask = result["price_usd"].isna()
        if not mask.any():
            return 0
        chunk = result.loc[mask, ["timestamp", "__ord"]]
        joined = pd.merge_asof(
            chunk.sort_values("timestamp"),
            px_sorted,
            left_on="timestamp",
            right_on="px_ts",
            direction="backward",
            tolerance=int(tol),
        )
        found = joined["price_usd"].notna()
        if found.any():
            upd = joined.loc[found, ["__ord", "price_usd"]]
            result.loc[result["__ord"].isin(upd["__ord"]), "price_usd"] = (
                result.loc[result["__ord"].isin(upd["__ord"])]
                .merge(upd, on="__ord", how="left")["price_usd_y"].values
            )
        return int(found.sum())

    filled = _try(base_tol)
    rem = int(result["price_usd"].isna().sum())
    print(f"[asof] tol={base_tol}s filled={filled} remaining={rem}")
    if rem > 0:
        filled2 = _try(tol_3h)
        rem = int(result["price_usd"].isna().sum())
        print(f"[asof] tol={tol_3h}s filled={filled2} remaining={rem}")
    if rem > 0:
        filled3 = _try(tol_34h)
        rem = int(result["price_usd"].isna().sum())
        print(f"[asof] tol={tol_34h}s filled={filled3} remaining={rem}")
    if rem > 0:
        print(f"[warn] {rem} timestamp(s) still lack a prior price within 34h")

    return result.sort_values("__ord")[["timestamp", "price_usd"]]

# ---------- Discovery + seeding ----------
def discover_addresses_from_events(events_csv: Path) -> set[str]:
    addrs: set[str] = set()
    try:
        ev = pd.read_csv(events_csv, usecols=["collateral_token", "debt_token"])
        for col in ("collateral_token", "debt_token"):
            if col in ev.columns:
                addrs.update(map(str.lower, ev[col].dropna().astype(str).tolist()))
    except Exception:
        pass
    return {a for a in addrs if a.startswith("0x") and len(a) == 42}

def ensure_price_ids(reg_path: Path, reg: Dict[str, dict], chain: str, addrs: Iterable[str]) -> Dict[str, dict]:
    updated = False
    for addr in sorted(set(a.lower() for a in addrs)):
        meta = reg.get(addr) or {}
        pid = meta.get("price_id") if isinstance(meta, dict) else None
        if pid:
            continue
        try:
            cg_id = fetch_coingecko_id_for_contract(chain, addr)
        except requests.HTTPError as e:
            print(f"[http] price_id lookup failed for {addr}: {e}")
            continue
        except Exception as e:
            print(f"[error] price_id lookup failed for {addr}: {e}")
            continue
        if cg_id:
            if not isinstance(meta, dict):
                meta = {}
            meta["price_id"] = f"coingecko:{cg_id}"
            reg[addr] = meta
            updated = True
            print(f"[registry] added price_id for {addr} → coingecko:{cg_id}")
    if updated:
        try:
            write_registry_atomic(reg_path, reg)
            print(f"[registry] wrote updates to {reg_path}")
        except Exception as e:
            print(f"[warn] failed to write {reg_path}: {e}")
    return reg

def emit_missing_requests_for_events(
    events_csv: Path,
    cache_dir: Path,
    requests_dir: Path,
    chain: str,
    ts_col: str = "timestamp",
) -> int:
    """
    Look at the events CSV, and for each distinct token address produce
    pricing/requests/missing_{chain}_{addr}.csv listing all timestamps
    that are not already covered by pricing cache for that token.
    Returns # of request files created or updated.
    """
    requests_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        ev = pd.read_csv(events_csv)
    except FileNotFoundError:
        print(f"[emit] events file not found: {events_csv}")
        return 0
    if ev.empty or ts_col not in ev.columns:
        print(f"[emit] no rows or missing '{ts_col}' in {events_csv}")
        return 0

    ev["timestamp"] = pd.to_numeric(ev[ts_col], errors="coerce").astype("Int64")
    ev = ev.dropna(subset=["timestamp"])
    ev["timestamp"] = ev["timestamp"].astype("int64")

    tokens = set()
    for col in ("collateral_token", "debt_token"):
        if col in ev.columns:
            tokens.update(ev[col].dropna().astype(str).str.lower().tolist())
    tokens = {t for t in tokens if t.startswith("0x") and len(t) == 42}
    if not tokens:
        print("[emit] found no token addresses in events")
        return 0

    created = 0
    for addr in sorted(tokens):
        need = ev.loc[
            (ev["collateral_token"].str.lower() == addr) | (ev["debt_token"].str.lower() == addr),
            "timestamp"
        ].drop_duplicates().sort_values()

        cache_file = cache_dir / f"{chain}_{addr}.csv"
        if cache_file.exists():
            cached = pd.read_csv(cache_file)
            if not cached.empty:
                have = set(pd.to_numeric(cached["timestamp"], errors="coerce").dropna().astype("int64").tolist())
                need = need[~need.isin(have)]

        if need.empty:
            continue

        out_req = requests_dir / f"missing_{chain}_{addr}.csv"
        need.to_frame(name="timestamp").to_csv(out_req, index=False)
        created += 1
        print(f"[req] wrote {out_req} rows={len(need)}")

    return created

def seed_requests_from_folder(
    reg: Dict[str, dict],
    reg_path: Path,
    requests_dir: Path,
    cache_dir: Path,
    chain: str,
    base_tolerance_sec: int = 3600,
) -> None:
    req_files = sorted((requests_dir or Path("pricing/requests")).glob("missing_*.csv"))
    if not req_files:
        print("[seed] no request files found")
        return

    for p in req_files:
        try:
            chain2, addr = parse_request_filename(p)
            if chain2.lower() != chain.lower():
                # allow cross-chain in same folder, but skip here
                continue
            need = pd.read_csv(p)
            if need.empty or "timestamp" not in need.columns:
                print(f"[seed] {p.name} has no timestamps")
                continue
            need_ts = pd.to_numeric(need["timestamp"], errors="coerce").dropna().astype("int64")
            if need_ts.empty:
                print(f"[seed] {p.name} has no valid timestamps")
                continue

            # Short-circuit: if cache already fulfills some/all requests (as-of prior price),
            # avoid unnecessary CoinGecko calls by pruning fulfilled and only fetching unmet timestamps.
            cache_file = cache_dir / f"{chain}_{addr}.csv"
            unmet_ts = need_ts
            if cache_file.exists():
                try:
                    cached = pd.read_csv(cache_file)
                except Exception:
                    cached = pd.DataFrame()
                if not cached.empty and "timestamp" in cached.columns:
                    c = pd.to_numeric(cached["timestamp"], errors="coerce").dropna().astype("int64").to_numpy()
                    if c.size:
                        c.sort()
                        r = need_ts.to_numpy()
                        # fulfilled if any cached ts <= r[i]
                        idx = np.searchsorted(c, r, side="right")
                        mask_unmet = idx == 0
                        if not mask_unmet.any():
                            # Everything already fulfillable from cache → prune and continue
                            _prune_request_file(chain=chain, addr=addr, cache_dir=cache_dir, requests_dir=requests_dir)
                            print(f"[seed] skip {addr}: all {len(r)} timestamps fulfillable from cache")
                            continue
                        # Only fetch the unmet subset
                        unmet_ts = pd.Series(r[mask_unmet], name="timestamp")

            # Replace the needed timestamps with only the unmet subset (if any)
            need_ts = unmet_ts
            if need_ts.empty:
                _prune_request_file(chain=chain, addr=addr, cache_dir=cache_dir, requests_dir=requests_dir)
                print(f"[seed] skip {addr}: no unmet timestamps after cache check")
                continue

            # ensure price_id in registry (writes atomically)
            reg = ensure_price_ids(reg_path, reg, chain, [addr])
            price_id = (reg.get(addr) or {}).get("price_id")
            if not price_id or ":" not in price_id:
                print(f"[seed] skip {addr}: missing price_id (add and rerun)")
                continue
            src, ident = price_id.split(":", 1)

            if src != "coingecko":
                print(f"[seed] unsupported source '{src}' for {addr}")
                continue

            t_from, t_to = int(need_ts.min()), int(need_ts.max())
            px = fetch_coingecko_range(ident, t_from, t_to)
            filled = asof_fill(need_ts, px, base_tolerance_sec)
            missing = int(filled["price_usd"].isna().sum())
            out_path = merge_into_cache(chain, addr, filled, cache_dir)
            print(f"[ok] cached {len(filled) - missing} / {len(filled)} → {out_path}")
            # Prune fulfilled request timestamps now that the cache was updated
            _prune_request_file(chain=chain, addr=addr, cache_dir=cache_dir, requests_dir=requests_dir)
        except Exception as e:
            print(f"[seed][error] {p.name}: {e}")