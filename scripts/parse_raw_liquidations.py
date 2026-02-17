#!/usr/bin/env python3
"""
Parse Raw Liquidation Events

Converts raw eth_getLogs output to parsed format with protocol-specific fields.
Works offline using blockTimestamp already in the data.

Usage:
    python scripts/parse_raw_liquidations.py --chain optimism
    python scripts/parse_raw_liquidations.py --chain all  # All chains with raw data
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Event signatures (topic0) for different protocols
EVENT_SIGNATURES = {
    # Aave V3 / SparkLend / Tydro: LiquidationCall(address,address,address,uint256,uint256,address,bool)
    "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286": "aave_v3",
    # Compound V3: AbsorbCollateral(address,address,address,uint256,uint256)
    "0x9850ab1af75177e4a7e9870da8a34d4979b71cc4cd596df22ba4fb8b571430b9": "compound_v3_collateral",
    # Compound V3: AbsorbDebt(address,address,uint256,uint256) — FIX: was missing
    "0x1547a878dc89ad3c367b6338b4be6a65a5dd74fb77ae044da1e8747ef1f4f62f": "compound_v3_debt",
    # Compound V2 / Venus / Benqi / Moonwell / Kinetic / Sumer: LiquidateBorrow(address,address,uint256,address,uint256)
    "0x298637f684da70674f26509b10f07ec2fbc77a335ab1e7d6215a4b2484d8bb52": "compound_v2",
    # Fluid: Liquidation(address,address,address,address,uint256,uint256) — FIX: was wrong signature
    "0x64f7c2c46814e079964a1934953e50adc025dc52cdbeb7d8e478e9fb9bfd2c2d": "fluid",
    # Gearbox: LiquidateCreditAccount(address,address,address,uint256)
    "0x7dfecd8419723a9d3954585a30c2a270165d70aafa146c11c1e1b88ae1439064": "gearbox",
    # Cap: Liquidate(address,address,uint256,uint256)
    "0xf3fa0eaee8f258c23b013654df25d1527f98a5c7ccd5e951dd77caca400ef972": "cap",
    # Lista (Morpho-style): Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)
    "0xa4946ede45d0c6f06a0f5ce92c9ad3b4751452d2fe0e25010783bcab57a67e41": "lista",
}

# === CSU Name Resolution ===
# Compound V3: each Comet contract is a specific isolated market
# Keyed by (address, chain) for addresses deployed on multiple chains
COMPOUND_V3_COMET_TO_CSU = {
    # Ethereum
    ("0xc3d688b66703497daa19211eedff47f25384cdc3", "ethereum"): "compound_v3_eth_usdc",
    ("0xa17581a9e3356d9a858b789d68b4d866e593ae94", "ethereum"): "compound_v3_eth_weth",
    ("0x3afdc9bca9213a35503b077a6072f3d0d5ab0840", "ethereum"): "compound_v3_eth_usdt",
    ("0x3d0bb1ccab520a66e607822fc55bc921738fafe3", "ethereum"): "compound_v3_eth_wsteth",
    ("0x5d409e56d886231adaf00c8775665ad0f9897b56", "ethereum"): "compound_v3_eth_usds",
    # Arbitrum
    ("0x9c4ec768c28520b50860ea7a15bd7213a9ff58bf", "arbitrum"): "compound_v3_arb_usdc",
    ("0xa5edbdd9646f8dff606d7448e414884c7d905dca", "arbitrum"): "compound_v3_arb_usdc_e",
    ("0x6f7d514bbd4aff3bcd1140b7344b32f063dee486", "arbitrum"): "compound_v3_arb_weth",
    ("0xd98be00b5d27fc98112bde293e487f8d4ca57d07", "arbitrum"): "compound_v3_arb_usdt",
    # Base
    ("0xb125e6687d4313864e53df431d5425969c15eb2f", "base"): "compound_v3_base_usdc",
    ("0x9c4ec768c28520b50860ea7a15bd7213a9ff58bf", "base"): "compound_v3_base_usdbc",
    ("0x46e6b214b524310239732d51387075e0e70970bf", "base"): "compound_v3_base_weth",
    ("0x784efeb622244d2348d4f2522f8860b96fbece89", "base"): "compound_v3_base_aero",
    # Optimism
    ("0x2e44e174f7d53f0212823acc11c01a11d58c5bcb", "optimism"): "compound_v3_op_usdc",
    ("0x995e394b8b2437ac8ce61ee0bc610d617962b214", "optimism"): "compound_v3_op_usdt",
    ("0xe36a30d249f7761327fd973001a32010b521b6fd", "optimism"): "compound_v3_op_weth",
    # Polygon
    ("0xf25212e676d1f7f89cd72ffee66158f541246445", "polygon"): "compound_v3_poly_usdc",
}

# Aave V3: special Pool addresses for SparkLend and Tydro
AAVE_SPECIAL_POOLS = {
    # SparkLend on Ethereum
    "0xc13e21b648a5ee794902342038ff3adab66be987": "sparklend_ethereum",
    # Tydro on Ink
    "0x2816cf15f6d2a220e789aa011d5ee4eb6c47feba": "tydro_ink",
}

# Compound V2-style: chain → CSU name (primary fork per chain)
COMPOUND_V2_CHAIN_MAP = {
    "base": "moonwell_lending_base",
    "bsc": "venus_core_pool_binance",
    "avalanche": "benqi_lending_avalanche",
    "flare": "kinetic_flare",
    "meter": "sumermoney_meter",
    "ethereum": "compound_v2_ethereum",
    "linea": "mendi_lending_linea",
    "arbitrum": "lodestar_lending_arbitrum",
    "optimism": "sonne_lending_optimism",
    "polygon": "keom_lending_polygon",
    "scroll": "layerbank_lending_scroll",
    "gnosis": "agave_lending_xdai",  # Agave is Aave V2-style, only 59 events
}


def resolve_csu(protocol: str, chain: str, contract: str) -> str:
    """Resolve the canonical CSU name from protocol, chain, and contract address."""
    contract = contract.lower()

    if protocol == "compound_v3":
        key = (contract, chain)
        if key in COMPOUND_V3_COMET_TO_CSU:
            return COMPOUND_V3_COMET_TO_CSU[key]
        return f"compound_v3_{chain}"

    if protocol == "aave_v3":
        if contract in AAVE_SPECIAL_POOLS:
            return AAVE_SPECIAL_POOLS[contract]
        # Normalize chain names to match vol_util convention
        chain_name = {"bsc": "binance", "gnosis": "xdai"}.get(chain, chain)
        return f"aave_v3_{chain_name}"

    if protocol == "compound_v2":
        return COMPOUND_V2_CHAIN_MAP.get(chain, f"compound_v2_{chain}")

    if protocol == "fluid":
        return f"fluid_lending_{chain}"

    if protocol == "gearbox":
        return f"gearbox_{chain}"

    if protocol == "cap":
        return f"cap_{chain}"

    if protocol == "lista":
        return f"lista_lending_{chain}"

    return f"{protocol}_{chain}"


# Input/output directories
INPUT_DIR = Path("data/bronze/liquidations")
OUTPUT_DIR = Path("data/bronze/liquidations")  # Same dir, will create parsed/ subfolder


def hex_to_int(hex_str: str) -> int:
    """Convert hex string to int."""
    if isinstance(hex_str, int):
        return hex_str
    return int(hex_str, 16)


def decode_address(hex_str: str) -> str:
    """Decode address from 32-byte padded hex."""
    # Remove 0x prefix and take last 40 chars (20 bytes)
    return "0x" + hex_str[-40:].lower()


def decode_uint256(hex_str: str) -> int:
    """Decode uint256 from hex."""
    return int(hex_str, 16)


def decode_bool(hex_str: str) -> bool:
    """Decode bool from hex."""
    return int(hex_str, 16) != 0


def parse_aave_v3(event: Dict) -> Dict:
    """
    Parse Aave V3 LiquidationCall event.

    Event: LiquidationCall(
        address indexed collateralAsset,
        address indexed debtAsset,
        address indexed user,
        uint256 debtToCover,
        uint256 liquidatedCollateralAmount,
        address liquidator,
        bool receiveAToken
    )
    """
    topics = event.get("topics", [])
    data = event.get("data", "0x")

    # Indexed params are in topics[1], topics[2], topics[3]
    collateral_asset = decode_address(topics[1]) if len(topics) > 1 else None
    debt_asset = decode_address(topics[2]) if len(topics) > 2 else None
    borrower = decode_address(topics[3]) if len(topics) > 3 else None

    # Non-indexed params are in data (remove 0x prefix)
    data_hex = data[2:] if data.startswith("0x") else data

    # Each param is 32 bytes (64 hex chars)
    debt_repaid = decode_uint256(data_hex[0:64]) if len(data_hex) >= 64 else 0
    collateral_seized = decode_uint256(data_hex[64:128]) if len(data_hex) >= 128 else 0
    liquidator = decode_address(data_hex[128:192]) if len(data_hex) >= 192 else None
    receive_a_token = decode_bool(data_hex[192:256]) if len(data_hex) >= 256 else False

    return {
        "protocol": "aave_v3",
        "event_name": "LiquidationCall",
        "collateral_asset": collateral_asset,
        "debt_asset": debt_asset,
        "borrower": borrower,
        "debt_repaid_raw": debt_repaid,
        "collateral_seized_raw": collateral_seized,
        "liquidator": liquidator,
        "receive_a_token": receive_a_token,
    }


def parse_compound_v3_collateral(event: Dict) -> Dict:
    """
    Parse Compound V3 AbsorbCollateral event.

    Event: AbsorbCollateral(
        address indexed absorber,
        address indexed borrower,
        address indexed asset,
        uint256 collateralAbsorbed,
        uint256 usdValue
    )
    """
    topics = event.get("topics", [])
    data = event.get("data", "0x")

    absorber = decode_address(topics[1]) if len(topics) > 1 else None
    borrower = decode_address(topics[2]) if len(topics) > 2 else None
    asset = decode_address(topics[3]) if len(topics) > 3 else None

    data_hex = data[2:] if data.startswith("0x") else data
    collateral_absorbed = decode_uint256(data_hex[0:64]) if len(data_hex) >= 64 else 0
    usd_value = decode_uint256(data_hex[64:128]) if len(data_hex) >= 128 else 0

    return {
        "protocol": "compound_v3",
        "event_name": "AbsorbCollateral",
        "collateral_asset": asset,
        "debt_asset": None,
        "borrower": borrower,
        "debt_repaid_raw": 0,
        "collateral_seized_raw": collateral_absorbed,
        "liquidator": absorber,
        "receive_a_token": False,
        "usd_value_raw": usd_value,
    }


def parse_compound_v3_debt(event: Dict) -> Dict:
    """
    Parse Compound V3 AbsorbDebt event.

    Event: AbsorbDebt(
        address indexed absorber,
        address indexed borrower,
        uint256 basePaidOut,
        uint256 usdValue
    )
    """
    topics = event.get("topics", [])
    data = event.get("data", "0x")

    absorber = decode_address(topics[1]) if len(topics) > 1 else None
    borrower = decode_address(topics[2]) if len(topics) > 2 else None

    data_hex = data[2:] if data.startswith("0x") else data
    base_paid_out = decode_uint256(data_hex[0:64]) if len(data_hex) >= 64 else 0
    usd_value = decode_uint256(data_hex[64:128]) if len(data_hex) >= 128 else 0

    return {
        "protocol": "compound_v3",
        "event_name": "AbsorbDebt",
        "collateral_asset": None,
        "debt_asset": None,
        "borrower": borrower,
        "debt_repaid_raw": base_paid_out,
        "collateral_seized_raw": 0,
        "liquidator": absorber,
        "receive_a_token": False,
        "usd_value_raw": usd_value,
    }


def parse_compound_v2(event: Dict) -> Dict:
    """
    Parse Compound V2 / Venus / Benqi / Moonwell / Kinetic / Sumer LiquidateBorrow event.

    Event: LiquidateBorrow(
        address liquidator,
        address borrower,
        uint256 repayAmount,
        address cTokenCollateral,
        uint256 seizeTokens
    )

    NOTE: Two ABI variants exist in the wild:
      - Standard Compound V2: liquidator & borrower are INDEXED (3 topics, 3 data params)
      - Some forks (Moonwell, etc.): NO indexed params (1 topic, 5 data params)
    We detect the format by counting topics.
    """
    topics = event.get("topics", [])
    data = event.get("data", "0x")
    data_hex = data[2:] if data.startswith("0x") else data

    if len(topics) >= 3:
        # Standard layout: 2 indexed params in topics, 3 in data
        liquidator = decode_address(topics[1])
        borrower = decode_address(topics[2])
        repay_amount = decode_uint256(data_hex[0:64]) if len(data_hex) >= 64 else 0
        collateral_token = decode_address(data_hex[64:128]) if len(data_hex) >= 128 else None
        seize_tokens = decode_uint256(data_hex[128:192]) if len(data_hex) >= 192 else 0
    else:
        # Non-indexed layout: all 5 params in data
        liquidator = decode_address(data_hex[0:64]) if len(data_hex) >= 64 else None
        borrower = decode_address(data_hex[64:128]) if len(data_hex) >= 128 else None
        repay_amount = decode_uint256(data_hex[128:192]) if len(data_hex) >= 192 else 0
        collateral_token = decode_address(data_hex[192:256]) if len(data_hex) >= 256 else None
        seize_tokens = decode_uint256(data_hex[256:320]) if len(data_hex) >= 320 else 0

    return {
        "protocol": "compound_v2",
        "event_name": "LiquidateBorrow",
        "collateral_asset": collateral_token,
        "debt_asset": event.get("address", "").lower(),  # The emitting contract is the debt cToken
        "borrower": borrower,
        "debt_repaid_raw": repay_amount,
        "collateral_seized_raw": seize_tokens,
        "liquidator": liquidator,
        "receive_a_token": False,
    }


def parse_fluid(event: Dict) -> Dict:
    """
    Parse Fluid Liquidation event.

    Event: Liquidation(
        address indexed liquidator,
        address indexed borrower,
        address indexed debtToken,
        address collateralToken,
        uint256 debtRepaid,
        uint256 collateralSeized
    )

    FIX: Was using wrong event signature 'Liquidate(address,uint256,uint256,address,uint256,bool)'.
    Correct signature is 'Liquidation(...)' with 3 indexed addresses + 1 address + 2 uint256 in data.
    """
    topics = event.get("topics", [])
    data = event.get("data", "0x")

    # 3 indexed params in topics
    liquidator = decode_address(topics[1]) if len(topics) > 1 else None
    borrower = decode_address(topics[2]) if len(topics) > 2 else None
    debt_token = decode_address(topics[3]) if len(topics) > 3 else None

    # Non-indexed params in data: collateralToken (address), debtRepaid (uint256), collateralSeized (uint256)
    data_hex = data[2:] if data.startswith("0x") else data
    collateral_token = decode_address(data_hex[0:64]) if len(data_hex) >= 64 else None
    debt_repaid = decode_uint256(data_hex[64:128]) if len(data_hex) >= 128 else 0
    collateral_seized = decode_uint256(data_hex[128:192]) if len(data_hex) >= 192 else 0

    return {
        "protocol": "fluid",
        "event_name": "Liquidation",
        "collateral_asset": collateral_token,
        "debt_asset": debt_token,
        "borrower": borrower,
        "debt_repaid_raw": debt_repaid,
        "collateral_seized_raw": collateral_seized,
        "liquidator": liquidator,
        "receive_a_token": False,
    }


def parse_gearbox(event: Dict) -> Dict:
    """
    Parse Gearbox LiquidateCreditAccount event.

    Event: LiquidateCreditAccount(
        address indexed creditAccount,
        address indexed liquidator,
        address to,
        uint256 remainingFunds
    )
    """
    topics = event.get("topics", [])
    data = event.get("data", "0x")

    credit_account = decode_address(topics[1]) if len(topics) > 1 else None
    liquidator = decode_address(topics[2]) if len(topics) > 2 else None

    data_hex = data[2:] if data.startswith("0x") else data
    to = decode_address(data_hex[0:64]) if len(data_hex) >= 64 else None
    remaining_funds = decode_uint256(data_hex[64:128]) if len(data_hex) >= 128 else 0

    return {
        "protocol": "gearbox",
        "event_name": "LiquidateCreditAccount",
        "collateral_asset": None,
        "debt_asset": None,
        "borrower": credit_account,
        "debt_repaid_raw": 0,
        "collateral_seized_raw": remaining_funds,
        "liquidator": liquidator,
        "receive_a_token": False,
        "to": to,
    }


def parse_cap(event: Dict) -> Dict:
    """
    Parse Cap Liquidate event.

    Event: Liquidate(
        address indexed liquidator,
        address indexed borrower,
        uint256 debtRepaid,
        uint256 collateralSeized
    )
    """
    topics = event.get("topics", [])
    data = event.get("data", "0x")

    liquidator = decode_address(topics[1]) if len(topics) > 1 else None
    borrower = decode_address(topics[2]) if len(topics) > 2 else None

    data_hex = data[2:] if data.startswith("0x") else data
    debt_repaid = decode_uint256(data_hex[0:64]) if len(data_hex) >= 64 else 0
    collateral_seized = decode_uint256(data_hex[64:128]) if len(data_hex) >= 128 else 0

    return {
        "protocol": "cap",
        "event_name": "Liquidate",
        "collateral_asset": None,
        "debt_asset": None,
        "borrower": borrower,
        "debt_repaid_raw": debt_repaid,
        "collateral_seized_raw": collateral_seized,
        "liquidator": liquidator,
        "receive_a_token": False,
    }


def parse_lista(event: Dict) -> Dict:
    """
    Parse Lista (Morpho-style) Liquidate event.

    Event: Liquidate(
        bytes32 indexed marketId,
        address indexed caller,
        address indexed borrower,
        uint256 repaidAssets,
        uint256 repaidShares,
        uint256 seizedAssets,
        uint256 badDebtAssets,
        uint256 badDebtShares
    )
    """
    topics = event.get("topics", [])
    data = event.get("data", "0x")

    market_id = topics[1] if len(topics) > 1 else None
    caller = decode_address(topics[2]) if len(topics) > 2 else None
    borrower = decode_address(topics[3]) if len(topics) > 3 else None

    data_hex = data[2:] if data.startswith("0x") else data
    repaid_assets = decode_uint256(data_hex[0:64]) if len(data_hex) >= 64 else 0
    repaid_shares = decode_uint256(data_hex[64:128]) if len(data_hex) >= 128 else 0
    seized_assets = decode_uint256(data_hex[128:192]) if len(data_hex) >= 192 else 0
    bad_debt_assets = decode_uint256(data_hex[192:256]) if len(data_hex) >= 256 else 0
    bad_debt_shares = decode_uint256(data_hex[256:320]) if len(data_hex) >= 320 else 0

    return {
        "protocol": "lista",
        "event_name": "Liquidate",
        "collateral_asset": None,
        "debt_asset": None,
        "borrower": borrower,
        "debt_repaid_raw": repaid_assets,
        "collateral_seized_raw": seized_assets,
        "liquidator": caller,
        "receive_a_token": False,
        "market_id": market_id,
        "bad_debt_assets": bad_debt_assets,
    }


def parse_event(event: Dict, chain: str) -> Optional[Dict]:
    """Parse a raw event into structured format."""
    topics = event.get("topics", [])
    if not topics:
        return None

    topic0 = topics[0].lower() if topics[0].startswith("0x") else "0x" + topics[0].lower()

    # Identify protocol
    protocol = EVENT_SIGNATURES.get(topic0)
    if not protocol:
        return None  # Unknown event type

    # Parse based on protocol
    if protocol == "aave_v3":
        parsed = parse_aave_v3(event)
    elif protocol == "compound_v3_collateral":
        parsed = parse_compound_v3_collateral(event)
    elif protocol == "compound_v3_debt":
        parsed = parse_compound_v3_debt(event)
    elif protocol == "compound_v2":
        parsed = parse_compound_v2(event)
    elif protocol == "fluid":
        parsed = parse_fluid(event)
    elif protocol == "gearbox":
        parsed = parse_gearbox(event)
    elif protocol == "cap":
        parsed = parse_cap(event)
    elif protocol == "lista":
        parsed = parse_lista(event)
    else:
        return None

    # Add common fields
    block_num = hex_to_int(event.get("blockNumber", 0))
    log_index = hex_to_int(event.get("logIndex", 0))
    tx_hash = event.get("transactionHash", "")
    if tx_hash.startswith("0x"):
        tx_hash = tx_hash[2:]

    # Get timestamp from blockTimestamp (hex) if available
    block_ts = event.get("blockTimestamp")
    if block_ts:
        timestamp = hex_to_int(block_ts)
    else:
        timestamp = None

    # Build CSU identifier using contract-aware resolution
    contract = event.get("address", "").lower()
    csu = resolve_csu(parsed["protocol"], chain, contract)

    result = {
        "tx_hash": tx_hash,
        "log_index": log_index,
        "block_number": block_num,
        "timestamp": timestamp,
        "date": datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d") if timestamp else None,
        "protocol": parsed["protocol"],
        "csu": csu,
        "event_name": parsed["event_name"],
        "contract": event.get("address", "").lower(),
        "collateral_asset": parsed.get("collateral_asset"),
        "debt_asset": parsed.get("debt_asset"),
        "borrower": parsed.get("borrower"),
        "debt_repaid_raw": parsed.get("debt_repaid_raw", 0),
        "collateral_seized_raw": parsed.get("collateral_seized_raw", 0),
        "liquidator": parsed.get("liquidator"),
        "receive_a_token": parsed.get("receive_a_token", False),
    }

    # Add protocol-specific extra fields
    if "usd_value_raw" in parsed:
        result["usd_value_raw"] = parsed["usd_value_raw"]
    if "bonus" in parsed:
        result["bonus"] = parsed["bonus"]
    if "absorb" in parsed:
        result["absorb"] = parsed["absorb"]

    return result


def is_raw_format(file_path: Path) -> bool:
    """Check if file contains raw format (has 'topics' field)."""
    with open(file_path, 'r') as f:
        first_line = f.readline().strip()
        if first_line:
            event = json.loads(first_line)
            return "topics" in event
    return False


def parse_chain(chain: str, dry_run: bool = False) -> Dict:
    """Parse all raw events for a chain."""
    input_file = INPUT_DIR / chain / "events.jsonl"
    output_file = OUTPUT_DIR / chain / "events_parsed.jsonl"

    if not input_file.exists():
        print(f"  ERROR: {input_file} not found")
        return {"chain": chain, "status": "error", "error": "file not found"}

    # Check if already parsed
    if not is_raw_format(input_file):
        print(f"  SKIP: {chain} already in parsed format")
        return {"chain": chain, "status": "skipped", "reason": "already parsed"}

    print(f"  Parsing {chain}...")

    parsed_count = 0
    error_count = 0

    if not dry_run:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        out_f = open(output_file, 'w')

    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
                parsed = parse_event(event, chain)

                if parsed:
                    if not dry_run:
                        out_f.write(json.dumps(parsed) + "\n")
                    parsed_count += 1
                else:
                    error_count += 1

            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"    Error on line {line_num}: {e}")

            if line_num % 10000 == 0:
                print(f"    Processed {line_num:,} lines, {parsed_count:,} parsed...")

    if not dry_run:
        out_f.close()

        # Replace original with parsed version
        backup_file = INPUT_DIR / chain / "events_raw.jsonl"
        input_file.rename(backup_file)
        output_file.rename(input_file)
        print(f"    Backed up raw data to {backup_file.name}")

    print(f"  DONE: {chain} - {parsed_count:,} events parsed, {error_count:,} errors")

    return {
        "chain": chain,
        "status": "success",
        "parsed": parsed_count,
        "errors": error_count,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse raw liquidation events to structured format")
    parser.add_argument("--chain", required=True, help="Chain to parse (or 'all' for all raw chains)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write output, just count")
    args = parser.parse_args()

    print("=" * 60)
    print("RAW LIQUIDATION EVENT PARSER")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Get chains to process
    if args.chain == "all":
        # Find all chains with raw data
        chains = []
        for chain_dir in INPUT_DIR.iterdir():
            if chain_dir.is_dir():
                events_file = chain_dir / "events.jsonl"
                if events_file.exists() and is_raw_format(events_file):
                    chains.append(chain_dir.name)
        print(f"Found {len(chains)} chains with raw data: {', '.join(chains)}")
    else:
        chains = [args.chain]

    if args.dry_run:
        print("DRY RUN - no files will be modified")

    print()

    results = []
    for chain in chains:
        result = parse_chain(chain, args.dry_run)
        results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_parsed = sum(r.get("parsed", 0) for r in results)
    total_errors = sum(r.get("errors", 0) for r in results)

    for r in results:
        status = r["status"]
        if status == "success":
            print(f"  {r['chain']}: {r['parsed']:,} events parsed")
        elif status == "skipped":
            print(f"  {r['chain']}: skipped ({r.get('reason', 'unknown')})")
        else:
            print(f"  {r['chain']}: ERROR - {r.get('error', 'unknown')}")

    print(f"\nTotal: {total_parsed:,} events parsed, {total_errors:,} errors")


if __name__ == "__main__":
    main()
