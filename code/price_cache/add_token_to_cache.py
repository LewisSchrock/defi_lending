#!/usr/bin/env python3
"""
add_token_to_cache.py

Discover new token addresses (from events and pricing request files), look up a
pricing identifier by contract on CoinGecko for the appropriate chain, and
append `price_id: coingecko:<slug>` into token_registry.yaml for any address
missing one.

Usage (zero-arg, run from repo root):
    python3 add_token_to_cache.py

Environment assumptions:
- token_registry.yaml at repo root
- events CSV at ./out/aave_v3_<chain>/liquidation_events.csv (default chain=ethereum)
- request files at ./pricing/requests/missing_{chain}_{addr}.csv
"""
import sys
import time
from pathlib import Path
from typing import Dict, Tuple, Set
import os
from collections.abc import Mapping
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput, ContractLogicError

import pandas as pd
import requests
import yaml
from collections import OrderedDict

# ------- Defaults (edit if needed) -------------------------------------------
ROOT = Path.cwd()
CHAIN = "ethereum"
TOKEN_REG = ROOT / "token_registry.yaml"
REQUESTS_DIR = ROOT / "pricing" / "requests"
EVENTS = ROOT / "out" / f"aave_v3_{CHAIN}" / "liquidation_events.csv"

# Map our CHAIN string to CoinGecko's platform slug for contract lookup
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

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol",   "outputs": [{"name": "", "type": "string"}], "type": "function"},
]

# polite rate limiting per domain
_LAST_CALL: Dict[str, float] = {}
_MIN_INTERVAL = {"coingecko": 1.2}

def _rate_limit(key: str) -> None:
    now = time.time()
    last = _LAST_CALL.get(key, 0.0)
    delay = max(0.0, _MIN_INTERVAL.get(key, 0.0) - (now - last))
    if delay > 0:
        time.sleep(delay)
    _LAST_CALL[key] = time.time()

# ------- Core helpers ---------------------------------------------------------

def load_registry(path: Path) -> Dict[str, dict]:
    if not path.exists():
        print(f"[error] token registry not found: {path}")
        sys.exit(1)
    reg_raw = yaml.safe_load(path.read_text()) or {}
    return {str(k).lower(): (dict(v) if isinstance(v, Mapping) else v) for k, v in reg_raw.items()}

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

def discover_addresses(events_csv: Path, requests_dir: Path) -> Set[str]:
    addrs: Set[str] = set()
    # From request filenames
    if requests_dir.exists():
        for p in requests_dir.glob("missing_*.csv"):
            try:
                _, addr = parse_request_filename(p)
                addrs.add(addr)
            except Exception:
                continue
    # From events CSV
    try:
        ev = pd.read_csv(events_csv, usecols=["collateral_token", "debt_token"])  # light read
        for col in ("collateral_token", "debt_token"):
            if col in ev.columns:
                addrs.update(map(str.lower, ev[col].dropna().astype(str).tolist()))
    except Exception:
        pass
    return {a for a in addrs if a.startswith("0x") and len(a) == 42}

def fetch_coingecko_id_for_contract(chain: str, addr: str) -> str | None:
    platform = COINGECKO_PLATFORM.get(chain.lower())
    if not platform:
        return None
    url = f"https://api.coingecko.com/api/v3/coins/{platform}/contract/{addr.lower()}"
    _rate_limit("coingecko")
    r = requests.get(url, timeout=30)
    if r.status_code == 429:
        time.sleep(2.0)
        _rate_limit("coingecko")
        r = requests.get(url, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    data = r.json()
    return data.get("id")  # e.g., 'usd-coin'

def write_registry_atomic(path: Path, reg: Dict[str, dict]) -> None:
    # Normalize: lowercase string keys; plain dict values
    cleaned: Dict[str, dict] = {str(k).lower(): (dict(v) if isinstance(v, Mapping) else v) for k, v in reg.items()}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(cleaned, sort_keys=True))
    os.replace(tmp, path)

def ensure_price_ids(reg_path: Path, reg: Dict[str, dict], chain: str, addrs: Set[str]) -> Dict[str, dict]:
    """For any address in `addrs` missing a price_id, try to look it up on CoinGecko
    by contract and write back to token_registry.yaml if we add anything."""
    updated = False
    for addr in sorted(addrs):
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
    else:
        print("[registry] no new price_id entries discovered")
    return reg

def get_rpc_url() -> str:
    # Reuse the same env var(s) you already use elsewhere; prefer ETH_RPC_URL if present
    for key in ("ETH_RPC_URL", "ALCHEMY_MAINNET_URL", "RPC_URL"):
        val = os.getenv(key)
        if val:
            return val
    return ""

def get_w3(rpc_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        raise RuntimeError(f"RPC not connected: {rpc_url}")
    return w3

def fetch_erc20_decimals_and_symbol(w3: Web3, addr: str) -> Tuple[int | None, str | None]:
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
        try:
            dec = c.functions.decimals().call()
        except (BadFunctionCallOutput, ContractLogicError):
            dec = None
        sym = None
        try:
            sym = c.functions.symbol().call()
            if isinstance(sym, bytes):
                sym = sym.decode(errors="ignore")
        except (BadFunctionCallOutput, ContractLogicError, ValueError):
            sym = None
        return dec, sym
    except Exception:
        return None, None

def ensure_decimals_via_rpc(reg_path: Path, reg: Dict[str, dict], addrs: Set[str], rpc_url: str) -> Dict[str, dict]:
    if not rpc_url:
        print("[warn] No RPC URL set (ETH_RPC_URL). Skipping decimals lookup.")
        return reg
    try:
        w3 = get_w3(rpc_url)
    except Exception as e:
        print(f"[warn] Cannot connect to RPC: {e}. Skipping decimals lookup.")
        return reg

    updated = False
    for addr in sorted(addrs):
        meta = reg.get(addr) if isinstance(reg.get(addr), dict) else {}
        need_dec = (not meta) or ("decimals" not in meta)
        need_sym = (not meta) or ("symbol" not in meta)
        if not (need_dec or need_sym):
            continue
        dec, sym = fetch_erc20_decimals_and_symbol(w3, addr)
        if dec is not None:
            meta = dict(meta) if isinstance(meta, dict) else {}
            meta["decimals"] = int(dec)
            updated = True
            print(f"[registry] decimals {addr} → {dec}")
        if sym:
            meta = dict(meta) if isinstance(meta, dict) else {}
            meta["symbol"] = sym
            updated = True
            print(f"[registry] symbol {addr} → {sym}")
        if updated:
            reg[addr] = meta
            write_registry_atomic(reg_path, reg)
            updated = False
    return reg

# ------- CLI entrypoint ------------------------------------------------------

def main() -> None:
    reg = load_registry(TOKEN_REG)
    addrs = discover_addresses(EVENTS, REQUESTS_DIR)
    if not addrs:
        print("[info] no token addresses discovered from events/requests; nothing to do")
        return
    reg = ensure_price_ids(TOKEN_REG, reg, CHAIN, addrs)
    # New: fill decimals/symbol via RPC
    rpc_url = get_rpc_url()
    reg = ensure_decimals_via_rpc(TOKEN_REG, reg, addrs, rpc_url)

if __name__ == "__main__":
    main()