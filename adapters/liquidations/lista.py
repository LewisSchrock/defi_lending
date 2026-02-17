"""
Lista Lending Liquidation Adapter (Morpho-style)

Liquidation Mechanism:
- Moolah contract emits Liquidate events
- Event includes market_id to identify which market was liquidated

Event signature:
Liquidate(
    bytes32 indexed id,
    address indexed caller,
    address indexed borrower,
    uint256 repaidAssets,
    uint256 repaidShares,
    uint256 seizedAssets,
    uint256 badDebtAssets,
    uint256 badDebtShares
)
"""

from typing import Dict, List, Any
from web3 import Web3
from eth_utils import keccak
import time

# Moolah ABI - for idToMarketParams
MOOLAH_ID_TO_PARAMS_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "id", "type": "bytes32"}],
        "name": "idToMarketParams",
        "outputs": [
            {"internalType": "address", "name": "loanToken", "type": "address"},
            {"internalType": "address", "name": "collateralToken", "type": "address"},
            {"internalType": "address", "name": "oracle", "type": "address"},
            {"internalType": "address", "name": "irm", "type": "address"},
            {"internalType": "uint256", "name": "lltv", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# Liquidate event ABI
LIQUIDATE_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "id", "type": "bytes32"},
        {"indexed": True, "name": "caller", "type": "address"},
        {"indexed": True, "name": "borrower", "type": "address"},
        {"indexed": False, "name": "repaidAssets", "type": "uint256"},
        {"indexed": False, "name": "repaidShares", "type": "uint256"},
        {"indexed": False, "name": "seizedAssets", "type": "uint256"},
        {"indexed": False, "name": "badDebtAssets", "type": "uint256"},
        {"indexed": False, "name": "badDebtShares", "type": "uint256"},
    ],
    "name": "Liquidate",
    "type": "event",
}

# Event signature
EVENT_SIG = "Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)"
TOPIC0 = keccak(text=EVENT_SIG).hex()


def _decode_liquidation(web3: Web3, log) -> Dict[str, Any]:
    """Decode a Lista Liquidate event."""
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters (market_id is bytes32, addresses are padded)
    market_id = topics[1]  # Already bytes32
    caller = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    borrower = web3.to_checksum_address('0x' + topics[3].hex()[-40:])
    
    # Decode non-indexed parameters from data
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    
    # Data layout: 8 uint256 values (32 bytes each)
    repaid_assets = int.from_bytes(data_bytes[0:32], 'big')
    repaid_shares = int.from_bytes(data_bytes[32:64], 'big')
    seized_assets = int.from_bytes(data_bytes[64:96], 'big')
    bad_debt_assets = int.from_bytes(data_bytes[96:128], 'big')
    bad_debt_shares = int.from_bytes(data_bytes[128:160], 'big')
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'market_id': market_id.hex() if isinstance(market_id, bytes) else market_id,
        'liquidator': caller,
        'borrower': borrower,
        'repaid_assets_raw': repaid_assets,
        'repaid_shares_raw': repaid_shares,
        'seized_assets_raw': seized_assets,
        'bad_debt_assets_raw': bad_debt_assets,
        'bad_debt_shares_raw': bad_debt_shares,
    }


def scan_lista_liquidations(
    web3: Web3,
    moolah_address: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 10,
    max_retries: int = 3,
    pace_seconds: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Scan for Lista liquidation events from Moolah contract.
    
    Args:
        web3: Web3 instance
        moolah_address: Moolah core contract address
        from_block: Start block (inclusive)
        to_block: End block (inclusive)
        chunk_size: Max blocks per eth_getLogs call
        max_retries: Number of retries on rate limit errors
        pace_seconds: Sleep duration between chunks
        
    Returns:
        List of decoded liquidation events
    """
    moolah_address = Web3.to_checksum_address(moolah_address)
    
    print(f"Scanning Lista Moolah: {moolah_address}")
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
                    'address': moolah_address,
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
    
    rpc = get_rpc_url('binance')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    # Lista Moolah on BSC
    moolah = '0x8F73b65B4caAf64FBA2aF91cC5D4a2A1318E5D8C'
    
    latest = w3.eth.block_number
    from_block = latest - 10000
    
    print("Testing Lista liquidation scanning...")
    print(f"Latest block: {latest:,}")
    
    events = scan_lista_liquidations(w3, moolah, from_block, latest,
                                     chunk_size=10, pace_seconds=0.1)
    
    print(f"\n✅ Found {len(events)} liquidation events")
    if events:
        print("\nFirst event:")
        first = events[0]
        print(f"  TX: {first['tx_hash']}")
        print(f"  Block: {first['block_number']:,}")
        print(f"  Market ID: {first['market_id']}")
        print(f"  Liquidator: {first['liquidator']}")
        print(f"  Borrower: {first['borrower']}")
        print(f"  Repaid (raw): {first['repaid_assets_raw']:,}")
        print(f"  Seized (raw): {first['seized_assets_raw']:,}")
