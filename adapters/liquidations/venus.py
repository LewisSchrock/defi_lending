"""
Venus Liquidation Adapter (Compound V2 Fork)

Liquidation Mechanism:
- Each vToken emits LiquidationBorrow events
- Need to scan all vTokens from Comptroller

Event signature:
LiquidateBorrow(
    address indexed liquidator,
    address indexed borrower,
    uint256 repayAmount,
    address vTokenCollateral,
    uint256 seizeTokens
)

Note: Different from Compound V2:
- seizeTokens instead of seizeAmount
- vTokenCollateral instead of cTokenCollateral
"""

from typing import Dict, List, Any, Optional
from web3 import Web3
from eth_utils import keccak
import time

# Minimal Comptroller ABI
COMPTROLLER_ABI = [
    {
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    }
]

# LiquidateBorrow event ABI
LIQUIDATE_BORROW_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "liquidator", "type": "address"},
        {"indexed": True, "name": "borrower", "type": "address"},
        {"indexed": False, "name": "repayAmount", "type": "uint256"},
        {"indexed": False, "name": "vTokenCollateral", "type": "address"},
        {"indexed": False, "name": "seizeTokens", "type": "uint256"},
    ],
    "name": "LiquidateBorrow",
    "type": "event",
}

# Event signature
EVENT_SIG = "LiquidateBorrow(address,address,uint256,address,uint256)"
TOPIC0 = keccak(text=EVENT_SIG).hex()


def _decode_liquidation(web3: Web3, log) -> Dict[str, Any]:
    """Decode a Venus LiquidateBorrow event."""
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters (addresses from topics)
    liquidator = web3.to_checksum_address('0x' + topics[1].hex()[-40:])
    borrower = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    
    # Decode non-indexed parameters from data
    # Data layout: [repayAmount (32 bytes), vTokenCollateral (32 bytes), seizeTokens (32 bytes)]
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    
    repay_amount = int.from_bytes(data_bytes[0:32], 'big')
    vtoken_collateral = web3.to_checksum_address('0x' + data_bytes[32:64].hex()[-40:])
    seize_tokens = int.from_bytes(data_bytes[64:96], 'big')
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'vtoken_borrowed': log['address'],  # The vToken that emitted this event
        'liquidator': liquidator,
        'borrower': borrower,
        'repay_amount_raw': repay_amount,
        'vtoken_collateral': vtoken_collateral,
        'seize_tokens_raw': seize_tokens,
    }


def scan_venus_liquidations(
    web3: Web3,
    comptroller_address: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 10,
    max_retries: int = 3,
    pace_seconds: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Scan for Venus liquidation events across all vTokens.
    
    Args:
        web3: Web3 instance
        comptroller_address: Comptroller (Unitroller) contract address
        from_block: Start block (inclusive)
        to_block: End block (inclusive)
        chunk_size: Max blocks per eth_getLogs call (default: 10 for Alchemy)
        max_retries: Number of retries on rate limit errors
        pace_seconds: Sleep duration between chunks
        
    Returns:
        List of decoded liquidation events
    """
    comptroller_address = Web3.to_checksum_address(comptroller_address)
    comptroller = web3.eth.contract(address=comptroller_address, abi=COMPTROLLER_ABI)
    
    # Step 1: Get all vTokens
    print("Resolving vTokens from Comptroller...")
    vtoken_addresses = comptroller.functions.getAllMarkets().call()
    vtoken_addresses = [Web3.to_checksum_address(addr) for addr in vtoken_addresses]
    
    print(f"Found {len(vtoken_addresses)} vTokens")
    print(f"Block range: [{from_block:,}, {to_block:,}]")
    print(f"Chunk size: {chunk_size} blocks")
    
    all_events = []
    chunks_processed = 0
    chunks_failed = 0
    
    # Step 2: Scan each vToken for liquidation events
    for vtoken in vtoken_addresses:
        current = from_block
        
        while current <= to_block:
            chunk_end = min(current + chunk_size - 1, to_block)
            
            # Retry logic with exponential backoff
            for attempt in range(max_retries):
                try:
                    # Get logs for this vToken and chunk
                    logs = web3.eth.get_logs({
                        'fromBlock': current,
                        'toBlock': chunk_end,
                        'address': vtoken,
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
                        print(f"  vToken {vtoken[:10]}... [{current:,}, {chunk_end:,}]: {len(logs)} events")
                    
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
                        print(f"  Rate limit hit, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        if attempt == max_retries - 1:
                            print(f"  ❌ Failed [{current:,}, {chunk_end:,}] after {max_retries} attempts")
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
    
    rpc = get_rpc_url('binance')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    # Venus Comptroller on BSC
    comptroller = '0xfd36e2c2a6789db23113685031d7f16329158384'
    
    latest = w3.eth.block_number
    from_block = latest - 10000  # Last 10k blocks
    
    print("Testing Venus liquidation scanning...")
    print(f"Latest block: {latest:,}")
    
    events = scan_venus_liquidations(w3, comptroller, from_block, latest, 
                                     chunk_size=10, pace_seconds=0.1)
    
    print(f"\n✅ Found {len(events)} liquidation events")
    if events:
        print("\nFirst event:")
        first = events[0]
        print(f"  TX: {first['tx_hash']}")
        print(f"  Block: {first['block_number']:,}")
        print(f"  Liquidator: {first['liquidator']}")
        print(f"  Borrower: {first['borrower']}")
        print(f"  vToken borrowed: {first['vtoken_borrowed']}")
        print(f"  Repay amount (raw): {first['repay_amount_raw']:,}")
        print(f"  vToken collateral: {first['vtoken_collateral']}")
        print(f"  Seize tokens (raw): {first['seize_tokens_raw']:,}")
