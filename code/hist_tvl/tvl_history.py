from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path

import sys

# Ensure the project root (the directory that contains `config/`, `tvl/`, etc.)
# is on sys.path so that `import config...` works when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Dict, Any, Iterable, List

import yaml
from web3 import Web3, HTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware
from tvl.blockchain_utils import connect_rpc, get_pool_addresses
from tvl.config import POOL_ABI, DATA_PROVIDER_ABI, ERC20_ABI

from config.utils.time import ny_date_to_utc_window
from config.utils.block import block_for_ts


def iterate_dates(start_str: str, end_str: str) -> Iterable[str]:
    """Yield YYYY-MM-DD strings from start_str to end_str (inclusive)."""
    d0 = date.fromisoformat(start_str)
    d1 = date.fromisoformat(end_str)
    d = d0
    while d <= d1:
        yield d.isoformat()
        d += timedelta(days=1)


def erc20_total_supply_at_block(w3: Web3, token_addr: str, block_number: int) -> float:
    """
    Historical-friendly totalSupply reader.

    We intentionally do not reuse tvl.blockchain_utils.get_total_supply here
    because that always reads at the head block and does not accept a
    block_identifier. This version mirrors its behavior but pins reads to a
    given block.
    """
    token_addr = Web3.to_checksum_address(token_addr)
    try:
        # Skip non-contract addresses
        if len(w3.eth.get_code(token_addr)) < 100:
            return 0.0
        c = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        try:
            decimals = c.functions.decimals().call()
        except Exception:
            decimals = 18
        raw = c.functions.totalSupply().call(block_identifier=block_number)
        return raw / (10 ** decimals)
    except Exception:
        return 0.0


def compute_aave_v3_balances_at_block(
    w3: Web3,
    csu_cfg: Dict[str, Any],
    block_number: int,
) -> List[Dict[str, Any]]:
    """
    Compute Aave v3 reserve-level balances at a specific block, for one CSU.

    This reuses the same provider → pool/dataProvider wiring as the live TVL
    code, but pins all state reads to `block_number`. It does NOT write or
    touch anything in tvl/.
    """
    chain = csu_cfg["chain"]
    protocol = csu_cfg["protocol"]
    provider_addr = csu_cfg.get("registry") or csu_cfg.get("provider")

    if not provider_addr:
        print(f"[warn] {chain}: no provider/registry address in CSU config; skipping balances")
        return []

    provider_addr = Web3.to_checksum_address(provider_addr)

    # Reuse the provider → (pool, oracle, data_provider) mapping from tvl.blockchain_utils,
    # which reads at the head. For Aave v3 these are stable proxy addresses, so using
    # head-state addresses is safe even for historical balances.
    addrs = get_pool_addresses(w3, provider_addr)
    pool_addr = addrs["pool"]
    data_provider_addr = addrs["data_provider"]

    pool = w3.eth.contract(address=pool_addr, abi=POOL_ABI)
    data_provider = w3.eth.contract(address=data_provider_addr, abi=DATA_PROVIDER_ABI)

    # Reserves list as of block_number
    try:
        reserves: List[str] = pool.functions.getReservesList().call(block_identifier=block_number)
    except Exception as e:
        print(f"[warn] {chain}: getReservesList failed at block {block_number}: {e}")
        return []

    rows: List[Dict[str, Any]] = []

    for asset in reserves:
        asset = Web3.to_checksum_address(asset)
        try:
            # Aave v3 data provider interface: returns (aToken, stableDebt, variableDebt)
            a_addr, sd_addr, vd_addr = data_provider.functions.getReserveTokensAddresses(asset).call(
                block_identifier=block_number
            )
            a_addr = Web3.to_checksum_address(a_addr)
            sd_addr = Web3.to_checksum_address(sd_addr)
            vd_addr = Web3.to_checksum_address(vd_addr)

            a_supply = erc20_total_supply_at_block(w3, a_addr, block_number)
            vd_supply = erc20_total_supply_at_block(w3, vd_addr, block_number)
            sd_supply = erc20_total_supply_at_block(w3, sd_addr, block_number)

            rows.append(
                {
                    "asset": asset,
                    "a_token": a_addr,
                    "sd_token": sd_addr,
                    "vd_token": vd_addr,
                    "a_supply": a_supply,
                    "sd_supply": sd_supply,
                    "vd_supply": vd_supply,
                }
            )
        except Exception as e:
            print(f"[warn] {chain}: failed to snapshot reserve {asset} at block {block_number}: {e}")
            continue

    print(
        f"[info] {chain} Aave v3 snapshot at block {block_number}: "
        f"{len(rows)} reserves with balances"
    )
    return rows


