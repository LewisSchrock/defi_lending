#!/usr/bin/env python3
"""
plot_deployment_gantt_2024.py

Creates a Gantt chart of CSU "active" periods during 2024.
- Reads code/config/csu_config.yaml
- Reads code/config/deployment_dates.yaml (optional overrides; missing => pre-2024)
- Filters to WORKING_CHAINS
- Plots bars from start_date to 2024-12-31

Run:
  python code/scripts/plot_deployment_gantt_2024.py

Optional:
  python code/scripts/plot_deployment_gantt_2024.py --color_by protocol
  python code/scripts/plot_deployment_gantt_2024.py --color_by chain
  python code/scripts/plot_deployment_gantt_2024.py --out outputs/csu_gantt_2024.png
  python code/scripts/plot_deployment_gantt_2024.py --limit 60
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yaml

WORKING_CHAINS = {
    "ethereum", "arbitrum", "base", "optimism",
    "avalanche", "linea", "gnosis", "scroll"
}

YEAR_START = date(2024, 1, 1)
YEAR_END = date(2024, 12, 31)

DEFAULT_CSU_CONFIG = Path("code/config/csu_config.yaml")
DEFAULT_DEPLOY_DATES = Path("code/config/deployment_dates.yaml")


def parse_iso_date(s: str) -> date:
    s = str(s).strip()
    # Accept YYYY-MM-DD only (your file format)
    return datetime.strptime(s, "%Y-%m-%d").date()


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Empty YAML: {path}")
    return data


def load_csu_config(path: Path) -> pd.DataFrame:
    """
    Expects top-level mapping:
      aave_v3_ethereum:
        protocol: aave
        version: v3
        chain: ethereum
        registry: ...
    """
    raw = load_yaml(path)
    if not isinstance(raw, dict):
        raise ValueError(f"csu_config.yaml should be a mapping; got {type(raw)}")

    rows = []
    for csu, cfg in raw.items():
        if not isinstance(cfg, dict):
            continue
        rows.append(
            {
                "csu": csu,
                "protocol": str(cfg.get("protocol", "")).strip().lower(),
                "chain": str(cfg.get("chain", "")).strip().lower(),
                "version": str(cfg.get("version", "")).strip().lower(),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No CSU rows parsed from csu_config.yaml")
    return df


def load_deployment_dates(path: Path) -> Dict[str, date]:
    """
    Expects:
    csus:
      compound_v3_base_usdc: "2024-03-11"
      ...
    """
    raw = load_yaml(path)
    if not isinstance(raw, dict) or "csus" not in raw:
        raise ValueError("deployment_dates.yaml must contain top-level key: csus")

    csus = raw["csus"]
    if not isinstance(csus, dict):
        raise ValueError("deployment_dates.yaml 'csus' must be a mapping")

    out: Dict[str, date] = {}
    for csu, d in csus.items():
        if d is None:
            continue
        out[str(csu).strip()] = parse_iso_date(str(d))
    return out


def build_chart_df(csu_df: pd.DataFrame, deploy_dates: Dict[str, date]) -> pd.DataFrame:
    df = csu_df.copy()

    # Filter to working chains
    df = df[df["chain"].isin(WORKING_CHAINS)].copy()

    # Assign start dates: explicit deployment date else YEAR_START
    def start_for(csu: str) -> date:
        d = deploy_dates.get(csu)
        if d is None:
            return YEAR_START
        # If deployment date is after 2024 end, it shouldn't appear active in 2024
        return d

    df["start"] = df["csu"].apply(start_for)
    df["end"] = YEAR_END

    # Only keep those that are active at any point in 2024
    df = df[df["start"] <= YEAR_END].copy()

    # Clamp starts to YEAR_START (pre-2024 become 2024-01-01)
    df.loc[df["start"] < YEAR_START, "start"] = YEAR_START

    # Duration in days (at least 1 day for rendering)
    df["duration_days"] = (pd.to_datetime(df["end"]) - pd.to_datetime(df["start"])).dt.days
    df.loc[df["duration_days"] < 1, "duration_days"] = 1

    # Sort: protocol then chain then start then name (readable blocks)
    df = df.sort_values(["protocol", "chain", "start", "csu"]).reset_index(drop=True)
    return df


def plot_gantt(df: pd.DataFrame, out_path: Path, color_by: str, title: str, limit: int | None) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    if limit is not None and limit > 0:
        df = df.head(limit).copy()

    if df.empty:
        raise ValueError("No CSUs to plot after filtering.")

    # Choose group key for coloring
    if color_by not in {"protocol", "chain"}:
        raise ValueError("--color_by must be 'protocol' or 'chain'")

    df["group"] = df[color_by].fillna("unknown")

    groups = list(dict.fromkeys(df["group"].tolist()))  # preserve order

    # Build a stable color map (matplotlib default cycle)
    prop_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
    if not prop_cycle:
        prop_cycle = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"]

    color_map = {g: prop_cycle[i % len(prop_cycle)] for i, g in enumerate(groups)}

    # Figure height scales with number of CSUs
    fig_h = max(6.0, 0.28 * len(df) + 2.0)
    fig, ax = plt.subplots(figsize=(14, fig_h))

    y_positions = range(len(df))
    starts_num = mdates.date2num(pd.to_datetime(df["start"]).dt.to_pydatetime())
    durations = df["duration_days"].tolist()

    colors = [color_map[g] for g in df["group"].tolist()]
    ax.barh(list(y_positions), durations, left=starts_num, height=0.7, color=colors)

    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(df["csu"].tolist(), fontsize=9)
    ax.invert_yaxis()

    # X-axis bounds exactly 2024
    ax.set_xlim(mdates.date2num(datetime(2024, 1, 1)), mdates.date2num(datetime(2024, 12, 31)))

    locator = mdates.MonthLocator(interval=1)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))

    ax.set_xlabel("2024")
    ax.set_title(title)

    # Legend
    handles = [
        plt.Line2D([0], [0], color=color_map[g], lw=6, label=g)
        for g in groups
    ]
    ax.legend(handles=handles, title=color_by, loc="lower right", frameon=True)

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csu_config", type=str, default=str(DEFAULT_CSU_CONFIG))
    ap.add_argument("--deployment_dates", type=str, default=str(DEFAULT_DEPLOY_DATES))
    ap.add_argument("--out", type=str, default="outputs/csu_deploy_gantt_2024.png")
    ap.add_argument("--color_by", type=str, default="protocol", choices=["protocol", "chain"])
    ap.add_argument("--title", type=str, default="CSU Active Periods in 2024 (deployment → 2024-12-31)")
    ap.add_argument("--limit", type=int, default=None, help="Plot only first N rows (debug).")
    ap.add_argument("--csv_out", type=str, default="outputs/csu_deploy_gantt_2024_data.csv", help="Write chart data to CSV.")
    args = ap.parse_args()

    csu_path = Path(args.csu_config)
    dep_path = Path(args.deployment_dates)
    out_path = Path(args.out)
    csv_out = Path(args.csv_out)

    csu_df = load_csu_config(csu_path)
    deploy_dates = load_deployment_dates(dep_path)

    chart_df = build_chart_df(csu_df, deploy_dates)

    # # Write the underlying data (useful for debugging + thesis appendix)
    # csv_out.parent.mkdir(parents=True, exist_ok=True)
    # chart_df.to_csv(csv_out, index=False)

    plot_gantt(
        df=chart_df,
        out_path=out_path,
        color_by=args.color_by,
        title=args.title,
        limit=args.limit,
    )

    # print(f"✅ Saved chart: {out_path.resolve()}")
    # print(f"✅ Saved data:  {csv_out.resolve()}")
    print(f"CSUs plotted: {len(chart_df)}")
    print("Chains included:", ", ".join(sorted(WORKING_CHAINS)))


if __name__ == "__main__":
    main()
