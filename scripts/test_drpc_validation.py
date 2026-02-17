#!/usr/bin/env python3
"""
Phase 1 Validation: dRPC Connectivity & Optimization Tests

Tests:
1. Basic connectivity - single eth_getLogs call
2. Chunk size optimization - find max blocks per call
3. Parallelism - test concurrent worker limits
4. Cross-chain validation - verify multiple chains work

Usage:
    export DRPC_API_KEY="your_key_here"
    python scripts/test_drpc_validation.py
"""

import os
import sys
import time
import asyncio
import aiohttp
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Will use environment variables directly

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# dRPC keys per chain - set via environment variables
# Format: DRPC_KEY_ETHEREUM, DRPC_KEY_ARBITRUM, etc.
DRPC_KEYS = {
    "ethereum": os.environ.get("DRPC_KEY_ETHEREUM", ""),
    "arbitrum": os.environ.get("DRPC_KEY_ARBITRUM", ""),
    "optimism": os.environ.get("DRPC_KEY_OPTIMISM", ""),
    "polygon": os.environ.get("DRPC_KEY_POLYGON", ""),
    "avalanche": os.environ.get("DRPC_KEY_AVALANCHE", ""),
    "bsc": os.environ.get("DRPC_KEY_BSC", ""),
    "linea": os.environ.get("DRPC_KEY_LINEA", ""),
    "scroll": os.environ.get("DRPC_KEY_SCROLL", ""),
    "gnosis": os.environ.get("DRPC_KEY_GNOSIS", ""),
    # "plasma": os.environ.get("DRPC_KEY_PLASMA", ""),
    # "ink": os.environ.get("DRPC_KEY_INK", ""),
}

# dRPC network slugs (if different from our chain names)
DRPC_SLUGS = {
    "ethereum": "ethereum",
    "arbitrum": "arbitrum",
    "optimism": "optimism",
    "polygon": "polygon",
    "avalanche": "avalanche",
    "bsc": "bsc",
    "linea": "linea",
    "scroll": "scroll",
    "gnosis": "gnosis",
}

# Known liquidation event signatures (topic0)
LIQUIDATION_TOPICS = [
    # Aave V3: LiquidationCall(address,address,address,uint256,uint256,address,bool)
    "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286",
    # Compound V3: AbsorbCollateral(address,address,address,uint256,uint256)
    "0x9850ab1af75177e4a7e9870da8a34d4979b71cc4cd596df22ba4fb8b571430b9",
    # Fluid: Liquidate(address,uint256,uint256,address)
    "0x21e5d8a6c21bdef70b0d22f1ab8fa303a64de1d365bbfe8baa6bcd5ad71e0884",
]

# Known blocks with liquidation events for validation
KNOWN_LIQUIDATIONS = {
    "ethereum": {
        "block": 18922256,  # Known Aave V3 liquidation
        "expected_topic": "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286",
    },
    "arbitrum": {
        "block": 175000000,  # Approximate - will search nearby
        "expected_topic": "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286",
    },
}

# Chunk sizes to test (in blocks)
CHUNK_SIZES = [10, 100, 1000, 5000, 10000, 50000]

# Concurrency levels to test (single paid account = sequential)
CONCURRENCY_LEVELS = [1]  # Single account, no parallelism needed

# Chains to cross-validate
CROSS_CHAIN_TEST = ["optimism", "bsc", "gnosis", "polygon"]


# ==============================================================================
# UTILITIES
# ==============================================================================

@dataclass
class TestResult:
    """Container for test results."""
    test_name: str
    passed: bool
    duration_ms: float
    details: Dict = field(default_factory=dict)
    error: Optional[str] = None


def get_drpc_url(chain: str) -> str:
    """Get dRPC endpoint URL for a chain.

    Accepts either:
    - Full URL: https://lb.drpc.live/ethereum/KEY
    - Just the key: KEY (will construct URL)
    """
    value = DRPC_KEYS.get(chain, "")
    if not value:
        raise ValueError(f"DRPC_KEY_{chain.upper()} environment variable not set")

    # If it's already a full URL, use it directly
    if value.startswith("http"):
        return value

    # Otherwise construct the URL from the key
    slug = DRPC_SLUGS.get(chain, chain)
    return f"https://lb.drpc.org/ogrpc?network={slug}&dkey={value}"


async def eth_get_logs(
    session: aiohttp.ClientSession,
    url: str,
    from_block: int,
    to_block: int,
    topics: List[str],
    addresses: Optional[List[str]] = None,
) -> Tuple[List[Dict], float]:
    """
    Call eth_getLogs and return (logs, duration_ms).
    """
    params = {
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
        "topics": [topics],  # OR of all topics
    }
    if addresses:
        params["address"] = addresses

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",
        "params": [params],
        "id": 1,
    }

    start = time.perf_counter()
    async with session.post(url, json=payload) as resp:
        result = await resp.json()
        duration_ms = (time.perf_counter() - start) * 1000

    if "error" in result:
        raise Exception(f"RPC error: {result['error']}")

    return result.get("result", []), duration_ms