def compute_balances_at_block(
    w3: Web3,
    csu_cfg: Dict[str, Any],
    block_number: int,
) -> List[Dict[str, Any]]:
    """
    Dispatch to the appropriate historical adapter based on protocol/version.

    For now this only supports Aave v3, but the interface is generic so we
    can add Compound/Morpho/etc. later without touching the main driver.
    """
    protocol = csu_cfg["protocol"].lower()
    version = str(csu_cfg.get("version", "")).lower()

    if protocol == "aave" and version == "v3":
        return compute_aave_v3_balances_at_block(w3, csu_cfg, block_number)

    print(f"[warn] no historical balances adapter for protocol={protocol} version={version}; skipping")
    return []


def load_csu_cfg(csu_key: str) -> Dict[str, Any]:
    """Load a single CSU entry from config/csu_config.yaml.

    The config file is typically structured as:

        csus:
          aave_v3_ethereum:
            ...
          aave_v3_polygon:
            ...

    so we look under the top-level "csus" mapping. If "csus" is missing,
    we fall back to treating the root mapping as the CSU map for robustness.
    """
    cfg_path = Path("config/csu_config.yaml")
    if not cfg_path.exists():
        raise SystemExit(f"[error] missing CSU config at {cfg_path}")

    root = yaml.safe_load(cfg_path.read_text()) or {}
    # Prefer the nested "csus" mapping, but allow flat configs too.
    all_csus = root.get("csus", root)

    if csu_key not in all_csus:
        raise SystemExit(f"[error] CSU '{csu_key}' not found in {cfg_path}")
    return all_csus[csu_key]


