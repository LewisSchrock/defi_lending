"""
Compound V3 (Comet) Liquidation Adapter

Liquidation Mechanism:
- Compound V3 uses "absorb" for liquidations
- Emits "AbsorbCollateral" and "AbsorbDebt" events
- Absorber (liquidator) takes over bad debt positions

Event signature:
AbsorbCollateral(
    address indexed absorber,
    address indexed borrower, 
    address indexed asset,
    uint collateralAbsorbed,
    uint usdValue
)

AbsorbDebt(
    address indexed absorber,
    address indexed borrower,
    uint basePaidOut,
    uint usdValue
)
"""

from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_utils import keccak
import time

# AbsorbCollateral event ABI
ABSORB_COLLATERAL_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "absorber", "type": "address"},
        {"indexed": True, "name": "borrower", "type": "address"},
        {"indexed": True, "name": "asset", "type": "address"},
        {"indexed": False, "name": "collateralAbsorbed", "type": "uint256"},
        {"indexed": False, "name": "usdValue", "type": "uint256"},
    ],
    "name": "AbsorbCollateral",
    "type": "event",
}

# AbsorbDebt event ABI
ABSORB_DEBT_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "absorber", "type": "address"},
        {"indexed": True, "name": "borrower", "type": "address"},
        {"indexed": False, "name": "basePaidOut", "type": "uint256"},
        {"indexed": False, "name": "usdValue", "type": "uint256"},
    ],
    "name": "AbsorbDebt",
    "type": "event",
}

# Event signatures
ABSORB_COLLATERAL_SIG = "AbsorbCollateral(address,address,address,uint256,uint256)"
ABSORB_DEBT_SIG = "AbsorbDebt(address,address,uint256,uint256)"
TOPIC0_COLLATERAL = keccak(text=ABSORB_COLLATERAL_SIG).hex()
TOPIC0_DEBT = keccak(text=ABSORB_DEBT_SIG).hex()


def _decode_absorb_collateral(web3: Web3, log) -> Dict[str, Any]:
    """Decode AbsorbCollateral event."""
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters (addresses from topics)
    absorber = web3.to_checksum_address('0x' + topics[1].hex()[-40:])
    borrower = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    asset = web3.to_checksum_address('0x' + topics[3].hex()[-40:])
    
    # Decode non-indexed parameters from data
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    collateral_absorbed = int.from_bytes(data_bytes[0:32], 'big')
    usd_value = int.from_bytes(data_bytes[32:64], 'big')
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'event_type': 'AbsorbCollateral',
        'absorber': absorber,
        'borrower': borrower,
        'collateral_asset': asset,
        'collateral_absorbed_raw': collateral_absorbed,
        'usd_value_raw': usd_value,
    }


def _decode_absorb_debt(web3: Web3, log) -> Dict[str, Any]:
    """Decode AbsorbDebt event."""
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters
    absorber = web3.to_checksum_address('0x' + topics[1].hex()[-40:])
    borrower = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    
    # Decode non-indexed parameters from data
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    base_paid_out = int.from_bytes(data_bytes[0:32], 'big')
    usd_value = int.from_bytes(data_bytes[32:64], 'big')
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'event_type': 'AbsorbDebt',
        'absorber': absorber,
        'borrower': borrower,
        'base_paid_out_raw': base_paid_out,
        'usd_value_raw': usd_value,
    }


def scan_compound_v3_liquidations(
    web3: Web3,
    comet_address: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 10,
    max_retries: int = 3,
    pace_seconds: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Scan for Compound V3 liquidation events (AbsorbCollateral + AbsorbDebt).
    
    Args:
        web3: Web3 instance
        comet_address: Comet contract address
        from_block: Start block (inclusive)
        to_block: End block (inclusive)
        chunk_size: Max blocks per eth_getLogs call (default: 10 for Alchemy)
        max_retries: Number of retries on rate limit errors
        pace_seconds: Sleep duration between chunks
        
    Returns:
        List of decoded liquidation events (both collateral and debt absorptions)
    """
    comet_address = Web3.to_checksum_address(comet_address)
    
    print(f"Scanning Comet: {comet_address}")
    print(f"Block range: [{from_block:,}, {to_block:,}]")
    print(f"Chunk size: {chunk_size} blocks")
    
    all_events = []
    current = from_block
    chunks_processed = 0
    chunks_failed = 0
    
    while current <= to_block:
        chunk_end = min(current + chunk_size - 1, to_block)
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                # Get both event types in one call using multiple topics
                logs = web3.eth.get_logs({
                    'fromBlock': current,
                    'toBlock': chunk_end,
                    'address': comet_address,
                    'topics': [[TOPIC0_COLLATERAL, TOPIC0_DEBT]],  # OR condition
                })
                
                # Decode each log based on event type
                for log in logs:
                    try:
                        topic0 = log['topics'][0].hex() if isinstance(log['topics'][0], bytes) else log['topics'][0]
                        
                        if topic0 == TOPIC0_COLLATERAL:
                            event = _decode_absorb_collateral(web3, log)
                        elif topic0 == TOPIC0_DEBT:
                            event = _decode_absorb_debt(web3, log)
                        else:
                            continue
                        
                        all_events.append(event)
                    except Exception as e:
                        print(f"Warning: Failed to decode log {log['logIndex']}: {e}")
                
                chunks_processed += 1
                if logs:
                    print(f"  [{current:,}, {chunk_end:,}]: {len(logs)} events")
                
                # Success - break retry loop
                break
                
            except Exception as e:
                error_msg = str(e).lower()
                
                is_rate_limit = any(phrase in error_msg for phrase in [
                    'too many requests',
                    'rate limit',
                    'exceeded',
                    '429',
                    'compute units',
                ])
                
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"  Rate limit hit on [{current:,}, {chunk_end:,}], "
                          f"retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    if attempt == max_retries - 1:
                        print(f"  ❌ Failed [{current:,}, {chunk_end:,}] after {max_retries} attempts: {e}")
                        chunks_failed += 1
                    else:
                        print(f"  Warning: Error on [{current:,}, {chunk_end:,}]: {e}")
                        chunks_failed += 1
                    break
        
        # Small delay between chunks
        if pace_seconds > 0:
            time.sleep(pace_seconds)
        
        current = chunk_end + 1
    
    print(f"\n✅ Scan complete: {chunks_processed} chunks processed, {chunks_failed} chunks failed")
    return all_events


if __name__ == '__main__':
    # Quick test
    from web3 import Web3
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.rpc_config import get_rpc_url
    
    rpc = get_rpc_url('ethereum')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    # Compound V3 USDC market on Ethereum
    comet = '0xc3d688B66703497DAA19211EEdff47f25384cdc3'
    
    latest = w3.eth.block_number
    from_block = latest - 10000  # Last 10k blocks
    
    print("Testing Compound V3 liquidation scanning...")
    print(f"Latest block: {latest:,}")
    
    events = scan_compound_v3_liquidations(w3, comet, from_block, latest, 
                                           chunk_size=10, pace_seconds=0.1)
    
    print(f"\n✅ Found {len(events)} absorption events")
    if events:
        print("\nFirst event:")
        first = events[0]
        print(f"  Type: {first['event_type']}")
        print(f"  TX: {first['tx_hash']}")
        print(f"  Block: {first['block_number']:,}")
        print(f"  Absorber: {first['absorber']}")
        print(f"  Borrower: {first['borrower']}")
        if 'collateral_asset' in first:
            print(f"  Collateral asset: {first['collateral_asset']}")
            print(f"  Collateral absorbed (raw): {first['collateral_absorbed_raw']:,}")
