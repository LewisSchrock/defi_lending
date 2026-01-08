# # liquid/adapters/kamino_lend.py

# from typing import Dict, Any, List
# from pathlib import Path
# import json

# from solana.rpc.api import Client
# from solders.pubkey import Pubkey


# """
# TVL adapter for Kamino Lend on Solana.

# Design:
# - Off-chain pre-step: config/utils/kamino/ts/dump_kamino_reserves.ts uses the
#   official @kamino-finance/klend-sdk to dump all reserves for the main
#   Kamino market into kamino_markets_main.json with fields:
#     symbol, underlying_mint, vault, decimals.
# did u fix'
# - At runtime, this adapter:
#   * loads that JSON mapping
#   * uses Solana RPC get_multiple_accounts on the vault SPL token accounts
#   * extracts tokenAmount.amount for each vault
#   * returns a list of standardized rows for your TVL pipeline.
# """

# # code/ (project root) is two levels up from tvl/adapters/
# PROJECT_ROOT = Path(__file__).resolve().parents[2]
# KAMINO_MARKETS_JSON = (
#     PROJECT_ROOT / "config" / "utils" / "kamino" / "ts" / "kamino_markets_main.json"
# )


# with KAMINO_MARKETS_JSON.open() as f:
#     # e.g. { "USDC": {"symbol": "USDC", "underlying_mint": "...", "vault": "...", "decimals": 6}, ... }
#     KAMINO_MARKETS: Dict[str, Dict[str, Any]] = json.load(f)


# def _fetch_token_account_balances(
#     client: Client,
#     accounts: List[str],
# ) -> Dict[str, Dict[str, Any]]:
#     """
#     Fetch SPL token account data for a list of vaults using jsonParsed encoding.
#     Returns a dict mapping vault pubkey (string) -> account info dict.
#     """
#     if not accounts:
#         return {}

#     out: Dict[str, Dict[str, Any]] = {}
#     chunk_size = 10

#     for i in range(0, len(accounts), chunk_size):
#         chunk = accounts[i : i + chunk_size]

#         resp = client.get_multiple_accounts(
#             pubkeys=[Pubkey.from_string(a) for a in chunk],
#             encoding="jsonParsed",
#             commitment="confirmed",
#         )
#         result = resp.get("result")
#         if result is None or "value" not in result:
#             raise RuntimeError(f"Unexpected get_multiple_accounts response for chunk {chunk}: {resp}")

#         value = result["value"]
#         for acc_info, pubkey_str in zip(value, chunk):
#             if acc_info is None:
#                 continue
#             out[pubkey_str] = acc_info

#     return out


# def get_kamino_lend_tvl_raw(rpc_url: str, registry: str) -> List[Dict[str, Any]]:
#     """
#     Return per-reserve raw TVL snapshot for Kamino Lend main market.

#     Parameters
#     ----------
#     rpc_url : str
#         Solana RPC endpoint.
#     registry : str
#         Kamino market address; currently ignored because we dump a single main market
#         to kamino_markets_main.json, but kept for signature compatibility.

#     Returns
#     -------
#     List[Dict[str, Any]]
#         Each row has: symbol, underlying_mint, vault, decimals, raw_amount.
#     """
#     client = Client(rpc_url)

#     # Unique list of vault token accounts from the dumped JSON
#     vault_accounts: List[str] = [meta["vault"] for meta in KAMINO_MARKETS.values()]
#     balances_by_vault = _fetch_token_account_balances(client, vault_accounts)

#     rows: List[Dict[str, Any]] = []
#     for symbol, meta in KAMINO_MARKETS.items():
#         vault = meta["vault"]
#         acc_info = balances_by_vault.get(vault)
#         if acc_info is None:
#             # account missing; skip but you could log this if desired
#             continue

#         try:
#             # jsonParsed SPL token account layout:
#             # data -> parsed -> info -> tokenAmount -> amount
#             token_amount_str = (
#                 acc_info["data"]["parsed"]["info"]["tokenAmount"]["amount"]
#             )
#             raw_amount = int(token_amount_str)
#         except Exception:
#             # If parsing fails, skip this reserve rather than crashing the whole run
#             continue

#         rows.append(
#             {
#                 "symbol": symbol,
#                 "underlying_mint": meta["underlying_mint"],
#                 "vault": vault,
#                 "decimals": int(meta["decimals"]),
#                 "raw_amount": raw_amount,
#             }
#         )

#     return rows





from typing import Dict, Any, List
from pathlib import Path
import json
import requests

# code/ (project root) is two levels up from tvl/adapters/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
KAMINO_MARKETS_JSON = (
    PROJECT_ROOT / "config" / "utils" / "kamino" / "ts" / "kamino_markets_main.json"
)

with KAMINO_MARKETS_JSON.open() as f:
    KAMINO_MARKETS: Dict[str, Dict[str, Any]] = json.load(f)


def get_kamino_lend_tvl_raw(rpc_url: str, registry: str) -> List[Dict[str, Any]]:
    """
    Temporary, ultra-simple TVL snapshot for Kamino Lend main market.

    - Uses direct JSON-RPC (requests) with encoding="jsonParsed"
    - Chunks vaults into batches of 10
    - Returns: symbol, underlying_mint, vault, decimals, raw_amount
    """
    vault_accounts: List[str] = [meta["vault"] for meta in KAMINO_MARKETS.values()]

    rows: List[Dict[str, Any]] = []
    chunk_size = 10

    for i in range(0, len(vault_accounts), chunk_size):
        chunk = vault_accounts[i : i + chunk_size]

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getMultipleAccounts",
            "params": [
                chunk,
                {
                    "encoding": "jsonParsed",
                    "commitment": "confirmed",
                },
            ],
        }

        resp = requests.post(rpc_url, json=payload, timeout=30)
        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError(
                f"Non-JSON response from Solana RPC: status={resp.status_code}, "
                f"text={resp.text[:200]}"
            ) from e

        if "error" in data:
            raise RuntimeError(f"Error from Solana RPC for chunk {chunk}: {data['error']}")

        result = data.get("result")
        if result is None or "value" not in result:
            raise RuntimeError(
                f"Unexpected getMultipleAccounts response for chunk {chunk}: {data}"
            )

        value = result["value"]
        for acc_info, vault_addr in zip(value, chunk):
            if acc_info is None:
                continue

            try:
                token_amount_str = (
                    acc_info["data"]["parsed"]["info"]["tokenAmount"]["amount"]
                )
                raw_amount = int(token_amount_str)
            except Exception:
                continue

            # find symbol/meta by matching vault
            meta = next(
                (m for m in KAMINO_MARKETS.values() if m["vault"] == vault_addr),
                None,
            )
            if meta is None:
                continue

            rows.append(
                {
                    "symbol": meta["symbol"],
                    "underlying_mint": meta["underlying_mint"],
                    "vault": vault_addr,
                    "decimals": int(meta["decimals"]),
                    "raw_amount": raw_amount,
                }
            )

    return rows