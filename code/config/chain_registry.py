
# chain_registry.py
# ------------------------------------------------------------
# Utilities for working with DeFiLlama Chainlist RPC endpoints.
#
# Features:
# - Downloads and parses the Chainlist RPC catalog
# - Normalizes chain lookups by name, shortName, or chainId
# - get_rpcs(key, ...) returns a list of candidate RPCs
# - get_rpc(key, ...) returns a single RPC (with simple rotation options)
# - Optional health-check to prefer alive endpoints (eth_blockNumber)
# - Simple CLI for quick lookups
#
# Usage (Python):
#   from chain_registry import ChainRegistry
#   reg = ChainRegistry()                 # loads data from Chainlist
#   print(reg.get_rpcs('Polygon'))        # list of RPCs for Polygon
#   print(reg.get_rpc(1))                 # one RPC for Ethereum mainnet
#
# CLI:
#   python chain_registry.py --find Polygon
#   python chain_registry.py --find 137 --one
#   python chain_registry.py --list | head
#
# Notes:
# - Requires: requests
# - Default sources:
#       https://chainlist.org/rpcs.json
#       https://raw.githubusercontent.com/DefiLlama/chainlist/main/rpcs.json
# ------------------------------------------------------------

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import requests
except ImportError as e:
    raise SystemExit("This module requires the 'requests' package. Install with: pip install requests") from e

DEFAULT_SOURCES = [
    "https://chainlist.org/rpcs.json",
    "https://raw.githubusercontent.com/DefiLlama/chainlist/main/rpcs.json",
]

# Minimal EVM JSON-RPC call payload for health checking
ETH_BLOCK_NUMBER = {
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": 1,
}

@dataclass
class ChainRecord:
    chain_id: int
    name: str
    short_name: Optional[str]
    native_currency: Optional[Dict[str, Any]]
    rpcs: List[str]
    explorers: List[str]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ChainRecord":
        # Chainlist uses keys like: chainId, name, shortName, nativeCurrency, explorers, rpc
        # Some fields may be absent depending on the chain entry.
        chain_id = int(d.get("chainId"))
        name = d.get("name") or d.get("title") or str(chain_id)
        short_name = d.get("shortName")
        rpcs: List[str] = []
        # RPC entries can be strings or objects with 'url' and maybe 'tracking' fields.
        for entry in d.get("rpc", []):
            if isinstance(entry, str):
                rpcs.append(entry.strip())
            elif isinstance(entry, dict) and "url" in entry:
                rpcs.append(str(entry["url"]).strip())
        # Explorer entries can be strings or objects with 'url'
        explorers: List[str] = []
        for ex in d.get("explorers", []):
            if isinstance(ex, str):
                explorers.append(ex.strip())
            elif isinstance(ex, dict) and "url" in ex:
                explorers.append(str(ex["url"]).strip())
        return ChainRecord(
            chain_id=chain_id,
            name=name,
            short_name=short_name,
            native_currency=d.get("nativeCurrency"),
            rpcs=rpcs,
            explorers=explorers,
        )

