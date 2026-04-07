#!/usr/bin/env python3
"""
Unified Multi-Protocol Liquidation Collector

Efficiently collects liquidation events across ALL protocols on a chain in a single pass.
Uses eth_getLogs with multiple topic0 values (OR condition) to filter for all liquidation
event signatures simultaneously.

Design Goals:
- ONE scan per chain block range (minimize API calls)
- Single source of truth: reads from code/config/csu_config.yaml
- Incremental collection: automatically resumes from last checkpoint
- Automatic protocol detection from event signatures
- Unified output format for all protocols

Output Structure:
    data/bronze/liquidations/{chain}/
    ├── events.jsonl           # Append-only event log (one JSON per line)
    ├── checkpoint.json        # Last processed block per chain
    └── summary.json           # Collection statistics

Usage:
    # Collect all protocols on Ethereum for 2024
    python scripts/collect_liquidations_unified.py --chain ethereum --start-date 2024-01-01 --end-date 2024-12-31

    # Force restart (ignore checkpoint)
    python scripts/collect_liquidations_unified.py --chain ethereum --start-date 2024-01-01 --end-date 2024-12-31

    # Dry run to see what would be scanned
    python scripts/collect_liquidations_unified.py --chain ethereum --start-date 2024-01-01 --end-date 2024-12-31 --dry-run
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add parent to path BEFORE importing project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import yaml
import argparse
import time
from datetime import date, timedelta, datetime, timezone
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, asdict
from eth_utils import keccak
from web3 import Web3

from config.rpc_pool_v2 import get_web3_with_info, report_rpc_error, is_chain_backing_off, get_pool

# Import POA middleware
try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        from web3.middleware import geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None


# =============================================================================
# PATHS
# =============================================================================

CSU_CONFIG_PATH = Path('code/config/csu_config.yaml')
BRONZE_LIQUIDATIONS_DIR = Path('data/bronze/liquidations')
BLOCK_CACHE_DIR = Path('data/cache')


# =============================================================================
# PER-CHAIN eth_getLogs BLOCK RANGE LIMITS
# =============================================================================
# Maximum blocks per eth_getLogs call, sourced from blockchain node defaults
# and provider documentation (Chainstack, dRPC). Using these instead of a
# flat default ensures we maximize throughput per chain.

CHAIN_BLOCK_LIMITS = {
    'ethereum':   10_000,   # Geth default
    'arbitrum':   10_000,   # Nitro
    'base':       10_000,   # OP Stack
    'optimism':   10_000,   # OP Stack
    'binance':     5_000,   # BSC node limit
    'polygon':     3_500,   # Bor client
    'avalanche':   2_048,   # C-Chain
    'fantom':      5_000,   # Opera
    'gnosis':     10_000,   # xDai
    'linea':       5_000,   # Linea
    'celo':       10_000,   # Celo
    'blast':      10_000,   # OP Stack-based
    'zksync':     10_000,   # zkSync Era
    'sonic':      10_000,   # Sonic (Fantom successor)
    'manta':      10_000,   # Manta
    'scroll':     10_000,   # Scroll
}

DEFAULT_BLOCK_LIMIT = 2_000  # Conservative fallback for unknown chains


# =============================================================================
# PROTOCOL EVENT SIGNATURES
# =============================================================================

@dataclass
class EventSignature:
    """Liquidation event signature definition."""
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


# All liquidation event signatures
LIQUIDATION_EVENTS = [
    # Aave V3 / SparkLend / Tydro (Aave forks)
    EventSignature.from_signature(
        protocol='aave_v3',
        event_name='LiquidationCall',
        signature='LiquidationCall(address,address,address,uint256,uint256,address,bool)',
        indexed_params=['collateral_asset', 'debt_asset', 'borrower'],
        data_params=['debt_repaid_raw', 'collateral_seized_raw', 'liquidator', 'receive_a_token']
    ),
    # Compound V3 - AbsorbCollateral
    EventSignature.from_signature(
        protocol='compound_v3',
        event_name='AbsorbCollateral',
        signature='AbsorbCollateral(address,address,address,uint256,uint256)',
        indexed_params=['absorber', 'borrower', 'collateral_asset'],
        data_params=['collateral_absorbed_raw', 'usd_value_raw']
    ),
    # Compound V3 - AbsorbDebt
    EventSignature.from_signature(
        protocol='compound_v3',
        event_name='AbsorbDebt',
        signature='AbsorbDebt(address,address,uint256,uint256)',
        indexed_params=['absorber', 'borrower'],
        data_params=['base_paid_out_raw', 'usd_value_raw']
    ),
    # Fluid
    EventSignature.from_signature(
        protocol='fluid',
        event_name='Liquidation',
        signature='Liquidation(address,address,address,address,uint256,uint256)',
        indexed_params=['liquidator', 'borrower', 'debt_token'],
        data_params=['collateral_token', 'debt_repaid_raw', 'collateral_seized_raw']
    ),
    # Compound V2-style (Benqi, Moonwell, Kinetic, Tectonic, Sumer) — indexed liquidator+borrower
    EventSignature.from_signature(
        protocol='compound_v2',
        event_name='LiquidateBorrow',
        signature='LiquidateBorrow(address,address,uint256,address,uint256)',
        indexed_params=['liquidator', 'borrower'],
        data_params=['repay_amount_raw', 'market_token_collateral', 'seize_tokens_raw']
    ),
    # Venus on BSC — NO indexed params beyond event sig (all 5 params in data)
    EventSignature.from_signature(
        protocol='compound_v2_no_index',
        event_name='LiquidateBorrow',
        signature='LiquidateBorrow(address,address,uint256,address,uint256)',
        indexed_params=[],
        data_params=['liquidator', 'borrower', 'repay_amount_raw', 'market_token_collateral', 'seize_tokens_raw']
    ),
    # Gearbox
    EventSignature.from_signature(
        protocol='gearbox',
        event_name='LiquidateCreditAccount',
        signature='LiquidateCreditAccount(address,address,address,uint256)',
        indexed_params=['credit_account', 'liquidator'],
        data_params=['to', 'remaining_funds_raw']
    ),
    # Cap
    EventSignature.from_signature(
        protocol='cap',
        event_name='Liquidate',
        signature='Liquidate(address,address,uint256,uint256)',
        indexed_params=['liquidator', 'borrower'],
        data_params=['debt_raw', 'collateral_raw']
    ),
    # Lista (Morpho-style)
    EventSignature.from_signature(
        protocol='lista',
        event_name='Liquidate',
        signature='Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)',
        indexed_params=['market_id', 'caller', 'borrower'],
        data_params=['repaid_assets', 'repaid_shares', 'seized_assets', 'bad_debt_assets', 'bad_debt_shares']
    ),
    # Morpho Blue — singleton contract on all chains
    EventSignature.from_signature(
        protocol='morpho',
        event_name='Liquidate',
        signature='Liquidate(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)',
        indexed_params=['market_id', 'caller', 'borrower'],
        data_params=['repaid_assets', 'repaid_shares', 'seized_assets', 'bad_debt_assets', 'bad_debt_shares']
    ),
    # Euler V2 — emitted from individual EVault contracts
    # Note: 'collateral' is NOT indexed in the actual Solidity event, it's in the data
    EventSignature.from_signature(
        protocol='euler_v2',
        event_name='Liquidate',
        signature='Liquidate(address,address,address,uint256,uint256)',
        indexed_params=['liquidator', 'violator'],
        data_params=['collateral', 'repay_assets', 'yield_balance']
    ),
    # Silo V2 — emitted from PartialLiquidation hook
    EventSignature.from_signature(
        protocol='silo_v2',
        event_name='LiquidationCall',
        signature='LiquidationCall(address,address,address,uint256,uint256,bool)',
        indexed_params=['liquidator', 'silo', 'borrower'],
        data_params=['repay_debt_assets', 'withdraw_collateral', 'receive_s_token']
    ),
    # Fraxlend — emitted from individual FraxlendPair contracts
    EventSignature.from_signature(
        protocol='fraxlend',
        event_name='Liquidate',
        signature='Liquidate(address,uint256,uint256,uint256,uint256,uint256)',
        indexed_params=['borrower'],
        data_params=['collateral_for_liquidator', 'shares_to_liquidate',
                     'amount_liquidator_to_repay', 'shares_to_adjust', 'amount_to_adjust']
    ),
]

# Build lookup by topic0 — group by topic0 for signatures that share the same hash
_TOPIC0_GROUPS: Dict[str, List[EventSignature]] = {}
for _e in LIQUIDATION_EVENTS:
    _TOPIC0_GROUPS.setdefault(_e.topic0, []).append(_e)
# Primary lookup picks the first (most common) variant; decode_liquidation_event handles ambiguity
TOPIC0_TO_EVENT: Dict[str, EventSignature] = {t: es[0] for t, es in _TOPIC0_GROUPS.items()}
ALL_TOPIC0S: List[str] = list(TOPIC0_TO_EVENT.keys())


# =============================================================================
# CHAIN CONFIGURATION
# =============================================================================

POA_CHAINS = ['binance', 'polygon', 'gnosis', 'avalanche', 'optimism', 'linea', 'scroll', 'xdai', 'plasma', 'sonic', 'cronos', 'meter', 'flare', 'celo', 'blast', 'manta', 'fantom']
CHAIN_ALIASES = {'xdai': 'gnosis'}

# Protocol to adapter type mapping
PROTOCOL_TYPES = {
    # Aave V3 and forks (all emit LiquidationCall)
    'aave': 'aave_v3',
    'sparklend': 'aave_v3',
    'tydro': 'aave_v3',
    'radiant': 'aave_v3',      # Aave V2 fork — same LiquidationCall event
    'zerolend': 'aave_v3',     # Aave V3 fork
    'seamless': 'aave_v3',     # Aave V3 fork on Base
    'pac': 'aave_v3',          # Aave V3 fork on Blast
    # Compound V3
    'compound': 'compound_v3',
    # Compound V2 and forks (all emit LiquidateBorrow)
    'venus': 'compound_v2',
    'benqi': 'compound_v2',
    'moonwell': 'compound_v2',
    'kinetic': 'compound_v2',
    'tectonic': 'compound_v2',
    'sumer': 'compound_v2',
    'cream': 'compound_v2',    # Cream Finance
    'ironbank': 'compound_v2', # Iron Bank (Yearn ecosystem)
    'layerbank': 'compound_v2',
    'mendi': 'compound_v2',
    'lodestar': 'compound_v2',
    'sonne': 'compound_v2',
    'keom': 'compound_v2',
    # New protocol architectures
    'morpho': 'morpho',
    'euler': 'euler_v2',
    'silo': 'silo_v2',
    'fraxlend': 'fraxlend',
    # Other
    'fluid': 'fluid',
    'gearbox': 'gearbox',
    'cap': 'cap',
    'lista': 'lista',
}


# =============================================================================
# CONFIG LOADING
# =============================================================================

def load_csu_config() -> Dict[str, Dict]:
    """Load CSU configuration from YAML file (single source of truth)."""
    if not CSU_CONFIG_PATH.exists():
        raise FileNotFoundError(f"CSU config not found: {CSU_CONFIG_PATH}")

    with open(CSU_CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    return config.get('csus', config)


def get_csus_for_chain(chain: str, csu_config: Dict) -> List[Dict]:
    """Get all CSUs for a specific chain with their addresses resolved."""
    csus = []

    for csu_name, cfg in csu_config.items():
        csu_chain = cfg.get('chain', '')

        # Handle chain aliases
        if csu_chain == chain or CHAIN_ALIASES.get(csu_chain) == chain or CHAIN_ALIASES.get(chain) == csu_chain:
            protocol = cfg.get('protocol', '').lower()
            adapter_type = PROTOCOL_TYPES.get(protocol)

            if not adapter_type:
                continue  # Skip unsupported protocols

            csu_info = {
                'csu': csu_name,
                'protocol': protocol,
                'adapter_type': adapter_type,
                'chain': csu_chain,
            }

            # Get contract addresses based on protocol type
            if adapter_type == 'aave_v3':
                # Aave uses PoolAddressesProvider
                registry = cfg.get('registry') or cfg.get('pool_addresses_provider')
                if registry and not registry.startswith('0x'):
                    continue  # Skip non-EVM registries
                csu_info['registry'] = registry
                csu_info['contract_type'] = 'pool_provider'

            elif adapter_type == 'compound_v3':
                # Compound V3 uses direct Comet addresses
                registry = cfg.get('registry')
                if registry and registry.startswith('0x'):
                    csu_info['address'] = registry
                    csu_info['contract_type'] = 'single'

            elif adapter_type == 'fluid':
                # Fluid has separate liquidation contract
                liq_reg = cfg.get('liq_reg')
                if liq_reg and liq_reg.startswith('0x'):
                    csu_info['address'] = liq_reg
                    csu_info['contract_type'] = 'single'

            elif adapter_type == 'compound_v2':
                # Compound V2-style uses Comptroller
                registry = cfg.get('registry') or cfg.get('comptroller') or cfg.get('unitroller')
                if registry and registry.startswith('0x'):
                    csu_info['registry'] = registry
                    csu_info['contract_type'] = 'comptroller'

            elif adapter_type == 'gearbox':
                # Gearbox uses AddressProvider
                registry = cfg.get('registry')
                if registry and registry.startswith('0x'):
                    csu_info['registry'] = registry
                    csu_info['contract_type'] = 'gearbox_provider'

            elif adapter_type == 'cap':
                # Cap uses direct vault address
                registry = cfg.get('registry')
                if registry and registry.startswith('0x'):
                    csu_info['address'] = registry
                    csu_info['contract_type'] = 'single'

            elif adapter_type == 'lista':
                # Lista uses direct address
                registry = cfg.get('registry')
                if registry and registry.startswith('0x'):
                    csu_info['address'] = registry
                    csu_info['contract_type'] = 'single'

            elif adapter_type == 'morpho':
                # Morpho Blue uses singleton contract
                registry = cfg.get('registry')
                if registry and registry.startswith('0x'):
                    csu_info['address'] = registry
                    csu_info['contract_type'] = 'single'

            elif adapter_type == 'euler_v2':
                # Euler V2 uses factory for dynamic vault discovery
                factory = cfg.get('factory') or cfg.get('registry')
                vaults = cfg.get('vaults')
                if vaults:
                    # Static vault list provided
                    csu_info['addresses'] = [v for v in vaults if v.startswith('0x')]
                    csu_info['contract_type'] = 'multi'
                elif factory and factory.startswith('0x'):
                    # Dynamic discovery from factory
                    csu_info['registry'] = factory
                    csu_info['contract_type'] = 'euler_factory'

            elif adapter_type == 'silo_v2':
                # Silo V2 uses factory + hook-based liquidation
                factory = cfg.get('factory') or cfg.get('registry')
                if factory and factory.startswith('0x'):
                    csu_info['registry'] = factory
                    csu_info['contract_type'] = 'silo_factory'

            elif adapter_type == 'fraxlend':
                # Fraxlend uses deployer for pair discovery
                deployer = cfg.get('deployer') or cfg.get('registry')
                if deployer and deployer.startswith('0x'):
                    csu_info['registry'] = deployer
                    csu_info['contract_type'] = 'fraxlend_deployer'

            # Only add if we have a valid address/registry
            if 'address' in csu_info or 'registry' in csu_info or 'addresses' in csu_info:
                csus.append(csu_info)

    return csus


# =============================================================================
# CONTRACT DISCOVERY
# =============================================================================

def resolve_aave_pool(web3: Web3, registry: str) -> str:
    """Get Pool address from PoolAddressesProvider (V2 or V3)."""
    registry = Web3.to_checksum_address(registry)

    # Try Aave V3 getPool() first
    abi_v3 = [{"inputs": [], "name": "getPool", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"}]
    try:
        provider = web3.eth.contract(address=registry, abi=abi_v3)
        return Web3.to_checksum_address(provider.functions.getPool().call())
    except Exception:
        pass

    # Fall back to Aave V2 getLendingPool()
    abi_v2 = [{"inputs": [], "name": "getLendingPool", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"}]
    provider = web3.eth.contract(address=registry, abi=abi_v2)
    return Web3.to_checksum_address(provider.functions.getLendingPool().call())


def resolve_compound_v2_markets(web3: Web3, comptroller: str) -> List[str]:
    """Get all market addresses from Comptroller."""
    abi = [{"inputs": [], "name": "getAllMarkets", "outputs": [{"type": "address[]"}], "stateMutability": "view", "type": "function"}]
    comptroller = Web3.to_checksum_address(comptroller)
    contract = web3.eth.contract(address=comptroller, abi=abi)
    markets = contract.functions.getAllMarkets().call()
    return [Web3.to_checksum_address(m) for m in markets]


def resolve_gearbox_facades(web3: Web3, address_provider: str) -> List[str]:
    """Discover all Credit Facades from Gearbox AddressProvider."""
    ap_abi = [{"inputs": [], "name": "getContractsRegister", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"}]
    cr_abi = [{"inputs": [], "name": "getCreditManagers", "outputs": [{"type": "address[]"}], "stateMutability": "view", "type": "function"}]
    cm_abi = [{"inputs": [], "name": "creditFacade", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"}]

    address_provider = Web3.to_checksum_address(address_provider)
    provider = web3.eth.contract(address=address_provider, abi=ap_abi)

    contracts_register = Web3.to_checksum_address(provider.functions.getContractsRegister().call())
    cr_contract = web3.eth.contract(address=contracts_register, abi=cr_abi)
    credit_managers = cr_contract.functions.getCreditManagers().call()

    facades = []
    for cm_addr in credit_managers:
        cm_addr = Web3.to_checksum_address(cm_addr)
        cm = web3.eth.contract(address=cm_addr, abi=cm_abi)
        try:
            facade = Web3.to_checksum_address(cm.functions.creditFacade().call())
            facades.append(facade)
        except Exception:
            continue

    return facades


def resolve_euler_v2_vaults(web3: Web3, factory: str) -> List[str]:
    """Discover all EVault proxy addresses from Euler V2 GenericFactory."""
    len_abi = [{"inputs": [], "name": "getProxyListLength", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]
    slice_abi = [{"inputs": [{"type": "uint256"}, {"type": "uint256"}], "name": "getProxyListSlice", "outputs": [{"type": "address[]"}], "stateMutability": "view", "type": "function"}]

    factory = Web3.to_checksum_address(factory)
    factory_contract = web3.eth.contract(address=factory, abi=len_abi + slice_abi)

    total = factory_contract.functions.getProxyListLength().call()
    print(f"    Euler V2 factory: {total} vaults deployed")

    # Fetch in batches of 100
    vaults = []
    batch_size = 100
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = factory_contract.functions.getProxyListSlice(start, end).call()
        vaults.extend([Web3.to_checksum_address(v) for v in batch])

    return vaults


def resolve_fraxlend_pairs(web3: Web3, deployer: str) -> List[str]:
    """Discover all FraxlendPair addresses from FraxlendPairDeployer."""
    abi = [{"inputs": [], "name": "getAllPairAddresses", "outputs": [{"type": "address[]"}], "stateMutability": "view", "type": "function"}]
    deployer = Web3.to_checksum_address(deployer)
    contract = web3.eth.contract(address=deployer, abi=abi)
    pairs = contract.functions.getAllPairAddresses().call()
    print(f"    Fraxlend deployer: {len(pairs)} pairs")
    return [Web3.to_checksum_address(p) for p in pairs]


def resolve_silo_v2_silos(web3: Web3, factory: str) -> List[str]:
    """Discover Silo V2 silo addresses from SiloFactory."""
    # Silo V2 uses a hook-based liquidation via PartialLiquidation contract
    # The factory can enumerate silos, but the liquidation events come from
    # the PartialLiquidation hook contract, not the silos themselves.
    # For now, return the factory as a catch-all (events will be filtered by topic0)
    return [Web3.to_checksum_address(factory)]


def resolve_contracts(web3: Web3, csu_info: Dict) -> List[str]:
    """Resolve contract addresses for a CSU."""
    contract_type = csu_info.get('contract_type')

    try:
        if contract_type == 'single':
            addr = csu_info.get('address')
            return [Web3.to_checksum_address(addr)] if addr else []

        elif contract_type == 'multi':
            # Multiple known addresses (e.g., static vault list)
            addresses = csu_info.get('addresses', [])
            return [Web3.to_checksum_address(a) for a in addresses]

        elif contract_type == 'pool_provider':
            pool = resolve_aave_pool(web3, csu_info['registry'])
            return [pool]

        elif contract_type == 'comptroller':
            markets = resolve_compound_v2_markets(web3, csu_info['registry'])
            return markets

        elif contract_type == 'gearbox_provider':
            facades = resolve_gearbox_facades(web3, csu_info['registry'])
            return facades

        elif contract_type == 'euler_factory':
            vaults = resolve_euler_v2_vaults(web3, csu_info['registry'])
            return vaults

        elif contract_type == 'fraxlend_deployer':
            pairs = resolve_fraxlend_pairs(web3, csu_info['registry'])
            return pairs

        elif contract_type == 'silo_factory':
            return resolve_silo_v2_silos(web3, csu_info['registry'])

    except Exception as e:
        print(f"  Warning: Failed to resolve contracts for {csu_info['csu']}: {e}")

    return []


# =============================================================================
# EVENT DECODING
# =============================================================================

def decode_liquidation_event(web3: Web3, log: Dict, event_sig: EventSignature, csu: str, block_timestamp: int = None) -> Dict[str, Any]:
    """Decode a liquidation event log into a normalized dict."""
    topics = log['topics']
    data = log['data']
    data_bytes = bytes.fromhex(data[2:]) if isinstance(data, str) else data

    # Resolve ambiguous signatures: if topic count doesn't match expected indexed params,
    # try alternate signatures with same topic0 (e.g., Venus has 0 indexed params)
    n_topics = len(topics) - 1  # subtract topic[0] (event sig hash)
    if n_topics != len(event_sig.indexed_params):
        topic0 = topics[0].hex() if isinstance(topics[0], bytes) else topics[0]
        for alt_sig in _TOPIC0_GROUPS.get(topic0, []):
            if len(alt_sig.indexed_params) == n_topics:
                event_sig = alt_sig
                break

    result = {
        'tx_hash': log['transactionHash'].hex() if isinstance(log['transactionHash'], bytes) else log['transactionHash'],
        'log_index': log['logIndex'],
        'block_number': log['blockNumber'],
        'timestamp': block_timestamp,
        'date': datetime.utcfromtimestamp(block_timestamp).strftime('%Y-%m-%d') if block_timestamp else None,
        'protocol': event_sig.protocol,
        'csu': csu,
        'event_name': event_sig.event_name,
        'contract': log['address'],
    }

    # Decode indexed parameters from topics
    for i, param_name in enumerate(event_sig.indexed_params):
        topic_idx = i + 1
        if topic_idx < len(topics):
            topic = topics[topic_idx]
            topic_hex = topic.hex() if isinstance(topic, bytes) else topic

            if 'market_id' in param_name:
                result[param_name] = '0x' + topic_hex[-64:]
            else:
                result[param_name] = web3.to_checksum_address('0x' + topic_hex[-40:])

    # Decode non-indexed parameters from data
    offset = 0
    for param_name in event_sig.data_params:
        if offset + 32 > len(data_bytes):
            break

        chunk = data_bytes[offset:offset + 32]

        # Check for boolean first (receive_a_token, receive_s_token)
        if param_name.startswith('receive_') and param_name.endswith('_token'):
            result[param_name] = bool(int.from_bytes(chunk, 'big'))
        # Then check for addresses
        elif param_name in ['liquidator', 'borrower', 'to', 'absorber', 'collateral'] or (
            'token' in param_name.lower() and 'receive' not in param_name.lower()
        ):
            result[param_name] = web3.to_checksum_address('0x' + chunk.hex()[-40:])
        else:
            result[param_name] = int.from_bytes(chunk, 'big')

        offset += 32

    return result


# =============================================================================
# CHECKPOINT & OUTPUT MANAGEMENT
# =============================================================================

def get_chain_output_dir(chain: str) -> Path:
    """Get output directory for a chain."""
    output_dir = BRONZE_LIQUIDATIONS_DIR / chain
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_checkpoint(chain: str) -> Dict:
    """Load checkpoint for a chain. Returns empty dict if none exists."""
    checkpoint_file = get_chain_output_dir(chain) / 'checkpoint.json'
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            return json.load(f)
    return {}


def save_checkpoint(chain: str, last_block: int, total_events: int, contracts_count: int):
    """Save checkpoint for a chain."""
    checkpoint = {
        'chain': chain,
        'last_block': last_block,
        'total_events': total_events,
        'contracts_count': contracts_count,
        'updated_at': datetime.now(timezone.utc).isoformat(),
    }

    checkpoint_file = get_chain_output_dir(chain) / 'checkpoint.json'
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def append_events(chain: str, events: List[Dict]):
    """Append events to the JSONL file (one JSON object per line)."""
    if not events:
        return

    events_file = get_chain_output_dir(chain) / 'events.jsonl'

    with open(events_file, 'a') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')


def count_existing_events(chain: str) -> int:
    """Count existing events in the JSONL file."""
    events_file = get_chain_output_dir(chain) / 'events.jsonl'
    if not events_file.exists():
        return 0

    count = 0
    with open(events_file) as f:
        for _ in f:
            count += 1
    return count


# =============================================================================
# BLOCK CACHE
# =============================================================================

def load_block_cache(chain: str, start_date: str, end_date: str) -> Dict[str, Dict]:
    """Load block cache for date-to-block conversion.

    Merges multiple cache files if needed (e.g., separate 2024 and 2025 files).
    """
    cache_chain = CHAIN_ALIASES.get(chain, chain)

    # Try exact match first
    exact_patterns = [
        BLOCK_CACHE_DIR / f'{cache_chain}_blocks_{start_date}_{end_date}.json',
        BLOCK_CACHE_DIR / f'{chain}_blocks_{start_date}_{end_date}.json',
    ]

    for cache_file in exact_patterns:
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                    if start_date in data and end_date in data:
                        return data
            except Exception:
                continue

    # No exact match - try to merge multiple cache files
    merged_cache = {}
    cache_files_found = []

    for pattern in [f'{cache_chain}_blocks_*.json', f'{chain}_blocks_*.json']:
        for cache_file in BLOCK_CACHE_DIR.glob(pattern):
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                    merged_cache.update(data)
                    cache_files_found.append(cache_file.name)
            except Exception:
                continue

    # Check if merged cache has the dates we need
    if start_date in merged_cache and end_date in merged_cache:
        if cache_files_found:
            print(f"  Merged {len(cache_files_found)} cache files: {', '.join(cache_files_found)}")
        return merged_cache

    raise FileNotFoundError(f"No block cache found for {chain} covering {start_date} to {end_date}")


# =============================================================================
# UNIFIED SCANNER
# =============================================================================

def setup_web3_for_chain(chain: str, max_attempts: int = 20) -> Tuple[Web3, Optional[str]]:
    """Setup Web3 instance with appropriate middleware. Retries across providers."""
    rpc_chain = CHAIN_ALIASES.get(chain, chain)

    key_name = "unknown"
    for attempt in range(max_attempts):
        try:
            w3, key_name, _ = get_web3_with_info(rpc_chain)

            if chain in POA_CHAINS and geth_poa_middleware:
                try:
                    if hasattr(w3, 'middleware_onion'):
                        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                except Exception:
                    pass

            # Verify connection works
            _ = w3.eth.block_number
            return w3, key_name
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"  Provider attempt {attempt+1} failed ({key_name}): {e}")
                time.sleep(1)
            else:
                raise RuntimeError(f"All {max_attempts} provider attempts failed for {chain}: {e}")

    raise RuntimeError(f"Could not connect to {chain}")


def scan_chain_liquidations(
    chain: str,
    from_block: int,
    to_block: int,
    contracts: Dict[str, List[str]],  # {csu: [addresses]}
    chunk_size: int = 10,  # Alchemy free tier: max 10 blocks
    max_retries: int = 5,
    pace_seconds: float = 0.25,  # 250ms = 4 calls/sec (safe for rate limits)
    save_interval: int = 100,  # Save checkpoint every 100 chunks
    status_interval: int = 500,  # Print status every N chunks
    provider_rotation_interval: int = 50,  # Rotate provider every N chunks (more frequent)
    rpc_chain: str = None,  # Real chain name for RPC (if different from output chain)
) -> int:
    """
    Scan a chain for liquidation events and save incrementally.

    Returns:
        Total number of events collected
    """
    rpc_chain = rpc_chain or chain
    w3, current_provider = setup_web3_for_chain(rpc_chain)
    chunks_since_rotation = 0

    total_blocks = to_block - from_block + 1
    total_chunks = (total_blocks + chunk_size - 1) // chunk_size

    print(f"\n{'─' * 60}")
    print(f"📊 SCAN CONFIGURATION")
    print(f"{'─' * 60}")
    print(f"  Chain:           {chain}")
    print(f"  Block range:     {from_block:,} → {to_block:,}")
    print(f"  Total blocks:    {total_blocks:,}")
    print(f"  Chunk size:      {chunk_size} blocks")
    print(f"  Total chunks:    {total_chunks:,}")
    print(f"  Contracts:       {sum(len(v) for v in contracts.values())}")
    print(f"{'─' * 60}\n")

    # Build reverse mapping: address -> csu
    address_to_csu = {}
    for csu, addresses in contracts.items():
        for addr in addresses:
            address_to_csu[addr.lower()] = csu

    all_addresses = list(set(addr for addrs in contracts.values() for addr in addrs))

    # Get relevant topic0s
    relevant_topic0s = ALL_TOPIC0S

    total_events = count_existing_events(chain)
    chunks_processed = 0
    current = from_block
    scan_start_time = time.time()
    events_by_csu = {}  # Track events per CSU
    last_status_time = scan_start_time

    print(f"🚀 Starting scan... (status updates every {status_interval} chunks)\n")

    while current <= to_block:
        chunk_end = min(current + chunk_size - 1, to_block)

        # Rotate provider periodically to distribute load
        chunks_since_rotation += 1
        if chunks_since_rotation >= provider_rotation_interval:
            w3, current_provider = setup_web3_for_chain(rpc_chain)
            chunks_since_rotation = 0

        # Check backoff
        is_backing, remaining = is_chain_backing_off(rpc_chain)
        if is_backing:
            print(f"  Chain in backoff, waiting {remaining:.0f}s...")
            time.sleep(remaining + 1)
            # Get fresh provider after backoff
            w3, current_provider = setup_web3_for_chain(rpc_chain)

        chunk_events = []

        for attempt in range(max_retries):
            try:
                # Query in batches if too many addresses
                if len(all_addresses) <= 50:
                    logs = w3.eth.get_logs({
                        'fromBlock': current,
                        'toBlock': chunk_end,
                        'address': all_addresses,
                        'topics': [relevant_topic0s],
                    })
                else:
                    logs = []
                    for i in range(0, len(all_addresses), 50):
                        batch_addrs = all_addresses[i:i+50]
                        batch_logs = w3.eth.get_logs({
                            'fromBlock': current,
                            'toBlock': chunk_end,
                            'address': batch_addrs,
                            'topics': [relevant_topic0s],
                        })
                        logs.extend(batch_logs)
                        if pace_seconds > 0:
                            time.sleep(pace_seconds)

                # Get block timestamps for all unique blocks in this chunk
                block_timestamps = {}
                unique_blocks = set(log['blockNumber'] for log in logs)
                for block_num in unique_blocks:
                    try:
                        block = w3.eth.get_block(block_num)
                        block_timestamps[block_num] = block['timestamp']
                    except Exception:
                        block_timestamps[block_num] = None

                # Decode events
                for log in logs:
                    try:
                        topic0 = log['topics'][0]
                        topic0_hex = '0x' + (topic0.hex() if isinstance(topic0, bytes) else topic0[2:])

                        event_sig = TOPIC0_TO_EVENT.get(topic0_hex)
                        if not event_sig:
                            continue

                        contract_addr = log['address'].lower()
                        csu = address_to_csu.get(contract_addr, 'unknown')
                        block_ts = block_timestamps.get(log['blockNumber'])

                        event = decode_liquidation_event(w3, log, event_sig, csu, block_timestamp=block_ts)
                        chunk_events.append(event)

                        # Track events by CSU
                        events_by_csu[csu] = events_by_csu.get(csu, 0) + 1

                    except Exception as e:
                        print(f"  ⚠️  Warning: Failed to decode log: {e}")

                break  # Success

            except Exception as e:
                error_msg = str(e).lower()
                is_rate_limit = any(p in error_msg for p in ['429', 'rate limit', 'too many', 'exceeded'])
                is_block_range = 'block range' in error_msg or '10 block range' in error_msg

                if is_rate_limit:
                    report_rpc_error(rpc_chain, str(e))
                    # Rotate to a different provider on rate limit
                    w3, current_provider = setup_web3_for_chain(rpc_chain)

                if is_block_range:
                    # Auto-reduce chunk size
                    chunk_size = max(chunk_size // 2, 1)
                    print(f"  Block range too large, reducing chunk_size to {chunk_size}")
                    chunk_end = min(current + chunk_size - 1, to_block)
                    total_chunks = (to_block - current + chunk_size) // chunk_size
                    continue
                elif is_rate_limit and attempt < max_retries - 1:
                    wait_time = min(2 ** attempt + 1, 15)  # 2, 3, 5, 9, 15 seconds
                    print(f"  Rate limit on [{current:,}, {chunk_end:,}], rotating provider & waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif 'connection' in error_msg or 'remote' in error_msg or 'timeout' in error_msg:
                    # Connection error - wait briefly and rotate
                    print(f"  Connection error on [{current:,}, {chunk_end:,}], rotating provider...")
                    w3, current_provider = setup_web3_for_chain(rpc_chain)
                    time.sleep(2)  # Brief cooldown
                    if attempt >= max_retries - 1:
                        break
                else:
                    print(f"  Failed [{current:,}, {chunk_end:,}]: {e}")
                    # Try rotating provider even on other errors
                    w3, current_provider = setup_web3_for_chain(rpc_chain)
                    time.sleep(1)
                    break

        # Save events from this chunk
        if chunk_events:
            append_events(chain, chunk_events)
            total_events += len(chunk_events)
            print(f"  ✅ [{current:,} → {chunk_end:,}]: +{len(chunk_events)} events (total: {total_events:,})")

        chunks_processed += 1

        # Periodic checkpoint save
        if chunks_processed % save_interval == 0:
            save_checkpoint(chain, chunk_end, total_events, len(all_addresses))

        # Periodic status update
        if chunks_processed % status_interval == 0 or chunks_processed == 1:
            elapsed = time.time() - scan_start_time
            blocks_done = chunk_end - from_block + 1
            blocks_remaining = to_block - chunk_end
            progress_pct = (blocks_done / total_blocks) * 100

            # Calculate speed and ETA
            blocks_per_sec = blocks_done / elapsed if elapsed > 0 else 0
            chunks_per_sec = chunks_processed / elapsed if elapsed > 0 else 0
            eta_seconds = blocks_remaining / blocks_per_sec if blocks_per_sec > 0 else 0
            eta_minutes = eta_seconds / 60

            print(f"\n{'─' * 60}")
            print(f"📈 PROGRESS UPDATE (chunk {chunks_processed:,}/{total_chunks:,})")
            print(f"{'─' * 60}")
            print(f"  Progress:        {progress_pct:.1f}% complete")
            print(f"  Blocks scanned:  {blocks_done:,} / {total_blocks:,}")
            print(f"  Current block:   {chunk_end:,}")
            print(f"  Events found:    {total_events:,}")
            print(f"  Speed:           {blocks_per_sec:.1f} blocks/sec ({chunks_per_sec:.2f} chunks/sec)")
            print(f"  Elapsed:         {elapsed/60:.1f} min")
            print(f"  ETA:             {eta_minutes:.1f} min remaining")

            # Show events by CSU if any found
            if events_by_csu:
                print(f"\n  Events by CSU:")
                for csu_name, count in sorted(events_by_csu.items(), key=lambda x: -x[1]):
                    print(f"    • {csu_name}: {count:,}")

            print(f"{'─' * 60}\n")

        if pace_seconds > 0:
            time.sleep(pace_seconds)

        current = chunk_end + 1

    # Final checkpoint
    save_checkpoint(chain, to_block, total_events, len(all_addresses))

    # Final summary
    elapsed = time.time() - scan_start_time
    print(f"\n{'═' * 60}")
    print(f"✅ SCAN COMPLETE")
    print(f"{'═' * 60}")
    print(f"  Chain:           {chain}")
    print(f"  Blocks scanned:  {total_blocks:,}")
    print(f"  Total events:    {total_events:,}")
    print(f"  Total time:      {elapsed/60:.1f} min")
    print(f"  Avg speed:       {total_blocks/elapsed:.1f} blocks/sec")

    if events_by_csu:
        print(f"\n  Events by CSU:")
        for csu_name, count in sorted(events_by_csu.items(), key=lambda x: -x[1]):
            print(f"    • {csu_name}: {count:,}")

    print(f"{'═' * 60}\n")

    return total_events


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Unified Multi-Protocol Liquidation Collector')
    parser.add_argument('--chain', required=True, help='Chain to scan')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--chunk-size', type=int, default=None,
                       help='Blocks per API call (auto-set from CHAIN_BLOCK_LIMITS if omitted)')
    parser.add_argument('--pace', type=float, default=0.0, help='Seconds between API calls (0 for dRPC paid, 0.25 for rate-limited)')
    parser.add_argument('--provider', type=str, default=None,
                       help='Restrict RPC pool to a single provider (e.g. drpc, alchemy, blockpi)')
    parser.add_argument('--status-interval', type=int, default=500, help='Print status every N chunks (default: 500)')
    # --force removed: previously wiped checkpoint data on accident
    parser.add_argument('--dry-run', action='store_true', help='Show what would be scanned')
    parser.add_argument('--csu-filter', nargs='+', default=None,
                       help='Only collect for specific CSU names (uses separate checkpoint/output)')
    parser.add_argument('--output-suffix', default=None,
                       help='Suffix for output dir (e.g. "new" → data/bronze/liquidations/ethereum_new/)')

    args = parser.parse_args()
    chain = args.chain

    # Auto-set chunk_size from per-chain limits if not explicitly provided
    if args.chunk_size is None:
        args.chunk_size = CHAIN_BLOCK_LIMITS.get(chain, DEFAULT_BLOCK_LIMIT)

    # Filter RPC pool to a single provider if requested
    if args.provider:
        pool = get_pool(chain)
        before = len(pool.endpoints)
        pool.endpoints = [e for e in pool.endpoints if e.provider == args.provider]
        pool.current_idx = 0
        print(f"[Provider filter] Restricted {chain} pool to '{args.provider}': {before} → {len(pool.endpoints)} endpoints")
        if not pool.endpoints:
            print(f"ERROR: No endpoints for provider '{args.provider}' on chain '{chain}'")
            return

    # Determine output chain name (for separate output when using --csu-filter)
    output_chain = chain
    if args.output_suffix:
        output_chain = f"{chain}_{args.output_suffix}"
    elif args.csu_filter:
        output_chain = f"{chain}_new"

    print("=" * 80)
    print("Unified Multi-Protocol Liquidation Collector")
    print("=" * 80)
    print(f"Chain: {chain}")
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Chunk size: {args.chunk_size:,} blocks (limit for {chain})")
    if args.provider:
        print(f"Provider: {args.provider} only")
    if args.csu_filter:
        print(f"CSU filter: {', '.join(args.csu_filter)}")
        print(f"Output dir: data/bronze/liquidations/{output_chain}/")

    # Load CSU config (single source of truth)
    print("\nLoading CSU configuration...")
    csu_config = load_csu_config()

    # Get CSUs for this chain
    csus = get_csus_for_chain(chain, csu_config)
    if not csus:
        print(f"No configured CSUs for chain: {chain}")
        return

    # Apply CSU filter if specified
    if args.csu_filter:
        filter_set = set(args.csu_filter)
        csus = [c for c in csus if c['csu'] in filter_set]
        if not csus:
            print(f"No matching CSUs for filter: {args.csu_filter}")
            return

    print(f"Found {len(csus)} CSUs for {chain}:")
    for csu in csus:
        print(f"  - {csu['csu']} ({csu['adapter_type']})")

    # Setup web3
    w3, _ = setup_web3_for_chain(chain)
    latest_block = w3.eth.block_number
    print(f"\nLatest block: {latest_block:,}")

    # Load block cache for date conversion
    print("Loading block cache...")
    try:
        block_cache = load_block_cache(chain, args.start_date, args.end_date)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run build_block_cache.py first to create block cache for this chain/date range")
        return

    if args.start_date not in block_cache:
        print(f"Start date {args.start_date} not in block cache")
        return
    if args.end_date not in block_cache:
        print(f"End date {args.end_date} not in block cache")
        return

    from_block = block_cache[args.start_date]['block']
    to_block = block_cache[args.end_date]['block']

    # Check checkpoint for resume (uses output_chain for isolation)
    checkpoint = load_checkpoint(output_chain)
    if checkpoint:
        last_block = checkpoint.get('last_block', 0)
        if last_block >= from_block and last_block < to_block:
            print(f"\nResuming from checkpoint: block {last_block:,}")
            print(f"  Previous events: {checkpoint.get('total_events', 0)}")
            from_block = last_block + 1
        elif last_block >= to_block:
            print(f"\nCheckpoint shows collection complete for this range")
            print(f"  Total events: {checkpoint.get('total_events', 0)}")
            return

    print(f"\nBlock range: [{from_block:,}, {to_block:,}] ({to_block - from_block + 1:,} blocks)")

    # Resolve contract addresses
    print("\nResolving contract addresses...")
    contracts: Dict[str, List[str]] = {}

    for csu_info in csus:
        csu_name = csu_info['csu']
        try:
            addresses = resolve_contracts(w3, csu_info)
            if addresses:
                contracts[csu_name] = addresses
                if len(addresses) == 1:
                    print(f"  {csu_name}: {addresses[0][:20]}...")
                else:
                    print(f"  {csu_name}: {len(addresses)} contracts")
        except Exception as e:
            print(f"  {csu_name}: Failed - {e}")

    if not contracts:
        print("\nNo contracts resolved. Check CSU configuration.")
        return

    total_contracts = sum(len(v) for v in contracts.values())
    print(f"\nTotal contracts: {total_contracts}")

    if args.dry_run:
        print("\n[DRY RUN] Would scan:")
        for csu, addrs in contracts.items():
            print(f"  {csu}: {len(addrs)} contract(s)")
        return

    # Scan for liquidations (uses output_chain for isolated output)
    print("\n" + "=" * 80)
    print("Starting scan...")
    print("=" * 80)

    total_events = scan_chain_liquidations(
        chain=output_chain,
        from_block=from_block,
        to_block=to_block,
        contracts=contracts,
        chunk_size=args.chunk_size,
        pace_seconds=args.pace,
        status_interval=args.status_interval,
        rpc_chain=chain,
    )

    # Final output location reminder
    print(f"📁 Output saved to: {get_chain_output_dir(output_chain)}/events.jsonl")


if __name__ == '__main__':
    main()