async def eth_block_number(session: aiohttp.ClientSession, url: str) -> int:
    """Get current block number."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1,
    }
    async with session.post(url, json=payload) as resp:
        result = await resp.json()
    if "error" in result:
        raise Exception(f"RPC error: {result['error']}")
    return int(result["result"], 16)


# ==============================================================================
# TEST 1: BASIC CONNECTIVITY
# ==============================================================================

async def test_basic_connectivity(session: aiohttp.ClientSession) -> TestResult:
    """Test basic dRPC connectivity with a known liquidation block."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Connectivity")
    print("=" * 60)

    # Use ethereum if configured, otherwise first configured chain
    configured = [c for c, k in DRPC_KEYS.items() if k]
    chain = "ethereum" if "ethereum" in configured else configured[0]

    # Use known block if available, otherwise query recent blocks
    if chain in KNOWN_LIQUIDATIONS:
        block = KNOWN_LIQUIDATIONS[chain]["block"]
        expected_topic = KNOWN_LIQUIDATIONS[chain]["expected_topic"]
    else:
        block = None  # Will query current block
        expected_topic = None

    try:
        url = get_drpc_url(chain)
        print(f"  Chain: {chain}")

        # If no known block, get current block and search recent range
        if block is None:
            current = await eth_block_number(session, url)
            block = current - 10000  # Search last 10K blocks
            print(f"  Searching blocks {block:,} to {current:,}")
        else:
            print(f"  Block: {block:,}")

        print(f"  URL: {url[:50]}...")

        # Query single block or range depending on whether we have a known block
        if expected_topic:
            logs, duration = await eth_get_logs(
                session, url, block, block, LIQUIDATION_TOPICS
            )
        else:
            current = await eth_block_number(session, url)
            logs, duration = await eth_get_logs(
                session, url, block, current, LIQUIDATION_TOPICS
            )

        # Check if we got the expected event (if we have one to check)
        found_expected = expected_topic is None or any(
            log.get("topics", [None])[0] == expected_topic
            for log in logs
        )

        print(f"  Events found: {len(logs)}")
        print(f"  Expected topic found: {found_expected}")
        print(f"  Duration: {duration:.1f}ms")

        if not logs:
            # Try a wider range
            print(f"  No events at exact block, trying range {block-10} to {block+10}...")
            logs, duration = await eth_get_logs(
                session, url, block - 10, block + 10, LIQUIDATION_TOPICS
            )
            print(f"  Events in range: {len(logs)}")

        passed = len(logs) > 0 or found_expected
        return TestResult(
            test_name="Basic Connectivity",
            passed=passed,
            duration_ms=duration,
            details={
                "chain": chain,
                "block": block,
                "events_found": len(logs),
                "expected_topic_found": found_expected,
            }
        )

    except Exception as e:
        print(f"  ERROR: {e}")
        return TestResult(
            test_name="Basic Connectivity",
            passed=False,
            duration_ms=0,
            error=str(e)
        )


# ==============================================================================
# TEST 2: CHUNK SIZE OPTIMIZATION
# ==============================================================================

async def test_chunk_sizes(session: aiohttp.ClientSession) -> TestResult:
    """Test different chunk sizes to find optimal blocks per call."""
    print("\n" + "=" * 60)
    print("TEST 2: Chunk Size Optimization")
    print("=" * 60)

    # Use ethereum if configured, otherwise first configured chain
    configured = [c for c, k in DRPC_KEYS.items() if k]
    chain = "ethereum" if "ethereum" in configured else configured[0]
    results = {}
    optimal_size = 10

    try:
        url = get_drpc_url(chain)
        print(f"  Testing on: {chain}")
        current_block = await eth_block_number(session, url)

        # Test each chunk size
        for chunk_size in CHUNK_SIZES:
            from_block = current_block - chunk_size
            to_block = current_block

            print(f"\n  Testing {chunk_size:,} blocks...")

            try:
                start = time.perf_counter()
                logs, duration = await eth_get_logs(
                    session, url, from_block, to_block, LIQUIDATION_TOPICS
                )
                total_time = (time.perf_counter() - start) * 1000

                blocks_per_sec = chunk_size / (total_time / 1000)

                results[chunk_size] = {
                    "success": True,
                    "events": len(logs),
                    "duration_ms": total_time,
                    "blocks_per_sec": blocks_per_sec,
                }

                print(f"    ✓ Success: {len(logs)} events, {total_time:.0f}ms, {blocks_per_sec:.0f} blocks/sec")
                optimal_size = chunk_size

            except Exception as e:
                error_str = str(e)
                results[chunk_size] = {
                    "success": False,
                    "error": error_str[:100],
                }
                print(f"    ✗ Failed: {error_str[:80]}...")

                # If we hit a limit, stop testing larger sizes
                if "limit" in error_str.lower() or "too large" in error_str.lower():
                    print(f"    → Hit size limit, stopping at {optimal_size:,} blocks")
                    break

        print(f"\n  OPTIMAL CHUNK SIZE: {optimal_size:,} blocks")

        return TestResult(
            test_name="Chunk Size Optimization",
            passed=optimal_size >= 100,  # Pass if we can do at least 100 blocks
            duration_ms=sum(r.get("duration_ms", 0) for r in results.values() if r.get("success")),
            details={
                "chain": chain,
                "results": results,
                "optimal_size": optimal_size,
            }
        )

    except Exception as e:
        print(f"  ERROR: {e}")
        return TestResult(
            test_name="Chunk Size Optimization",
            passed=False,
            duration_ms=0,
            error=str(e)
        )




