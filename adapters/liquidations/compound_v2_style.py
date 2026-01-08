"""
Generic Compound V2-Style Liquidation Adapter

Works for any protocol following the Compound V2 liquidation pattern:
- LiquidateBorrow(liquidator, borrower, repayAmount, cTokenCollateral, seizeTokens)
- Event emitted by each market token (cToken/vToken/qToken)

Supported protocols:
- Venus (BSC)
- Benqi (Avalanche)
- Moonwell (Base)
- Kinetic (Flare)
- Tectonic (Cronos)
- Sumer (CORE)
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

# LiquidateBorrow event ABI (generic - works for all Compound V2 forks)
LIQUIDATE_BORROW_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "liquidator", "type": "address"},
        {"indexed": True, "name": "borrower", "type": "address"},
        {"indexed": False, "name": "repayAmount", "type": "uint256"},
        {"indexed": False, "name": "cTokenCollateral", "type": "address"},  # May be vToken, qToken, etc.
        {"indexed": False, "name": "seizeTokens", "type": "uint256"},
    ],
    "name": "LiquidateBorrow",
    "type": "event",
}

# Event signature (same for all)
EVENT_SIG = "LiquidateBorrow(address,address,uint256,address,uint256)"
TOPIC0 = keccak(text=EVENT_SIG).hex()


def _decode_liquidation(web3: Web3, log) -> Dict[str, Any]:
    """Decode a LiquidateBorrow event."""
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters
    liquidator = web3.to_checksum_address('0x' + topics[1].hex()[-40:])
    borrower = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    
    # Decode non-indexed parameters
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    
    repay_amount = int.from_bytes(data_bytes[0:32], 'big')
    token_collateral = web3.to_checksum_address('0x' + data_bytes[32:64].hex()[-40:])
    seize_tokens = int.from_bytes(data_bytes[64:96], 'big')
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'market_token_borrowed': log['address'],  # The token that emitted this event
        'liquidator': liquidator,
        'borrower': borrower,
        'repay_amount_raw': repay_amount,
        'market_token_collateral': token_collateral,
        'seize_tokens_raw': seize_tokens,
    }


def scan_compound_style_liquidations(
    web3: Web3,
    comptroller_address: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 10,
    max_retries: int = 3,
    pace_seconds: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Generic liquidation scanner for Compound V2-style protocols.
    
    Args:
        web3: Web3 instance
        comptroller_address: Comptroller contract address
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
    
    # Get all market tokens
    print("Resolving markets from Comptroller...")
    market_addresses = comptroller.functions.getAllMarkets().call()
    market_addresses = [Web3.to_checksum_address(addr) for addr in market_addresses]
    
    print(f"Found {len(market_addresses)} markets")
    print(f"Block range: [{from_block:,}, {to_block:,}]")
    print(f"Chunk size: {chunk_size} blocks")
    
    all_events = []
    chunks_processed = 0
    chunks_failed = 0
    
    # Scan each market for liquidation events
    for market in market_addresses:
        current = from_block
        
        while current <= to_block:
            chunk_end = min(current + chunk_size - 1, to_block)
            
            # Retry logic with exponential backoff
            for attempt in range(max_retries):
                try:
                    logs = web3.eth.get_logs({
                        'fromBlock': current,
                        'toBlock': chunk_end,
                        'address': market,
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
                        print(f"  Market {market[:10]}... [{current:,}, {chunk_end:,}]: {len(logs)} events")
                    
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
                            chunks_failed += 1
                        break
            
            if pace_seconds > 0:
                time.sleep(pace_seconds)
            
            current = chunk_end + 1
    
    print(f"\n✅ Scan complete: {chunks_processed} chunks processed, {chunks_failed} chunks failed")
    return all_events


# Convenience wrappers
def scan_venus_liquidations(web3, comptroller, from_block, to_block, **kwargs):
    """Venus on BSC."""
    return scan_compound_style_liquidations(web3, comptroller, from_block, to_block, **kwargs)

def scan_benqi_liquidations(web3, comptroller, from_block, to_block, **kwargs):
    """Benqi on Avalanche."""
    return scan_compound_style_liquidations(web3, comptroller, from_block, to_block, **kwargs)

def scan_moonwell_liquidations(web3, comptroller, from_block, to_block, **kwargs):
    """Moonwell on Base."""
    return scan_compound_style_liquidations(web3, comptroller, from_block, to_block, **kwargs)

def scan_kinetic_liquidations(web3, comptroller, from_block, to_block, **kwargs):
    """Kinetic on Flare."""
    return scan_compound_style_liquidations(web3, comptroller, from_block, to_block, **kwargs)

def scan_tectonic_liquidations(web3, comptroller, from_block, to_block, **kwargs):
    """Tectonic on Cronos."""
    return scan_compound_style_liquidations(web3, comptroller, from_block, to_block, **kwargs)

def scan_sumer_liquidations(web3, comptroller, from_block, to_block, **kwargs):
    """Sumer on CORE."""
    return scan_compound_style_liquidations(web3, comptroller, from_block, to_block, **kwargs)


if __name__ == '__main__':
    # Test with Venus
    from web3 import Web3
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.rpc_config import get_rpc_url
    
    rpc = get_rpc_url('binance')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    comptroller = '0xfd36e2c2a6789db23113685031d7f16329158384'
    
    latest = w3.eth.block_number
    from_block = latest - 1000
    
    print("Testing generic Compound-style liquidations with Venus...")
    events = scan_venus_liquidations(w3, comptroller, from_block, latest,
                                     chunk_size=10, pace_seconds=0.1)
    
    print(f"✅ Found {len(events)} events")
