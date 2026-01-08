
import os
from pathlib import Path
import pandas as pd

CACHE_DIR = Path(os.environ.get("PRICE_CACHE_DIR", "pricing"))

def _token_key(chain: str, address: str) -> str:
    return f"{chain.lower()}_{address.lower()}"

def cache_path(chain: str, address: str) -> Path:
    return CACHE_DIR / f"{_token_key(chain, address)}.csv"

def load_cached_prices(chain: str, address: str) -> pd.DataFrame:
    p = cache_path(chain, address)
    if not p.exists():
        return pd.DataFrame(columns=["timestamp", "price_usd"])
    df = pd.read_csv(p)
    if "timestamp" not in df or "price_usd" not in df:
        raise ValueError(f"Bad cache schema in {p}")
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    return df

def save_cached_prices(chain: str, address: str, df: pd.DataFrame) -> None:
    p = cache_path(chain, address)
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = load_cached_prices(chain, address)
    if not existing.empty:
        df = pd.concat([existing, df], axis=0, ignore_index=True)
        df = df.drop_duplicates(subset=["timestamp"], keep="last")
    df = df.sort_values("timestamp")
    df.to_csv(p, index=False)

def record_missing_requests(chain: str, address: str, timestamps: list[int]) -> Path:
    req_dir = CACHE_DIR / "requests"
    req_dir.mkdir(parents=True, exist_ok=True)
    out = req_dir / f"missing_{chain.lower()}_{address.lower()}.csv"
    import pandas as pd
    pd.DataFrame({"timestamp": sorted(set(int(t) for t in timestamps))}).to_csv(out, index=False)
    return out
