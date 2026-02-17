#!/usr/bin/env python3
"""
Build Gold Layer - Daily Liquidation Panels (All Chains)

Aggregates silver liquidation data from all chains into daily panels by CSU.

Output: data/gold/liquidations/all_chains/daily_panel.parquet

Usage:
    python scripts/build_gold_panel_all_chains.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime


SILVER_DIR = Path("data/silver/liquidations")
GOLD_DIR = Path("data/gold/liquidations")


def load_all_silver_data() -> pd.DataFrame:
    """Load silver liquidation data from all chains."""
    import json
    all_dfs = []

    # Try enriched JSONL first, fallback to parquet
    chains = [d.name for d in SILVER_DIR.iterdir()
              if d.is_dir() and ((d / "events_enriched.jsonl").exists() or (d / "liquidations.parquet").exists())]

    print(f"Found {len(chains)} chains with silver data")

    for chain in sorted(chains):
        enriched_path = SILVER_DIR / chain / "events_enriched.jsonl"
        parquet_path = SILVER_DIR / chain / "liquidations.parquet"

        try:
            # Prefer enriched JSONL (has USD values from oracles)
            if enriched_path.exists():
                events = []
                with open(enriched_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line:  # Skip empty lines
                            continue
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError as je:
                            print(f"    Warning: Skipping invalid JSON line: {je}")
                            continue
                df = pd.DataFrame(events)
                source = "enriched JSONL"
            else:
                df = pd.read_parquet(parquet_path)
                source = "parquet"

            if len(df) == 0:
                print(f"  {chain}: SKIPPED (no events)")
                continue

            df["chain"] = chain  # Ensure chain column exists
            all_dfs.append(df)
            print(f"  {chain}: {len(df):,} events ({source})")
        except Exception as e:
            print(f"  {chain}: ERROR - {e}")

    if not all_dfs:
        raise ValueError("No silver data found")

    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"\nTotal: {len(combined):,} events")
    return combined


def aggregate_daily_by_csu(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate liquidations to daily totals by CSU."""
    # Ensure we have the date column
    if "date" not in df.columns or df["date"].isna().all():
        if "block_timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["block_timestamp"], unit="s").dt.strftime("%Y-%m-%d")

    # Remove rows without dates
    df = df[df["date"].notna()].copy()

    # Determine column names (enriched JSONL uses different names)
    collateral_col = "collateral_value_usd" if "collateral_value_usd" in df.columns else "collateral_usd"
    debt_col = "debt_value_usd" if "debt_value_usd" in df.columns else "debt_usd"

    agg = df.groupby(["date", "csu", "chain"]).agg(
        n_liquidations=("tx_hash", "count"),
        total_collateral_usd=(collateral_col, lambda x: x.sum() if x.notna().any() else 0),
        total_debt_usd=(debt_col, lambda x: x.sum() if x.notna().any() else 0),
        n_unique_borrowers=("borrower", "nunique"),
        n_unique_liquidators=("liquidator", "nunique"),
        n_priced=(collateral_col, lambda x: x.notna().sum()),
    ).reset_index()

    # Calculate averages
    agg["avg_collateral_usd"] = agg["total_collateral_usd"] / agg["n_liquidations"].clip(lower=1)
    agg["avg_debt_usd"] = agg["total_debt_usd"] / agg["n_liquidations"].clip(lower=1)
    agg["pct_priced"] = agg["n_priced"] / agg["n_liquidations"].clip(lower=1)

    return agg


