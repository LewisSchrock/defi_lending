#!/usr/bin/env python3
"""
Parallel Multi-Provider Liquidation Collector

Uses ThreadPoolExecutor to run multiple RPC providers simultaneously.
Each worker gets its own provider and processes chunks independently.

Key Design:
- 13 Alchemy accounts = 13 parallel workers
- Each worker processes different block ranges
- Thread-safe checkpoint and event writing
- No global backoff - each worker manages its own rate limiting

Usage:
    python scripts/collect_liquidations_parallel.py --chain ethereum --start-date 2024-01-01 --end-date 2025-12-31
    python scripts/collect_liquidations_parallel.py --chain ethereum --start-date 2024-01-01 --end-date 2025-12-31 --workers 8
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
import yaml
import argparse
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from eth_utils import keccak
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Import POA middleware
try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        from web3.middleware import geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None

# =============================================================================
# PATHS & CONFIG
# =============================================================================

CSU_CONFIG_PATH = Path('code/config/csu_config.yaml')
BRONZE_LIQUIDATIONS_DIR = Path('data/bronze/liquidations')
BLOCK_CACHE_DIR = Path('data/cache')

POA_CHAINS = ['binance', 'polygon', 'gnosis', 'avalanche', 'optimism', 'linea', 'scroll', 'xdai', 'cronos', 'meter', 'flare', 'sonic']
CHAIN_ALIASES = {'xdai': 'gnosis'}

# Thread-safe locks
_checkpoint_lock = threading.Lock()
_events_lock = threading.Lock()
_print_lock = threading.Lock()

# =============================================================================
# PROVIDER MANAGEMENT
# =============================================================================

def get_all_providers(chain: str) -> List[Tuple[str, str, str]]:
    """Get all available providers as (name, url, provider_type) tuples."""
    providers = []

    # Chain mappings for different providers
    alchemy_chains = {
        'ethereum': 'eth-mainnet',
        'arbitrum': 'arb-mainnet',
        'base': 'base-mainnet',
        'optimism': 'opt-mainnet',
        'polygon': 'polygon-mainnet',
        'avalanche': 'avalanche-mainnet',
        'binance': 'bnb-mainnet',
    }

    infura_chains = {
        'ethereum': 'mainnet',
        'arbitrum': 'arbitrum-mainnet',
        'base': 'base-mainnet',
        'optimism': 'optimism-mainnet',
        'polygon': 'polygon-mainnet',
        'linea': 'linea-mainnet',
        'avalanche': 'avalanche-mainnet',
    }

    ankr_chains = {
        'ethereum': 'eth',
        'arbitrum': 'arbitrum',
        'base': 'base',
        'optimism': 'optimism',
        'polygon': 'polygon',
        'binance': 'bsc',
        'avalanche': 'avalanche',
        'gnosis': 'gnosis',
        'linea': 'linea',
        'scroll': 'scroll',
    }

    blockpi_chains = {
        'ethereum': 'ethereum',
        'arbitrum': 'arbitrum',
        'base': 'base',
        'optimism': 'optimism',
        'polygon': 'polygon',
        'binance': 'bsc',
        'avalanche': 'avalanche',
        'gnosis': 'gnosis',
        'linea': 'linea',
        'sonic': 'sonic',
        'ink': 'ink',
        'meter': 'meter',
    }

    # Alchemy keys (primary - most capacity)
    if chain in alchemy_chains:
        chain_slug = alchemy_chains[chain]
        for i in range(1, 20):
            key = os.environ.get(f'ALCHEMY_KEY_{i}')
            if key:
                url = f'https://{chain_slug}.g.alchemy.com/v2/{key}'
                providers.append((f'alchemy_{i}', url, 'alchemy'))

    # BlockPi (per-chain keys)
    if chain in blockpi_chains:
        chain_slug = blockpi_chains[chain]
        env_key = f'BLOCKPI_KEY_{chain.upper()}'
        if chain == 'binance':
            env_key = 'BLOCKPI_KEY_BSC'
        key = os.environ.get(env_key)
        if key:
            url = f'https://{chain_slug}.blockpi.network/v1/rpc/{key}'
            providers.append(('blockpi', url, 'blockpi'))

    # Infura
    if chain in infura_chains:
        key = os.environ.get('INFURA_API_KEY')
        if key:
            chain_slug = infura_chains[chain]
            url = f'https://{chain_slug}.infura.io/v3/{key}'
            providers.append(('infura', url, 'infura'))

    # Ankr
    if chain in ankr_chains:
        key = os.environ.get('ANKR_API_KEY')
        if key:
            chain_slug = ankr_chains[chain]
            url = f'https://rpc.ankr.com/{chain_slug}/{key}'
            providers.append(('ankr', url, 'ankr'))

    return providers


def create_web3(url: str, chain: str) -> Web3:
    """Create Web3 instance with appropriate middleware."""
    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 30}))

    if chain in POA_CHAINS and geth_poa_middleware:
        try:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except Exception:
            pass

    return w3


# =============================================================================
# EVENT SIGNATURES (same as unified collector)
# =============================================================================

@dataclass
class EventSignature:
    protocol: str
    event_name: str
    signature: str
    topic0: str
    indexed_params: List[str]
    data_params: List[str]

    @classmethod
    def from_signature(cls, protocol: str, event_name: str, signature: str,
                       indexed_params: List[str], data_params: List[str]) -> 'EventSignature':
        topic0 = '0x' + keccak(text=signature).hex()
        return cls(protocol, event_name, signature, topic0, indexed_params, data_params)


LIQUIDATION_EVENTS = [
    EventSignature.from_signature('aave_v3', 'LiquidationCall',
        'LiquidationCall(address,address,address,uint256,uint256,address,bool)',
        ['collateral_asset', 'debt_asset', 'borrower'],
        ['debt_repaid_raw', 'collateral_seized_raw', 'liquidator', 'receive_a_token']),
    EventSignature.from_signature('compound_v3', 'AbsorbCollateral',
        'AbsorbCollateral(address,address,address,uint256,uint256)',
        ['absorber', 'borrower', 'asset'],
        ['collateral_raw', 'usd_value_raw']),
    EventSignature.from_signature('compound_v2', 'LiquidateBorrow',
        'LiquidateBorrow(address,address,uint256,address,uint256)',
        ['liquidator', 'borrower', 'repay_amount_raw'],
        ['ctoken_collateral', 'seize_tokens_raw']),
    EventSignature.from_signature('fluid', 'Liquidate',
        'Liquidate(address,uint256,uint256,address)',
        ['liquidator'], ['debt_amt_raw', 'collateral_amt_raw', 'to']),
]

ALL_TOPIC0S = [e.topic0 for e in LIQUIDATION_EVENTS]
TOPIC0_TO_EVENT = {e.topic0: e for e in LIQUIDATION_EVENTS}


# =============================================================================
# DATA MANAGEMENT (thread-safe)
# =============================================================================

def load_checkpoint(chain: str) -> Dict:
    checkpoint_file = BRONZE_LIQUIDATIONS_DIR / chain / 'checkpoint.json'
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            return json.load(f)
    return {}


def save_checkpoint(chain: str, last_block: int, total_events: int, contracts_count: int):
    with _checkpoint_lock:
        checkpoint = {
            'chain': chain,
            'last_block': last_block,
            'total_events': total_events,
            'contracts_count': contracts_count,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        checkpoint_file = BRONZE_LIQUIDATIONS_DIR / chain / 'checkpoint.json'
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)


def append_events(chain: str, events: List[Dict]):
    if not events:
        return
    with _events_lock:
        events_file = BRONZE_LIQUIDATIONS_DIR / chain / 'events.jsonl'
        events_file.parent.mkdir(parents=True, exist_ok=True)
        with open(events_file, 'a') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')


def count_existing_events(chain: str) -> int:
    events_file = BRONZE_LIQUIDATIONS_DIR / chain / 'events.jsonl'
    if not events_file.exists():
        return 0
    with open(events_file) as f:
        return sum(1 for _ in f)


def safe_print(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)


# =============================================================================
# BLOCK CACHE
# =============================================================================

def load_block_cache(chain: str) -> Dict[str, Dict]:
    cache = {}
    for cache_file in BLOCK_CACHE_DIR.glob(f'{chain}_blocks_*.json'):
        try:
            with open(cache_file) as f:
                file_cache = json.load(f)
                cache.update(file_cache)
        except Exception:
            continue
    return cache


# =============================================================================
# EVENT DECODING
# =============================================================================

def decode_liquidation_event(w3: Web3, log: Dict, event_sig: EventSignature,
                            csu: str, block_timestamp: int = None) -> Dict:
    """Decode a liquidation event log."""
    event = {
        'chain': csu.split('_')[-1] if '_' in csu else 'unknown',
        'csu': csu,
        'protocol': event_sig.protocol,
        'event_type': event_sig.event_name,
        'block_number': log['blockNumber'],
        'block_timestamp': block_timestamp,
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'contract_address': log['address'],
    }

    # Decode indexed params from topics
    topics = log['topics'][1:]  # Skip topic0
    for i, param_name in enumerate(event_sig.indexed_params):
        if i < len(topics):
            topic = topics[i]
            topic_bytes = topic if isinstance(topic, bytes) else bytes.fromhex(topic[2:])
            if 'asset' in param_name.lower() or param_name in ['borrower', 'liquidator', 'absorber', 'to']:
                event[param_name] = w3.to_checksum_address('0x' + topic_bytes.hex()[-40:])
            else:
                event[param_name] = int.from_bytes(topic_bytes, 'big')

    # Decode data params
    data = log['data']
    data_bytes = data if isinstance(data, bytes) else bytes.fromhex(data[2:])
    offset = 0
    for param_name in event_sig.data_params:
        if offset + 32 > len(data_bytes):
            break
        chunk = data_bytes[offset:offset + 32]
        if 'receive_a_token' in param_name:
            event[param_name] = bool(int.from_bytes(chunk, 'big'))
        elif param_name in ['liquidator', 'to', 'absorber', 'ctoken_collateral']:
            event[param_name] = w3.to_checksum_address('0x' + chunk.hex()[-40:])
        else:
            event[param_name] = int.from_bytes(chunk, 'big')
        offset += 32

    return event


# =============================================================================
# WORKER FUNCTION
# =============================================================================

def worker_scan(
    worker_id: int,
    provider_name: str,
    provider_url: str,
    chain: str,
    chunk_queue: Queue,
    results: Dict,
    all_addresses: List[str],
    address_to_csu: Dict[str, str],
    relevant_topic0s: List[str],
    pace_seconds: float = 0.3,
):
    """
    Worker function that processes chunks from a queue.
    Each worker has its own Web3 connection and rate limiting.
    """
    w3 = create_web3(provider_url, chain)

    processed = 0
    events_found = 0
    errors = 0
    consecutive_errors = 0

    while True:
        try:
            # Get next chunk from queue (non-blocking with timeout)
            chunk = chunk_queue.get(timeout=5)
        except Empty:
            # Queue empty - we're done
            break

        from_block, to_block = chunk

        # Rate limiting - back off if too many consecutive errors
        if consecutive_errors > 3:
            time.sleep(min(consecutive_errors * 2, 30))

        try:
            # Query logs
            logs = w3.eth.get_logs({
                'fromBlock': from_block,
                'toBlock': to_block,
                'address': all_addresses[:50],  # Max 50 addresses
                'topics': [relevant_topic0s],
            })

            # Decode events
            chunk_events = []
            for log in logs:
                try:
                    topic0 = log['topics'][0]
                    topic0_hex = '0x' + (topic0.hex() if isinstance(topic0, bytes) else topic0[2:])
                    event_sig = TOPIC0_TO_EVENT.get(topic0_hex)
                    if not event_sig:
                        continue

                    contract_addr = log['address'].lower()
                    csu = address_to_csu.get(contract_addr, 'unknown')

                    # Get block timestamp
                    try:
                        block = w3.eth.get_block(log['blockNumber'])
                        block_ts = block['timestamp']
                    except:
                        block_ts = None

                    event = decode_liquidation_event(w3, log, event_sig, csu, block_ts)
                    chunk_events.append(event)
                except Exception as e:
                    pass

            # Save events
            if chunk_events:
                append_events(chain, chunk_events)
                events_found += len(chunk_events)

            processed += 1
            consecutive_errors = 0

            # Update results
            results[worker_id] = {
                'provider': provider_name,
                'processed': processed,
                'events': events_found,
                'errors': errors,
                'last_block': to_block,
            }

            # Pace ourselves
            time.sleep(pace_seconds)

        except Exception as e:
            error_msg = str(e).lower()
            errors += 1
            consecutive_errors += 1

            # Put chunk back in queue for another worker if rate limited
            if '429' in error_msg or 'rate' in error_msg:
                chunk_queue.put(chunk)
                time.sleep(2)  # Brief pause before continuing
            elif consecutive_errors > 5:
                # Too many errors - put back and take a break
                chunk_queue.put(chunk)
                time.sleep(10)
                consecutive_errors = 0

        chunk_queue.task_done()

    results[worker_id] = {
        'provider': provider_name,
        'processed': processed,
        'events': events_found,
        'errors': errors,
        'status': 'done',
    }


# =============================================================================
# MAIN COLLECTION FUNCTION
# =============================================================================

def collect_liquidations_parallel(
    chain: str,
    from_block: int,
    to_block: int,
    contracts: Dict[str, List[str]],
    num_workers: int = None,
    chunk_size: int = 10,
    status_interval: int = 30,  # seconds
):
    """
    Parallel liquidation collection using multiple providers.
    """
    # Get available providers
    providers = get_all_providers(chain)
    if not providers:
        print(f"No providers available for {chain}")
        return 0

    # Default workers = number of providers (max parallelism)
    if num_workers is None:
        num_workers = min(len(providers), 15)  # Cap at 15 workers

    print(f"\n{'='*60}")
    print(f"PARALLEL LIQUIDATION COLLECTOR")
    print(f"{'='*60}")
    print(f"  Chain:          {chain}")
    print(f"  Block range:    {from_block:,} → {to_block:,}")
    print(f"  Total blocks:   {to_block - from_block + 1:,}")
    print(f"  Providers:      {len(providers)}")
    print(f"  Workers:        {num_workers}")
    print(f"  Chunk size:     {chunk_size}")
    print(f"{'='*60}\n")

    # Print providers
    print("Providers:")
    for name, url, ptype in providers[:num_workers]:
        print(f"  • {name}")
    print()

    # Build address mapping
    address_to_csu = {}
    for csu, addresses in contracts.items():
        for addr in addresses:
            address_to_csu[addr.lower()] = csu
    all_addresses = list(set(addr for addrs in contracts.values() for addr in addrs))

    # Create chunk queue
    chunk_queue = Queue()
    total_chunks = 0
    for block in range(from_block, to_block + 1, chunk_size):
        chunk_end = min(block + chunk_size - 1, to_block)
        chunk_queue.put((block, chunk_end))
        total_chunks += 1

    print(f"Total chunks to process: {total_chunks:,}")
    print(f"Starting {num_workers} parallel workers...\n")

    # Results dict (thread-safe via GIL for dict updates)
    results = {}
    start_time = time.time()

    # Start workers
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, (name, url, ptype) in enumerate(providers[:num_workers]):
            future = executor.submit(
                worker_scan,
                i, name, url, chain,
                chunk_queue, results,
                all_addresses, address_to_csu,
                ALL_TOPIC0S,
                0.3,  # pace_seconds
            )
            futures.append(future)

        # Monitor progress
        last_status = time.time()
        while not chunk_queue.empty() or any(not f.done() for f in futures):
            time.sleep(2)

            # Print status periodically
            if time.time() - last_status >= status_interval:
                last_status = time.time()
                elapsed = time.time() - start_time

                total_processed = sum(r.get('processed', 0) for r in results.values())
                total_events = sum(r.get('events', 0) for r in results.values())
                total_errors = sum(r.get('errors', 0) for r in results.values())
                remaining = chunk_queue.qsize()

                chunks_per_sec = total_processed / elapsed if elapsed > 0 else 0
                eta_seconds = remaining / chunks_per_sec if chunks_per_sec > 0 else 0

                print(f"\n{'─'*60}")
                print(f"📈 PROGRESS ({total_processed:,}/{total_chunks:,} chunks, {total_processed/total_chunks*100:.1f}%)")
                print(f"{'─'*60}")
                print(f"  Events found:  {total_events:,}")
                print(f"  Errors:        {total_errors:,}")
                print(f"  Speed:         {chunks_per_sec:.1f} chunks/sec ({chunks_per_sec*10:.0f} blocks/sec)")
                print(f"  Elapsed:       {elapsed/60:.1f} min")
                print(f"  ETA:           {eta_seconds/60:.1f} min")
                print(f"\n  Worker status:")
                for wid, r in sorted(results.items()):
                    print(f"    {r.get('provider', '?'):15} {r.get('processed', 0):>6} chunks, {r.get('events', 0):>5} events, {r.get('errors', 0):>3} errors")
                print(f"{'─'*60}")

                # Save checkpoint with highest block processed
                max_block = max((r.get('last_block', 0) for r in results.values()), default=from_block)
                save_checkpoint(chain, max_block, count_existing_events(chain), len(all_addresses))

        # Wait for all futures to complete
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Worker error: {e}")

    # Final stats
    elapsed = time.time() - start_time
    total_events = count_existing_events(chain)

    print(f"\n{'='*60}")
    print(f"✅ COLLECTION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total events:  {total_events:,}")
    print(f"  Total time:    {elapsed/60:.1f} min")
    print(f"  Avg speed:     {total_chunks/elapsed:.1f} chunks/sec")
    print(f"{'='*60}\n")

    # Save final checkpoint
    save_checkpoint(chain, to_block, total_events, len(all_addresses))

    return total_events


# =============================================================================
# CSU & CONTRACT RESOLUTION
# =============================================================================

def load_csu_config() -> Dict:
    if not CSU_CONFIG_PATH.exists():
        return {}
    with open(CSU_CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    return config.get('csus', config)


def get_csus_for_chain(chain: str) -> List[Dict]:
    csu_config = load_csu_config()
    csus = []
    for csu_name, csu_info in csu_config.items():
        csu_chain = csu_info.get('chain', '')
        if csu_chain == chain or CHAIN_ALIASES.get(csu_chain) == chain:
            csus.append({
                'csu': csu_name,
                'protocol': csu_info.get('protocol'),
                'registry': csu_info.get('registry'),
                'pool': csu_info.get('pool'),
                'comptroller': csu_info.get('comptroller'),
                'markets': csu_info.get('markets', []),
            })
    return csus


def resolve_contracts(w3: Web3, csu_info: Dict) -> List[str]:
    """Resolve contract addresses for a CSU."""
    addresses = []

    # Direct pool/market addresses
    if csu_info.get('pool'):
        addresses.append(csu_info['pool'])
    if csu_info.get('markets'):
        addresses.extend(csu_info['markets'])

    # Aave-style registry resolution
    if csu_info.get('registry') and csu_info.get('protocol') in ['aave', 'sparklend']:
        try:
            registry = w3.eth.contract(
                address=Web3.to_checksum_address(csu_info['registry']),
                abi=[{"inputs":[],"name":"getPool","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"}]
            )
            pool = registry.functions.getPool().call()
            addresses.append(pool)
        except:
            pass

    # Compound V3 comet
    if csu_info.get('registry') and csu_info.get('protocol') == 'compound':
        addresses.append(csu_info['registry'])

    return list(set(addresses))


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Parallel Liquidation Collector')
    parser.add_argument('--chain', required=True, help='Chain to scan')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--workers', type=int, help='Number of parallel workers')
    parser.add_argument('--chunk-size', type=int, default=10, help='Blocks per chunk')
    # --force removed: previously wiped checkpoint data on accident

    args = parser.parse_args()
    chain = args.chain

    # Load block cache
    block_cache = load_block_cache(chain)
    if not block_cache:
        print(f"No block cache for {chain}. Run build_block_cache.py first.")
        return

    if args.start_date not in block_cache or args.end_date not in block_cache:
        print(f"Date range not in block cache. Available: {min(block_cache.keys())} to {max(block_cache.keys())}")
        return

    from_block = block_cache[args.start_date]['block']
    to_block = block_cache[args.end_date]['block']

    # Check checkpoint
    checkpoint = load_checkpoint(chain)
    if checkpoint:
        last_block = checkpoint.get('last_block', 0)
        if last_block >= from_block and last_block < to_block:
            print(f"Resuming from checkpoint: block {last_block:,}")
            from_block = last_block + 1
        elif last_block >= to_block:
            print(f"Collection complete for this range.")
            return

    # Get CSUs and resolve contracts
    csus = get_csus_for_chain(chain)
    if not csus:
        print(f"No CSUs found for {chain}")
        return

    print(f"Found {len(csus)} CSUs for {chain}")

    # Get a web3 instance for contract resolution
    providers = get_all_providers(chain)
    if not providers:
        print(f"No providers for {chain}")
        return

    w3 = create_web3(providers[0][1], chain)

    # Resolve contracts
    contracts = {}
    for csu_info in csus:
        try:
            addrs = resolve_contracts(w3, csu_info)
            if addrs:
                contracts[csu_info['csu']] = addrs
        except Exception as e:
            print(f"  Failed to resolve {csu_info['csu']}: {e}")

    if not contracts:
        print("No contracts resolved")
        return

    print(f"Resolved {sum(len(v) for v in contracts.values())} contracts across {len(contracts)} CSUs")

    # Run parallel collection
    collect_liquidations_parallel(
        chain=chain,
        from_block=from_block,
        to_block=to_block,
        contracts=contracts,
        num_workers=args.workers,
        chunk_size=args.chunk_size,
    )


if __name__ == '__main__':
    main()
