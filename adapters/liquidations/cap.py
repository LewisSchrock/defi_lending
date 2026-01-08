"""
Cap Liquidation Adapter (Perpetual DEX Lending)

Liquidation Mechanism:
- Vault emits Liquidate events
- Event contains liquidator, account (borrower), and amounts

Event signature:
Liquidate(
    address indexed liquidator,
    address indexed account,
    uint256 debt,
    uint256 collateral
)
"""

from typing import Dict, List, Any
from web3 import Web3
from eth_utils import keccak
import time

# Liquidate event ABI
LIQUIDATE_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "liquidator", "type": "address"},
        {"indexed": True, "name": "account", "type": "address"},
        {"indexed": False, "name": "debt", "type": "uint256"},
        {"indexed": False, "name": "collateral", "type": "uint256"},
    ],
    "name": "Liquidate",
    "type": "event",
}

# Event signature
EVENT_SIG = "Liquidate(address,address,uint256,uint256)"
TOPIC0 = keccak(text=EVENT_SIG).hex()


def _decode_liquidation(web3: Web3, log) -> Dict[str, Any]:
    """Decode a Cap Liquidate event."""
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters
    liquidator = web3.to_checksum_address('0x' + topics[1].hex()[-40:])
    account = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    
    # Decode non-indexed parameters
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    
    debt = int.from_bytes(data_bytes[0:32], 'big')
    collateral = int.from_bytes(data_bytes[32:64], 'big')
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'vault': log['address'],
        'liquidator': liquidator,
        'borrower': account,
        'debt_repaid_raw': debt,
        'collateral_seized_raw': collateral,
    }


def scan_cap_liquidations(
    web3: Web3,
    vault_address: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 10,
    max_retries: int = 3,
    pace_seconds: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Scan for Cap liquidation events from vault.
    
    Args:
        web3: Web3 instance
        vault_address: Cap vault contract address
        from_block: Start block (inclusive)
        to_block: End block (inclusive)
        chunk_size: Max blocks per eth_getLogs call
        max_retries: Number of retries on rate limit errors
        pace_seconds: Sleep duration between chunks
        
    Returns:
        List of decoded liquidation events
    """
    vault_address = Web3.to_checksum_address(vault_address)
    
    print(f"Scanning Cap vault: {vault_address}")
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
                logs = web3.eth.get_logs({
                    'fromBlock': current,
                    'toBlock': chunk_end,
                    'address': vault_address,
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
                    print(f"  Rate limit hit, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    if attempt == max_retries - 1:
                        print(f"  ❌ Failed [{current:,}, {chunk_end:,}] after {max_retries} attempts")
                        chunks_failed += 1
                    break
        
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
    
    # Cap vault on Ethereum
    vault = '0x8dee5bf2e5e68ab80cc00c3bb7fb7577ec719e04'
    
    latest = w3.eth.block_number
    from_block = latest - 10000
    
    print("Testing Cap liquidation scanning...")
    print(f"Latest block: {latest:,}")
    
    events = scan_cap_liquidations(w3, vault, from_block, latest,
                                    chunk_size=10, pace_seconds=0.1)
    
    print(f"\n✅ Found {len(events)} liquidation events")
    if events:
        print("\nFirst event:")
        first = events[0]
        print(f"  TX: {first['tx_hash']}")
        print(f"  Block: {first['block_number']:,}")
        print(f"  Liquidator: {first['liquidator']}")
        print(f"  Borrower: {first['borrower']}")
        print(f"  Debt repaid (raw): {first['debt_repaid_raw']:,}")
        print(f"  Collateral seized (raw): {first['collateral_seized_raw']:,}")
