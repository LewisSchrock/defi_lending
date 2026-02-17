"""
Fluid Liquidation Adapter

Liquidation Mechanism:
- Separate FluidLiquidation contract (not the resolver!)
- Emits "Liquidation" events

Event signature:
Liquidation(
    address indexed liquidator,
    address indexed user,
    address indexed debtToken,
    address collateralToken,
    uint256 debtRepaid,
    uint256 collateralSeized
)

Note: Config should have both:
- registry: FluidLendingResolver (for TVL)
- liq_registry: FluidLiquidation (for liquidations)
"""

from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_utils import keccak
import time

# Liquidation event ABI
LIQUIDATION_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "liquidator", "type": "address"},
        {"indexed": True, "name": "user", "type": "address"},
        {"indexed": True, "name": "debtToken", "type": "address"},
        {"indexed": False, "name": "collateralToken", "type": "address"},
        {"indexed": False, "name": "debtRepaid", "type": "uint256"},
        {"indexed": False, "name": "collateralSeized", "type": "uint256"},
    ],
    "name": "Liquidation",
    "type": "event",
}

# Event signature
EVENT_SIG = "Liquidation(address,address,address,address,uint256,uint256)"
TOPIC0 = keccak(text=EVENT_SIG).hex()


def _decode_liquidation(web3: Web3, log) -> Dict[str, Any]:
    """Decode a Fluid Liquidation event."""
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters (addresses from topics)
    liquidator = web3.to_checksum_address('0x' + topics[1].hex()[-40:])
    user = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    debt_token = web3.to_checksum_address('0x' + topics[3].hex()[-40:])
    
    # Decode non-indexed parameters from data
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    
    # Data layout: [collateralToken (32 bytes), debtRepaid (32 bytes), collateralSeized (32 bytes)]
    collateral_token = web3.to_checksum_address('0x' + data_bytes[0:32].hex()[-40:])
    debt_repaid = int.from_bytes(data_bytes[32:64], 'big')
    collateral_seized = int.from_bytes(data_bytes[64:96], 'big')
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'liquidator': liquidator,
        'borrower': user,
        'debt_token': debt_token,
        'collateral_token': collateral_token,
        'debt_repaid_raw': debt_repaid,
        'collateral_seized_raw': collateral_seized,
    }


def scan_fluid_liquidations(
    web3: Web3,
    liquidation_contract: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 10,
    max_retries: int = 3,
    pace_seconds: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Scan for Fluid liquidation events.
    
    Args:
        web3: Web3 instance
        liquidation_contract: FluidLiquidation contract address (NOT the resolver!)
        from_block: Start block (inclusive)
        to_block: End block (inclusive)
        chunk_size: Max blocks per eth_getLogs call (default: 10 for Alchemy)
        max_retries: Number of retries on rate limit errors
        pace_seconds: Sleep duration between chunks
        
    Returns:
        List of decoded liquidation events
    """
    liquidation_contract = Web3.to_checksum_address(liquidation_contract)
    
    print(f"Scanning FluidLiquidation: {liquidation_contract}")
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
                # Get logs for this chunk
                logs = web3.eth.get_logs({
                    'fromBlock': current,
                    'toBlock': chunk_end,
                    'address': liquidation_contract,
                    'topics': [TOPIC0],
                })
                
                # Decode each log
                for log in logs:
                    try:
                        event = _decode_liquidation(web3, log)
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
    
    # Fluid liquidation contract on Ethereum
    liq_contract = '0x129aFd8dde3b96Ea01f847CD4e5B59786A91E4d3'
    
    latest = w3.eth.block_number
    from_block = latest - 10000  # Last 10k blocks
    
    print("Testing Fluid liquidation scanning...")
    print(f"Latest block: {latest:,}")
    
    events = scan_fluid_liquidations(w3, liq_contract, from_block, latest, 
                                     chunk_size=10, pace_seconds=0.1)
    
    print(f"\n✅ Found {len(events)} liquidation events")
    if events:
        print("\nFirst event:")
        first = events[0]
        print(f"  TX: {first['tx_hash']}")
        print(f"  Block: {first['block_number']:,}")
        print(f"  Liquidator: {first['liquidator']}")
        print(f"  Borrower: {first['borrower']}")
        print(f"  Debt token: {first['debt_token']}")
        print(f"  Debt repaid (raw): {first['debt_repaid_raw']:,}")
        print(f"  Collateral token: {first['collateral_token']}")
        print(f"  Collateral seized (raw): {first['collateral_seized_raw']:,}")
