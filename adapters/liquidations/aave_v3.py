"""
Aave V3 Liquidation Adapter

Scans for LiquidationCall events on the Pool contract.

Event signature:
LiquidationCall(
    address indexed collateralAsset,
    address indexed debtAsset,  
    address indexed user,
    uint256 debtToCover,
    uint256 liquidatedCollateralAmount,
    address liquidator,
    bool receiveAToken
)
"""

from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_utils import keccak

# Minimal ABIs
ADDRESSES_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

LIQUIDATION_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "collateralAsset", "type": "address"},
        {"indexed": True, "name": "debtAsset", "type": "address"},
        {"indexed": True, "name": "user", "type": "address"},
        {"indexed": False, "name": "debtToCover", "type": "uint256"},
        {"indexed": False, "name": "liquidatedCollateralAmount", "type": "uint256"},
        {"indexed": False, "name": "liquidator", "type": "address"},
        {"indexed": False, "name": "receiveAToken", "type": "bool"},
    ],
    "name": "LiquidationCall",
    "type": "event",
}

# Event signature
EVENT_SIG = "LiquidationCall(address,address,address,uint256,uint256,address,bool)"
TOPIC0 = keccak(text=EVENT_SIG).hex()


def _resolve_pool(web3: Web3, registry: str) -> str:
    """Get Pool address from registry."""
    registry = Web3.to_checksum_address(registry)
    provider = web3.eth.contract(address=registry, abi=ADDRESSES_PROVIDER_ABI)
    pool = provider.functions.getPool().call()
    return Web3.to_checksum_address(pool)


def _decode_event(web3: Web3, log) -> Dict[str, Any]:
    """Decode a LiquidationCall log into a dict."""
    # Manually decode since we have the ABI
    # topics[0] = event signature
    # topics[1] = collateralAsset (indexed)
    # topics[2] = debtAsset (indexed)
    # topics[3] = user/borrower (indexed)
    # data = debtToCover, liquidatedCollateralAmount, liquidator, receiveAToken
    
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters (addresses)
    collateral_asset = web3.to_checksum_address('0x' + topics[1].hex()[-40:])
    debt_asset = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    borrower = web3.to_checksum_address('0x' + topics[3].hex()[-40:])
    
    # Decode non-indexed parameters from data
    # data layout: [debtToCover (32 bytes), liquidatedCollateralAmount (32 bytes), 
    #               liquidator (32 bytes), receiveAToken (32 bytes)]
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    
    debt_to_cover = int.from_bytes(data_bytes[0:32], 'big')
    liquidated_collateral = int.from_bytes(data_bytes[32:64], 'big')
    liquidator = web3.to_checksum_address('0x' + data_bytes[64:96].hex()[-40:])
    receive_a_token = bool(int.from_bytes(data_bytes[96:128], 'big'))
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'collateral_asset': collateral_asset,
        'debt_asset': debt_asset,
        'borrower': borrower,
        'debt_repaid_raw': debt_to_cover,
        'collateral_seized_raw': liquidated_collateral,
        'liquidator': liquidator,
        'receive_a_token': receive_a_token,
    }


def scan_aave_liquidations(
    web3: Web3,
    registry: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 10,
    max_retries: int = 3,
    pace_seconds: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Scan for Aave V3 liquidation events with robust error handling.
    
    Args:
        web3: Web3 instance
        registry: PoolAddressesProvider address
        from_block: Start block (inclusive)
        to_block: End block (inclusive)
        chunk_size: Max blocks per eth_getLogs call (default: 10 for Alchemy free tier)
        max_retries: Number of retries on rate limit errors (default: 3)
        pace_seconds: Sleep duration between chunks (default: 0.1s)
        
    Returns:
        List of decoded liquidation events
        
    Notes:
        - Alchemy free tier requires <=10 block chunks
        - Automatically retries with exponential backoff on rate limit errors
        - Skips chunks that consistently fail after max_retries
    """
    import time
    
    # Resolve Pool address
    pool_address = _resolve_pool(web3, registry)
    
    print(f"Scanning Pool: {pool_address}")
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
                    'address': pool_address,
                    'topics': [TOPIC0],
                })
                
                # Decode each log
                for log in logs:
                    try:
                        event = _decode_event(web3, log)
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
                
                # Check if it's a rate limit error
                is_rate_limit = any(phrase in error_msg for phrase in [
                    'too many requests',
                    'rate limit',
                    'exceeded',
                    '429',
                    'compute units',
                ])
                
                if is_rate_limit and attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s...
                    wait_time = 2 ** attempt
                    print(f"  Rate limit hit on [{current:,}, {chunk_end:,}], "
                          f"retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    # Non-rate-limit error or final retry failed
                    if attempt == max_retries - 1:
                        print(f"  ❌ Failed [{current:,}, {chunk_end:,}] after {max_retries} attempts: {e}")
                        chunks_failed += 1
                    else:
                        print(f"  Warning: Error on [{current:,}, {chunk_end:,}]: {e}")
                        chunks_failed += 1
                    break
        
        # Small delay between chunks to respect rate limits
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
    
    registry = '0x2f39D218133AFaB8F2B819B1066c7E434Ad94E9e'  # Ethereum mainnet
    
    latest = w3.eth.block_number
    from_block = latest - 10000  # Last ~10k blocks (should be ~1000 chunks of 10)
    
    print("Testing Aave V3 liquidation scanning...")
    print(f"Latest block: {latest:,}")
    
    events = scan_aave_liquidations(w3, registry, from_block, latest, 
                                    chunk_size=10, pace_seconds=0.1)
    
    print(f"\n✅ Found {len(events)} liquidation events")
    if events:
        print("\nFirst event:")
        first = events[0]
        print(f"  TX: {first['tx_hash']}")
        print(f"  Block: {first['block_number']:,}")
        print(f"  Borrower: {first['borrower']}")
        print(f"  Liquidator: {first['liquidator']}")
        print(f"  Debt asset: {first['debt_asset']}")
        print(f"  Debt repaid (raw): {first['debt_repaid_raw']:,}")
        print(f"  Collateral asset: {first['collateral_asset']}")
        print(f"  Collateral seized (raw): {first['collateral_seized_raw']:,}")
