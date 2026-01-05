import argparse
import pandas as pd
import numpy as np
import yaml
from collections.abc import Mapping
from pathlib import Path
from datetime import datetime, timezone
from config.utils.time import to_dt, to_date_ny

from price_cache.pricing_cache import (
    load_registry,           # already exists and used elsewhere
    load_cached_prices,
    asof_fill,               # as-of join (if you’re currently re-implementing it)
    record_missing_requests, # same behavior (or use emit_missing_requests_for_events)
    merge_into_cache,        # saver that merges atomically
)


def norm_addr(x):
    return None if pd.isna(x) else str(x).strip().lower()

def ensure_metadata(events: pd.DataFrame, reg: dict, addr_cols: list[str]) -> list[str]:
    known = set(reg.keys())
    unknown = set()
    for c in addr_cols:
        unknown |= set(events[c].dropna().unique()) - known
    if unknown:
        pd.DataFrame({"address": sorted(unknown)}).to_csv("token_registry_missing.csv", index=False)
    return sorted(unknown)

def scale_amount(raw, decimals):
    if pd.isna(raw) or pd.isna(decimals): return np.nan
    return float(raw) / (10 ** int(decimals))

def asof_join(token_prices: pd.DataFrame, events: pd.DataFrame, ts_col: str, out_col: str, tolerance_sec: int) -> pd.DataFrame:
    # Always return a frame with the SAME index/length as `events`,
    # filling NaN where timestamp is missing or no prior price within tolerance.
    result = events[[ts_col]].copy()
    result.loc[:, out_col] = np.nan

    # No prices available → return all-NaN for this column
    if token_prices.empty:
        return result[[out_col]]

    # Prepare right-side prices: ensure int64 epoch seconds key
    px = token_prices.rename(columns={"timestamp": "px_ts"}).copy()
    px["px_ts"] = pd.to_numeric(px["px_ts"], errors="coerce").astype("Int64")
    px = px.dropna(subset=["px_ts"]).copy()
    if px.empty:
        return result[[out_col]]
    px["px_ts"] = px["px_ts"].astype("int64")
    px = px.sort_values("px_ts")

    # Left side: keep original index, only convert valid timestamps
    left = events[[ts_col]].copy()
    left["__idx"] = left.index
    left[ts_col] = pd.to_numeric(left[ts_col], errors="coerce").astype("Int64")
    valid_mask = left[ts_col].notna()
    left_valid = left.loc[valid_mask, [ts_col, "__idx"]].copy()
    left_valid[ts_col] = left_valid[ts_col].astype("int64")
    left_valid = left_valid.sort_values(ts_col)

    if not left_valid.empty:
        tol = int(tolerance_sec)
        merged = pd.merge_asof(
            left_valid,
            px,
            left_on=ts_col,
            right_on="px_ts",
            direction="backward",
            tolerance=tol,
        )
        # Map back to original indices
        if "price_usd" in merged.columns:
            result.loc[merged["__idx"].values, out_col] = merged["price_usd"].values

    return result[[out_col]]