# ==============================================================================
# TEST 4: CROSS-CHAIN VALIDATION
# ==============================================================================

async def test_cross_chain(session: aiohttp.ClientSession) -> TestResult:
    """Test liquidation queries across all configured chains."""
    print("\n" + "=" * 60)
    print("TEST 3: Cross-Chain Validation")
    print("=" * 60)

    # Test all configured chains
    configured = [c for c, k in DRPC_KEYS.items() if k]
    results = {}
    successes = 0

    print(f"  Testing {len(configured)} configured chains: {', '.join(configured)}")

    for chain in configured:
        print(f"\n  Testing {chain}...")

        try:
            url = get_drpc_url(chain)
            current_block = await eth_block_number(session, url)

            # Query last 10,000 blocks
            from_block = current_block - 10000

            logs, duration = await eth_get_logs(
                session, url, from_block, current_block, LIQUIDATION_TOPICS
            )

            results[chain] = {
                "success": True,
                "current_block": current_block,
                "events_found": len(logs),
                "duration_ms": duration,
            }

            print(f"    ✓ Block {current_block:,}, {len(logs)} events in last 10K blocks, {duration:.0f}ms")
            successes += 1

        except Exception as e:
            results[chain] = {
                "success": False,
                "error": str(e)[:100],
            }
            print(f"    ✗ Failed: {str(e)[:60]}...")

    passed = successes >= len(configured) - 1  # Allow 1 failure

    return TestResult(
        test_name="Cross-Chain Validation",
        passed=passed,
        duration_ms=sum(r.get("duration_ms", 0) for r in results.values() if r.get("success")),
        details={
            "chains_tested": configured,
            "successes": successes,
            "failures": len(configured) - successes,
            "results": results,
        }
    )


# ==============================================================================
# MAIN
# ==============================================================================

async def main():
    """Run all validation tests."""
    print("=" * 60)
    print("dRPC VALIDATION TESTS")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Check which keys are configured
    configured_chains = [chain for chain, key in DRPC_KEYS.items() if key]
    if not configured_chains:
        print("\n❌ ERROR: No dRPC keys configured!")
        print("   Set environment variables for each chain:")
        print("   export DRPC_KEY_ETHEREUM='your_ethereum_key'")
        print("   export DRPC_KEY_ARBITRUM='your_arbitrum_key'")
        print("   ... etc.")
        sys.exit(1)

    print(f"\nConfigured chains: {', '.join(configured_chains)}")
    for chain in configured_chains:
        key = DRPC_KEYS[chain]
        print(f"  {chain}: {key[:8]}...{key[-4:]}")

    # Create session with generous timeouts
    timeout = aiohttp.ClientTimeout(total=60, connect=10)
    connector = aiohttp.TCPConnector(limit=50)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        results = []

        # Run tests
        results.append(await test_basic_connectivity(session))
        results.append(await test_chunk_sizes(session))
        results.append(await test_cross_chain(session))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for r in results:
        status = "✓ PASS" if r.passed else "✗ FAIL"
        print(f"  {status}: {r.test_name}")
        if r.error:
            print(f"         Error: {r.error[:60]}")
        if not r.passed:
            all_passed = False

    # Extract key parameters
    chunk_result = next((r for r in results if r.test_name == "Chunk Size Optimization"), None)

    optimal_chunk = chunk_result.details.get("optimal_size", 1000) if chunk_result else 1000

    print("\n" + "-" * 60)
    print("RECOMMENDED SETTINGS")
    print("-" * 60)
    print(f"  Chunk size: {optimal_chunk:,} blocks")
    print(f"  Workers: 1 (single paid account)")

    # Decision
    print("\n" + "-" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Ready to proceed with collection!")
    else:
        print("⚠ SOME TESTS FAILED - Review results before proceeding")
    print("-" * 60)

    # Save results to file
    output = {
        "timestamp": datetime.now().isoformat(),
        "configured_chains": configured_chains,
        "all_passed": all_passed,
        "recommended_chunk_size": optimal_chunk,
        "recommended_workers": 1,
        "tests": [
            {
                "name": r.test_name,
                "passed": r.passed,
                "duration_ms": r.duration_ms,
                "details": r.details,
                "error": r.error,
            }
            for r in results
        ]
    }

    output_path = "data/bronze/liquidations/drpc_validation_results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