def create_balanced_panel(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Create balanced panel with all CSU x date combinations."""
    if start_date is None:
        start_date = df["date"].min()
    if end_date is None:
        end_date = df["date"].max()

    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    dates = [d.strftime("%Y-%m-%d") for d in dates]

    # Get all CSUs with their chains
    csu_chain = df[["csu", "chain"]].drop_duplicates()

    # Create full index
    full_rows = []
    for _, row in csu_chain.iterrows():
        for date in dates:
            full_rows.append({"date": date, "csu": row["csu"], "chain": row["chain"]})

    full_panel = pd.DataFrame(full_rows)

    # Merge with actual data
    panel = full_panel.merge(df, on=["date", "csu", "chain"], how="left")

    # Fill missing values
    fill_cols = ["n_liquidations", "total_collateral_usd", "total_debt_usd",
                 "n_unique_borrowers", "n_unique_liquidators", "n_priced",
                 "avg_collateral_usd", "avg_debt_usd", "pct_priced"]

    for col in fill_cols:
        if col in panel.columns:
            panel[col] = panel[col].fillna(0)

    # Convert counts to int
    int_cols = ["n_liquidations", "n_unique_borrowers", "n_unique_liquidators", "n_priced"]
    for col in int_cols:
        if col in panel.columns:
            panel[col] = panel[col].astype(int)

    return panel.sort_values(["chain", "csu", "date"]).reset_index(drop=True)


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features for econometric analysis."""
    df = df.copy()

    # Binary indicator
    df["has_liquidation"] = (df["n_liquidations"] > 0).astype(int)

    # Log transforms
    df["log_collateral_usd"] = np.log1p(df["total_collateral_usd"])
    df["log_debt_usd"] = np.log1p(df["total_debt_usd"])
    df["log_n_liquidations"] = np.log1p(df["n_liquidations"])

    return df


def main():
    print("=" * 70)
    print("Building Gold Layer - All Chains Daily Panel")
    print("=" * 70)

    # Load all silver data
    print("\nLoading silver data from all chains...")
    df = load_all_silver_data()

    # Drop rows without dates
    before_count = len(df)
    df = df[df["date"].notna()].copy()
    dropped = before_count - len(df)
    if dropped > 0:
        print(f"\nDropped {dropped:,} rows without dates")

    date_min = df["date"].dropna().min()
    date_max = df["date"].dropna().max()
    print(f"\nDate range: {date_min} to {date_max}")
    print(f"CSUs: {df['csu'].nunique()}")
    print(f"Chains: {df['chain'].nunique()}")

    # Aggregate
    print("\nAggregating to daily panels...")
    daily = aggregate_daily_by_csu(df)
    print(f"  Created {len(daily):,} CSU-day observations (sparse)")

    # Create balanced panel
    print("\nCreating balanced panel...")
    panel = create_balanced_panel(daily)
    print(f"  Balanced panel: {len(panel):,} observations")
    print(f"  ({panel['date'].nunique()} dates x {panel['csu'].nunique()} CSUs)")

    # Add derived features
    print("\nAdding derived features...")
    panel = add_derived_features(panel)

    # Summary by chain
    print("\n" + "=" * 70)
    print("Summary by Chain")
    print("=" * 70)

    chain_summary = panel.groupby("chain").agg({
        "csu": "nunique",
        "n_liquidations": "sum",
        "has_liquidation": "sum",
        "total_collateral_usd": "sum",
    }).round(0)

    for chain in sorted(chain_summary.index):
        row = chain_summary.loc[chain]
        print(f"\n  {chain}:")
        print(f"    CSUs: {int(row['csu'])}")
        print(f"    Total events: {int(row['n_liquidations']):,}")
        print(f"    Days with liquidations: {int(row['has_liquidation']):,}")
        print(f"    Total collateral USD: ${row['total_collateral_usd']:,.0f}")

    # Overall
    print("\n" + "-" * 70)
    print("Overall:")
    print(f"  Total events: {panel['n_liquidations'].sum():,}")
    print(f"  Total collateral: ${panel['total_collateral_usd'].sum():,.0f}")
    print(f"  Total debt: ${panel['total_debt_usd'].sum():,.0f}")

    # Save
    output_dir = GOLD_DIR / "all_chains"
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = output_dir / "daily_panel.parquet"
    panel.to_parquet(parquet_path, index=False)
    print(f"\nSaved: {parquet_path}")

    csv_path = output_dir / "daily_panel.csv"
    panel.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")

    # Panel structure
    print("\n" + "=" * 70)
    print("Panel Structure")
    print("=" * 70)

    n_csus = panel["csu"].nunique()
    n_dates = panel["date"].nunique()
    expected = n_csus * n_dates
    actual = len(panel)

    print(f"\n  N (CSUs): {n_csus}")
    print(f"  T (dates): {n_dates}")
    print(f"  N x T: {expected:,}")
    print(f"  Observations: {actual:,}")
    print(f"  Balanced: {'Yes' if expected == actual else 'No'}")

    print("\n  Gold panel complete.")


if __name__ == "__main__":
    main()
