# liquid/adapters/justlend_tron.py

import os
from typing import Dict, Any, Iterable, List
import requests
from decimal import Decimal

from adapters.base import LiquidationAdapter  # your existing base

TRONGRID_BASE = os.environ.get("TRONGRID_BASE", "https://api.trongrid.io")

# JustLend Comptroller (for reference; we won't actually use it in v0)
JUSTLEND_COMPTROLLER = "TB23wYojvAsSx6gR8ebHiBqwSeABiBMPAr"

# Hard-code the jToken contracts you care about (fill this out from JustLend docs)
JTOKENS: Dict[str, str] = {
    # symbol: base58 contract address
    "jUSDT": "TXYZ123...",
    "jTRX":  "TABCD...",
    # TODO: add all relevant markets
}

# Minimal ABI fragments encoded as Tron function selectors
# On Tron, for constant calls we POST to /wallet/triggerconstantcontract with selector + encoded params.
# We'll keep it simple and just call standard Compound-style views with no params.
FUNCTION_SELECTORS = {
    "getCash": "3b1d21a2",         # bytes4(keccak256("getCash()"))
    "totalBorrows": "47bd3718",    # bytes4(keccak256("totalBorrows()"))
    "totalReserves": "8f840ddd",   # bytes4(keccak256("totalReserves()"))
    "decimals": "313ce567",        # bytes4(keccak256("decimals()"))
    "symbol": "95d89b41",          # bytes4(keccak256("symbol()"))
}