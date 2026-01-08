"""
Gearbox Liquidation Adapter (Credit Account System)

Liquidation Mechanism:
- Credit Facades emit LiquidateCreditAccount events
- Each event contains creditAccount, liquidator, and remainingFunds

Event signature:
LiquidateCreditAccount(
    address indexed creditAccount,
    address indexed liquidator,
    address to,
    uint256 remainingFunds
)

Discovery:
1. Get ContractsRegister from AddressProvider
2. Get Credit Managers
3. Get Credit Facade from each Credit Manager
4. Scan all Credit Facades for liquidation events
"""

from typing import Dict, List, Any
from web3 import Web3
from eth_utils import keccak
import time

# AddressProvider ABI
ADDRESS_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getContractsRegister",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# ContractsRegister ABI
CONTRACTS_REGISTER_ABI = [
    {
        "inputs": [],
        "name": "getCreditManagers",
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# CreditManager ABI
CREDIT_MANAGER_ABI = [
    {
        "inputs": [],
        "name": "creditFacade",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# LiquidateCreditAccount event ABI
LIQUIDATE_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "creditAccount", "type": "address"},
        {"indexed": True, "name": "liquidator", "type": "address"},
        {"indexed": False, "name": "to", "type": "address"},
        {"indexed": False, "name": "remainingFunds", "type": "uint256"},
    ],
    "name": "LiquidateCreditAccount",
    "type": "event",
}

# Event signature
EVENT_SIG = "LiquidateCreditAccount(address,address,address,uint256)"
TOPIC0 = keccak(text=EVENT_SIG).hex()


def _discover_credit_facades(web3: Web3, address_provider: str) -> List[str]:
    """Discover all Credit Facades from AddressProvider."""
    address_provider = Web3.to_checksum_address(address_provider)
    
    # Get ContractsRegister
    provider = web3.eth.contract(address=address_provider, abi=ADDRESS_PROVIDER_ABI)
    contracts_register_addr = provider.functions.getContractsRegister().call()
    contracts_register_addr = Web3.to_checksum_address(contracts_register_addr)
    
    # Get all Credit Managers
    contracts_register = web3.eth.contract(address=contracts_register_addr, abi=CONTRACTS_REGISTER_ABI)
    credit_managers = contracts_register.functions.getCreditManagers().call()
    
    # Get Credit Facade from each Credit Manager
    facades = []
    for cm_addr in credit_managers:
        cm_addr = Web3.to_checksum_address(cm_addr)
        credit_manager = web3.eth.contract(address=cm_addr, abi=CREDIT_MANAGER_ABI)
        
        try:
            facade_addr = credit_manager.functions.creditFacade().call()
            facade_addr = Web3.to_checksum_address(facade_addr)
            facades.append(facade_addr)
        except Exception:
            continue
    
    return facades


def _decode_liquidation(web3: Web3, log) -> Dict[str, Any]:
    """Decode a LiquidateCreditAccount event."""
    topics = log['topics']
    data = log['data']
    
    # Decode indexed parameters
    credit_account = web3.to_checksum_address('0x' + topics[1].hex()[-40:])
    liquidator = web3.to_checksum_address('0x' + topics[2].hex()[-40:])
    
    # Decode non-indexed parameters
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data
    
    to = web3.to_checksum_address('0x' + data_bytes[0:32].hex()[-40:])
    remaining_funds = int.from_bytes(data_bytes[32:64], 'big')
    
    return {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'credit_facade': log['address'],
        'credit_account': credit_account,
        'liquidator': liquidator,
        'to': to,
        'remaining_funds_raw': remaining_funds,
    }


def scan_gearbox_liquidations(
    web3: Web3,
    address_provider: str,
    from_block: int,
    to_block: int,
    chunk_size: int = 10,
    max_retries: int = 3,
    pace_seconds: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Scan for Gearbox liquidation events across all Credit Facades.
    
    Args:
        web3: Web3 instance
        address_provider: AddressProvider contract address
        from_block: Start block (inclusive)
        to_block: End block (inclusive)
        chunk_size: Max blocks per eth_getLogs call
        max_retries: Number of retries on rate limit errors
        pace_seconds: Sleep duration between chunks
        
    Returns:
        List of decoded liquidation events
    """
    # Discover Credit Facades
    print("Discovering Credit Facades...")
    facades = _discover_credit_facades(web3, address_provider)
    print(f"Found {len(facades)} Credit Facades")
    
    print(f"Block range: [{from_block:,}, {to_block:,}]")
    print(f"Chunk size: {chunk_size} blocks")
    
    all_events = []
    chunks_processed = 0
    chunks_failed = 0
    
    # Scan each Credit Facade
    for facade in facades:
        facade = Web3.to_checksum_address(facade)
        current = from_block
        
        while current <= to_block:
            chunk_end = min(current + chunk_size - 1, to_block)
            
            # Retry logic with exponential backoff
            for attempt in range(max_retries):
                try:
                    logs = web3.eth.get_logs({
                        'fromBlock': current,
                        'toBlock': chunk_end,
                        'address': facade,
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
                        print(f"  Facade {facade[:10]}... [{current:,}, {chunk_end:,}]: {len(logs)} events")
                    
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


if __name__ == '__main__':
    # Quick test
    from web3 import Web3
    import sys
    import os
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.rpc_config import get_rpc_url
    
    rpc = get_rpc_url('ethereum')
    w3 = Web3(Web3.HTTPProvider(rpc))
    
    # Gearbox AddressProvider on Ethereum
    address_provider = '0xcF64698AFF7E5f27A11dff868AF228653ba53be0'
    
    latest = w3.eth.block_number
    from_block = latest - 10000
    
    print("Testing Gearbox liquidation scanning...")
    print(f"Latest block: {latest:,}")
    
    events = scan_gearbox_liquidations(w3, address_provider, from_block, latest,
                                        chunk_size=10, pace_seconds=0.1)
    
    print(f"\n✅ Found {len(events)} liquidation events")
    if events:
        print("\nFirst event:")
        first = events[0]
        print(f"  TX: {first['tx_hash']}")
        print(f"  Block: {first['block_number']:,}")
        print(f"  Credit Account: {first['credit_account']}")
        print(f"  Liquidator: {first['liquidator']}")
        print(f"  Remaining Funds (raw): {first['remaining_funds_raw']:,}")
