# tvl/price_cache_connect.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import pandas as pd

from price_cache.pricing_cache import (
    load_registry,
    ensure_price_ids,
    merge_into_cache,          # used by the seeder; import for completeness
    asof_fill,
)

def _cache_path(cache_dir: Path, chain: str, addr: str) -> Path:
    return (cache_dir / f"{chain}_{addr.lower()}.csv")

def _load_cached_prices(cache_dir: Path, chain: str, addr: str) -> pd.DataFrame:
    p = _cache_path(cache_dir, chain, addr)
    if not p.exists():
        return pd.DataFrame(columns=["timestamp", "price_usd"])
    df = pd.read_csv(p)
    # normalize timestamp dtype
    if not df.empty and "timestamp" in df.columns and not pd.api.types.is_integer_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).astype("int64") // 10**9
    return df[["timestamp","price_usd"]].dropna().drop_duplicates(subset=["timestamp"]).sort_values("timestamp")

def _write_single_request(requests_dir: Path, chain: str, addr: str, ts: int) -> Path:
    requests_dir.mkdir(parents=True, exist_ok=True)
    out = requests_dir / f"missing_{chain}_{addr.lower()}.csv"
    # append (de-duped)
    df = pd.DataFrame({"timestamp": [int(ts)]})
    if out.exists():
        old = pd.read_csv(out)
        df = pd.concat([old, df], ignore_index=True).drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    df.to_csv(out, index=False)
    return out

@dataclass
class CachePriceSource:
    chain: str
    registry_path: Path
    cache_dir: Path
    requests_dir: Path
    tolerance_sec: int = 3600

    def __post_init__(self):
        self.registry = load_registry(self.registry_path)

    def get(self, token_addr: str, ts: Optional[int] = None) -> Optional[float]:
        """
        Return USD price as-of ts using the on-disk cache.
        If missing/stale around ts, emit a request file and seed, then retry.
        """
        if ts is None:
            ts = int(datetime.now(timezone.utc).timestamp())

        addr = token_addr.lower()

        # 1) ensure registry has price_id (if not, we still proceed—seeder will resolve)
        self.registry = ensure_price_ids(self.registry_path, self.registry, self.chain, [addr])

        # 2) try cache as-of fill
        px = _load_cached_prices(self.cache_dir, self.chain, addr)
        filled = asof_fill(pd.Series([ts], name="timestamp"), px, base_tolerance_sec=self.tolerance_sec)
        if not filled.empty and not pd.isna(filled["price_usd"].iloc[0]):
            return float(filled["price_usd"].iloc[0])

        # 3) emit a request file for this timestamp and return None.
        #    An offline backfill job (gecko_backfill.py) will later fulfill this.
        _write_single_request(self.requests_dir, self.chain, addr, ts)
        return None