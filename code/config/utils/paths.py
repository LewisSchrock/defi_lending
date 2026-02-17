# utils/paths.py
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass

@dataclass
class OutLayout:
    # root folder for all outputs (override via CLI or env if you like)
    out_root: Path = Path("data/out")

    def csu_dir(self, domain: str, protocol_slug: str, chain: str) -> Path:
        """
        domain: 'tvl' or 'liquid'
        protocol_slug: e.g., 'aave_v3'
        chain: e.g., 'ethereum'
        """
        d = self.out_root / domain / f"{protocol_slug}_{chain}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # Filenames (can be tweaked later without touching call sites)
    def tvl_assets_daily(self, date_str: str) -> str:
        return f"tvl_assets_{date_str}.csv"

    def tvl_summary_daily(self, date_str: str) -> str:
        return f"tvl_summary_{date_str}.csv"

    def liquid_events_raw(self, date_str: str) -> str:
        return f"events_{date_str}.csv"

    def liquid_enriched_daily(self, date_str: str) -> str:
        return f"liquidations_daily_{date_str}.csv"