def main() -> None:
    """Historical TVL calculator (standalone, read-only w.r.t. tvl/).

    This script:
      * Uses the same NY-day convention as the liquidation pipeline
      * Maps each day to a closing UTC timestamp via ny_date_to_utc_window
      * Maps that timestamp to a block via block_for_ts
      * Emits, for now, just the (csu, date, block_number, ts_end_utc) mapping

    TVL-at-block computation will be layered on top of this mapping while
    keeping the main tvl/ code untouched.
    """

    ap = argparse.ArgumentParser("Historical TVL driver (block mapping only)")
    ap.add_argument("--csu", required=True, help="CSU key in config/csu_config.yaml")
    ap.add_argument("--from-date", required=True, help="Start NY date (YYYY-MM-DD)")
    ap.add_argument("--to-date", required=True, help="End NY date (YYYY-MM-DD, inclusive)")
    ap.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write CSV, just print mappings (useful for debugging)",
    )
    args = ap.parse_args()

    cfg = load_csu_cfg(args.csu)
    protocol = cfg["protocol"]
    chain = cfg["chain"]
    rpc_url = cfg["rpc"]
    out_root = Path(cfg.get("outputs_dir", f"out/{args.csu}_historical"))

    print(f"[info] CSU={args.csu} protocol={protocol} chain={chain}")
    print(f"[info] RPC={rpc_url}")
    print(f"[info] Date range NY: {args.from_date} → {args.to_date}")

    w3 = build_web3(chain, rpc_url)

    if args.no_write:
        map_csv = None
        map_writer = None
        tvl_csv = None
        tvl_writer = None
    else:
        out_root.mkdir(parents=True, exist_ok=True)

        # Block mapping CSV (date → block)
        map_csv = out_root / f"{args.csu}_block_mapping.csv"
        map_write_header = not map_csv.exists()
        map_f = open(map_csv, "a", newline="")
        map_writer = csv.writer(map_f)
        if map_write_header:
            map_writer.writerow([
                "date_ny",
                "chain",
                "protocol",
                "csu",
                "ts_start_utc",
                "ts_end_utc",
                "block_number",
            ])

        # Historical balances CSV (one row per reserve per date)
        tvl_csv = out_root / f"{args.csu}_tvl_history.csv"
        tvl_write_header = not tvl_csv.exists()
        tvl_f = open(tvl_csv, "a", newline="")
        tvl_writer = csv.writer(tvl_f)
        if tvl_write_header:
            tvl_writer.writerow([
                "date_ny",
                "chain",
                "protocol",
                "csu",
                "block_number",
                "asset",
                "a_token",
                "sd_token",
                "vd_token",
                "a_supply",
                "sd_supply",
                "vd_supply",
            ])

    # Iterate over NY dates and compute block mapping + historical balances
    for d_str in iterate_dates(args.from_date, args.to_date):
        ts_start_utc, ts_end_utc = ny_date_to_utc_window(d_str)
        b_close = block_for_ts(w3, ts_end_utc)
        block_number = max(1, b_close - 1)

        print(
            f"[info] {args.csu} {d_str}: ts_start_utc={ts_start_utc} "
            f"ts_end_utc={ts_end_utc} → block={block_number}"
        )

        if not args.no_write and map_writer is not None:
            map_writer.writerow([
                d_str,
                chain,
                protocol,
                args.csu,
                ts_start_utc,
                ts_end_utc,
                block_number,
            ])

        # For now, only Aave v3 is supported; other protocols will log a warning.
        if not args.no_write and tvl_writer is not None:
            balances = compute_balances_at_block(w3, cfg, block_number)
            for row in balances:
                tvl_writer.writerow([
                    d_str,
                    chain,
                    protocol,
                    args.csu,
                    block_number,
                    row.get("asset"),
                    row.get("a_token"),
                    row.get("sd_token"),
                    row.get("vd_token"),
                    row.get("a_supply"),
                    row.get("sd_supply"),
                    row.get("vd_supply"),
                ])

    if not args.no_write:
        # Close files if they were opened
        try:
            if 'map_f' in locals():
                map_f.close()
        except Exception:
            pass
        try:
            if 'tvl_f' in locals():
                tvl_f.close()
        except Exception:
            pass
        if map_csv is not None:
            print(f"[ok] wrote block mapping CSV to {map_csv}")
        if tvl_csv is not None:
            print(f"[ok] wrote TVL history CSV to {tvl_csv}")


def build_web3(chain: str, rpc_url: str) -> Web3:
    """
    Build a Web3 client for historical TVL, reusing the main TVL
    connect_rpc helper and adding PoA middleware for Polygon / similar chains.

    This keeps hist_tvl in sync with the existing TVL stack without modifying tvl/.
    """
    # Reuse the same RPC connection helper used by tvl.aggregator
    w3 = connect_rpc(rpc_url)

    # For Polygon and other PoA-style chains, Web3.py needs the PoA middleware
    # to handle longer extraData fields on blocks. We add this here rather than
    # touching tvl/ so that historical code can safely call get_block().
    chain_lc = (chain or "").lower()
    if chain_lc in ("polygon", "matic", "bsc", "gnosis", "arbitrum", "optimism"):
        # web3.py v7: use ExtraDataToPOAMiddleware instead of geth_poa_middleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    return w3


if __name__ == "__main__":
    main()