def main():
    ap = argparse.ArgumentParser(description="Convert liquidation events to daily USD with a reusable price cache.")
    ap.add_argument("--events_csv", required=True)
    ap.add_argument("--protocol", required=True, help="Protocol name, e.g., 'Aave V3'")
    ap.add_argument("--token_registry", default="token_registry.yaml")
    ap.add_argument("--chain", default="ethereum")
    ap.add_argument("--tolerance_sec", type=int, default=600)
    ap.add_argument("--out_enriched_csv", default=None, help="Override output path for enriched events CSV")
    ap.add_argument("--out_daily_csv", default=None, help="Override output path for daily aggregation CSV")
    ap.add_argument("--out-root", default="data/out", help="Root directory for standardized outputs")
    ap.add_argument("--no-write", action="store_true", help="Do not write files; only print destinations")
    args = ap.parse_args()

    ev = pd.read_csv(args.events_csv)

    # Normalize address columns
    for c in ["collateral_token","debt_token","user","liquidator","tx_hash"]:
        if c in ev.columns: ev[c] = ev[c].apply(norm_addr)

    if "timestamp" not in ev.columns:
        raise ValueError("events csv missing 'timestamp'")

    ev["datetime_utc"] = ev["timestamp"].apply(lambda t: to_dt(t).isoformat())
    ev["date_ny"] = ev["timestamp"].apply(to_date_ny)

    # Standardized date string (UTC, matching TVL convention)
    now_utc = datetime.now(timezone.utc)
    date_str = now_utc.strftime("%Y-%m-%d")

    # Standardized output locations: {out_root}/liquid/{protocol_slug}_{chain}/
    protocol_slug = args.protocol.lower().replace(" ", "_")
    out_dir = Path(args.out_root) / "liquid" / f"{protocol_slug}_{args.chain}"
    out_dir.mkdir(parents=True, exist_ok=True)

    enriched_path = Path(args.out_enriched_csv) if args.out_enriched_csv else (out_dir / f"events_{date_str}.csv")
    daily_path = Path(args.out_daily_csv) if args.out_daily_csv else (out_dir / f"liquidations_daily_{date_str}.csv")

    # Load token registry
    reg = load_registry(args.token_registry)
    ensure_metadata(ev, reg, ["collateral_token","debt_token"])

    # Add symbols/decimals
    def meta(addr, role):
        m = reg.get(addr)
        if not m: return (f"UNKNOWN_{role}", np.nan)
        return (m.get("symbol") or f"UNKNOWN_{role}", m.get("decimals"))
    ev[["collateral_symbol","collateral_decimals"]] = ev.apply(lambda r: pd.Series(meta(r["collateral_token"], "C")), axis=1)
    ev[["debt_symbol","debt_decimals"]] = ev.apply(lambda r: pd.Series(meta(r["debt_token"], "D")), axis=1)

    # Human amounts
    if "collateral_amount" in ev.columns:
        ev["collateral_amount_adj"] = ev.apply(lambda r: scale_amount(r["collateral_amount"], r["collateral_decimals"]), axis=1)
    if "debt_repaid" in ev.columns:
        ev["debt_repaid_adj"] = ev.apply(lambda r: scale_amount(r["debt_repaid"], r["debt_decimals"]), axis=1)

    # Tokens present
    tokens_coll = set(ev["collateral_token"].dropna().unique())
    tokens_debt = set(ev["debt_token"].dropna().unique())
    tokens = sorted(tokens_coll | tokens_debt)

    # All timestamps we might need
    needed_ts = sorted(set(int(t) for t in ev["timestamp"].unique()))

    # Assemble per-token price frames from cache; if empty, write request file
    token_price_map = {}
    for addr in tokens:
        px = load_cached_prices(args.chain, addr)
        if px.empty:
            req = record_missing_requests(args.chain, addr, needed_ts)
            print(f"[req] no cached prices for {addr}; wrote -> {req}")
        token_price_map[addr] = px

    # Join collateral prices
    ev["collateral_price_usd"] = np.nan
    for addr in tokens_coll:
        mask = ev["collateral_token"] == addr
        joined = asof_join(token_price_map.get(addr, pd.DataFrame()), ev.loc[mask], "timestamp", "collateral_price_usd", args.tolerance_sec)
        ev.loc[mask, "collateral_price_usd"] = joined["collateral_price_usd"].values

    # Join debt prices
    ev["debt_price_usd"] = np.nan
    for addr in tokens_debt:
        mask = ev["debt_token"] == addr
        joined = asof_join(token_price_map.get(addr, pd.DataFrame()), ev.loc[mask], "timestamp", "debt_price_usd", args.tolerance_sec)
        ev.loc[mask, "debt_price_usd"] = joined["debt_price_usd"].values

    # USD values
    ev["collateral_value_usd"] = ev["collateral_amount_adj"] * ev["collateral_price_usd"]
    ev["debt_repaid_value_usd"] = ev["debt_repaid_adj"] * ev["debt_price_usd"]

    # Save enriched
    if not args.no_write:
        enriched_path.parent.mkdir(parents=True, exist_ok=True)
        ev.to_csv(enriched_path, index=False)

    # Daily aggregation (NY calendar)
    grp = ev.groupby("date_ny", dropna=False).agg(
        events=("tx_hash", "count"),
        unique_users=("user", pd.Series.nunique),
        unique_liquidators=("liquidator", pd.Series.nunique),
        collateral_value_usd=("collateral_value_usd", "sum"),
        debt_repaid_value_usd=("debt_repaid_value_usd", "sum")
    ).reset_index()
    if not args.no_write:
        daily_path.parent.mkdir(parents=True, exist_ok=True)
        grp.to_csv(daily_path, index=False)

    if not args.no_write:
        print(f"[ok] wrote {enriched_path}")
        print(f"[ok] wrote {daily_path}")
    else:
        print(f"[dry-run] would write enriched → {enriched_path}")
        print(f"[dry-run] would write daily    → {daily_path}")
    print("[hint] Fill price_cache/pricing/*.csv for missing tokens/timestamps and re-run to remove NaNs.")

if __name__ == "__main__":
    main()