class ChainRegistry:
    def __init__(
        self,
        sources: Optional[List[str]] = None,
        timeout: float = 7.0,
        prefer_https: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        """Load Chainlist RPC data into memory.

        :param sources: List of JSON endpoints to try (defaults to DEFAULT_SOURCES).
        :param timeout: Per-request timeout when fetching the catalog or health checks.
        :param prefer_https: If True, prioritize https RPCs over http.
        :param seed: Random seed for deterministic 'random' RPC selection.
        """
        self.sources = sources or list(DEFAULT_SOURCES)
        self.timeout = timeout
        self.prefer_https = prefer_https
        self._records: Dict[int, ChainRecord] = {}
        self._index_by_name: Dict[str, int] = {}
        self._index_by_short: Dict[str, int] = {}

        if seed is not None:
            random.seed(seed)

        data = self._fetch_catalog()
        self._ingest(data)

    def _fetch_catalog(self) -> List[Dict[str, Any]]:
        last_err = None
        for url in self.sources:
            try:
                resp = requests.get(url, timeout=self.timeout)
                resp.raise_for_status()
                # Some sources return an object with 'chains' field, others a raw list.
                payload = resp.json()
                if isinstance(payload, dict) and "chains" in payload:
                    return payload["chains"]
                if isinstance(payload, list):
                    return payload
            except Exception as e:
                last_err = e
        raise RuntimeError(f"Failed to fetch Chainlist RPC catalog from all sources. Last error: {last_err}")

    def _ingest(self, chains: List[Dict[str, Any]]) -> None:
        for d in chains:
            try:
                rec = ChainRecord.from_dict(d)
            except Exception:
                continue
            self._records[rec.chain_id] = rec
            # Build case-insensitive indices for robustness
            self._index_by_name[rec.name.lower()] = rec.chain_id
            if rec.short_name:
                self._index_by_short[str(rec.short_name).lower()] = rec.chain_id

    # -------------- Public API --------------

    def normalize_key(self, key: Union[str, int]) -> int:
        """Accepts chainId (int or numeric str), chain 'name', or 'shortName'. Returns chainId (int)."""
        if isinstance(key, int):
            if key in self._records:
                return key
            raise KeyError(f"Unknown chainId: {key}")
        # If numeric string, parse as chainId
        key_str = str(key).strip()
        if key_str.isdigit():
            cid = int(key_str)
            if cid in self._records:
                return cid
            raise KeyError(f"Unknown chainId: {cid}")
        # Try case-insensitive name / shortName
        lowered = key_str.lower()
        if lowered in self._index_by_name:
            return self._index_by_name[lowered]
        if lowered in self._index_by_short:
            return self._index_by_short[lowered]
        # Support common aliases
        aliases = {
            "eth": "ethereum",
            "polygon": "polygon",
            "matic": "polygon",
            "bsc": "binance smart chain",
            "avax": "avalanche",
            "arb": "arbitrum one",
            "op": "optimism",
            "base": "base",
        }
        if lowered in aliases and aliases[lowered] in self._index_by_name:
            return self._index_by_name[aliases[lowered]]
        raise KeyError(f"Could not resolve chain key: {key}")

    def get_chain(self, key: Union[str, int]) -> ChainRecord:
        cid = self.normalize_key(key)
        return self._records[cid]

    def get_rpcs(
        self,
        key: Union[str, int],
        require_https: Optional[bool] = None,
        healthy_only: bool = False,
        max_to_check: Optional[int] = None,
    ) -> List[str]:
        """Return a filtered list of RPC URLs for the chain.

        :param require_https: If True, return only https RPCs. If False, allow http. If None, use self.prefer_https to sort but not filter.
        :param healthy_only: If True, probe endpoints with eth_blockNumber and keep only those that respond.
        :param max_to_check: If healthy_only, limit number of endpoints to probe for speed.
        """
        rec = self.get_chain(key)
        rpcs = list(rec.rpcs)  # copy
        if require_https is True:
            rpcs = [u for u in rpcs if u.startswith("https://")]
        elif require_https is None:
            # Sort so https endpoints come first (but keep http as fallback)
            rpcs.sort(key=lambda u: (not u.startswith("https://"), u))

        if healthy_only:
            checked = []
            to_probe = rpcs if max_to_check is None else rpcs[:max_to_check]
            for url in to_probe:
                if self._rpc_is_healthy(url):
                    checked.append(url)
            # If we probed a subset and found none healthy, fall back to unfiltered rpcs
            rpcs = checked if checked else rpcs
        return rpcs

    def get_rpc(
        self,
        key: Union[str, int],
        strategy: str = "first",
        require_https: Optional[bool] = None,
        healthy_only: bool = False,
    ) -> str:
        """Return a single RPC URL for the chain.

        :param strategy: 'first' (default), 'random', or 'round_robin' (stateless by env var/seed).
        """
        rpcs = self.get_rpcs(key, require_https=require_https, healthy_only=healthy_only)
        if not rpcs:
            raise RuntimeError(f"No RPCs found for chain: {key}")
        if strategy == "first":
            return rpcs[0]
        if strategy == "random":
            return random.choice(rpcs)
        if strategy == "round_robin":
            idx = int(time.time()) % len(rpcs)  # simple stateless rotation by seconds
            return rpcs[idx]
        raise ValueError("strategy must be one of: 'first', 'random', 'round_robin'")

    def get_explorers(self, key: Union[str, int]) -> List[str]:
        rec = self.get_chain(key)
        return list(rec.explorers)

    def list_chains(self) -> List[Tuple[int, str, Optional[str]]]:
        """Return [(chainId, name, shortName), ...] sorted by chainId."""
        rows = [(rec.chain_id, rec.name, rec.short_name) for rec in self._records.values()]
        return sorted(rows, key=lambda r: r[0])

    # -------------- Internals --------------

    def _rpc_is_healthy(self, url: str) -> bool:
        try:
            # Some public RPCs require POST with JSON; we keep it minimal.
            resp = requests.post(url, json=ETH_BLOCK_NUMBER, timeout=self.timeout)
            if resp.status_code != 200:
                return False
            data = resp.json()
            # Expect a hex string like '0xabc...'
            result = data.get("result")
            return isinstance(result, str) and result.startswith("0x")
        except Exception:
            return False


# ------------------ CLI ------------------

def _cli() -> int:
    p = argparse.ArgumentParser(description="Query DeFiLlama Chainlist RPCs.")
    p.add_argument("--find", metavar="KEY", help="Chain key: chainId (e.g. 1), name (e.g. Polygon), or shortName (e.g. matic)")
    p.add_argument("--one", action="store_true", help="Return a single RPC instead of a list")
    p.add_argument("--strategy", default="first", choices=["first", "random", "round_robin"], help="Selection strategy when --one is used")
    p.add_argument("--https-only", action="store_true", help="Require https RPCs only")
    p.add_argument("--healthy", action="store_true", help="Probe endpoints and keep only healthy ones (slower)" )
    p.add_argument("--max-check", type=int, default=None, help="When --healthy, limit number of endpoints to probe" )
    p.add_argument("--list", action="store_true", help="List known chains (chainId, name, shortName) and exit")
    p.add_argument("--seed", type=int, default=None, help="Random seed for deterministic 'random' strategy" )
    args = p.parse_args()

    reg = ChainRegistry(seed=args.seed)

    if args.list:
        for cid, name, short in reg.list_chains():
            short_disp = f" ({short})" if short else ""
            print(f"{cid:6d}  {name}{short_disp}")
        return 0

    if not args.find:
        p.print_help()
        return 2

    key = args.find
    require_https = True if args.https_only else None

    if args.one:
        rpc = reg.get_rpc(key, strategy=args.strategy, require_https=require_https, healthy_only=args.healthy)
        print(rpc)
        return 0
    else:
        rpcs = reg.get_rpcs(key, require_https=require_https, healthy_only=args.healthy, max_to_check=args.max_check)
        for u in rpcs:
            print(u)
        return 0

if __name__ == "__main__":
    sys.exit(_cli())
