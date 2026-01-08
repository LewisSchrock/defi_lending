# Thesis V2 - DeFi Lending Data Pipeline

Clean, organized codebase for extracting TVL and liquidation data from DeFi lending protocols.

## Directory Structure

```
thesis_v2/
├── config/                     # Configuration files
│   ├── units.csv              # List of CSUs to collect
│   ├── rpc_config.py          # RPC URL resolver
│   └── chains.yaml            # (TODO) Chain metadata
│
├── adapters/                   # Protocol-specific adapters
│   ├── tvl/                   # TVL extraction adapters
│   │   ├── aave_v3.py
│   │   ├── compound_v3.py
│   │   └── ...
│   └── liquidations/          # Liquidation extraction adapters
│       ├── aave_v3.py
│       ├── compound_v3.py
│       └── ...
│
├── collectors/                 # Core collection logic
│   ├── tvl_collector.py       # (TODO) Generic TVL collector
│   └── liquidation_collector.py  # (TODO) Generic liquidation collector
│
├── pricing/                    # Price data management
│   ├── price_cache.py         # (TODO) Port from v1
│   └── price_resolver.py      # (TODO) Oracle + cache hybrid
│
├── utils/                      # Utility functions
│   ├── chain_registry.py      # (TODO) Port from v1
│   └── file_utils.py          # (TODO) Output management
│
├── scripts/                    # Entry point scripts
│   ├── test_single_csu.py     # Test runner for single CSU
│   ├── collect_all.py         # (TODO) Batch collection
│   └── audit_coverage.py      # (TODO) Data validation
│
├── data/                       # Data output (gitignored)
│   ├── raw/                   # Raw collection output
│   └── processed/             # Cleaned panel data
│
└── tests/                      # Unit tests
    └── test_adapters.py       # (TODO) Adapter tests
```

## Quick Start

### 1. Set up environment

```bash
# Set your Alchemy API key
export ALCHEMY_API_KEY='your_key_here'

# Install dependencies
pip install web3 pandas pyyaml requests
```

### 2. Test a single CSU

```bash
# Test TVL extraction
python scripts/test_single_csu.py aave_v3_ethereum --tvl

# Test liquidation extraction
python scripts/test_single_csu.py aave_v3_ethereum --liquidations --blocks 50000
```

### 3. Run batch collection (TODO)

```bash
python scripts/collect_all.py --from-date 2024-10-01 --to-date 2025-01-06
```

## Supported Protocols (30 CSUs)

### Working Adapters
- **Aave V3**: Ethereum, Plasma, Polygon, Binance, Linea, Arbitrum, Optimism, xDai, Base, Sonic (10 CSUs)
- **Compound V3**: Ethereum, Arbitrum, Base (3 CSUs)
- **Fluid**: Ethereum, Plasma, Arbitrum, Base (4 CSUs)
- **Venus**: Binance (1 CSU)
- **Lista**: Binance (1 CSU)
- **SparkLend**: Ethereum (1 CSU)
- **Benqi**: Avalanche (1 CSU)
- **Gearbox**: Ethereum (1 CSU)
- **cap**: Ethereum (1 CSU)
- **Moonwell**: Base (1 CSU)
- **Tectonic**: Cronos (3 versions, 3 CSUs)
- **Kinetic**: Flare (1 CSU)
- **Tydro**: Ink (1 CSU)
- **Sumer**: CORE (1 CSU)

## Design Principles

1. **Separation of concerns**: Adapters vs. collectors vs. pricing
2. **Testability**: Easy to test single CSUs without full pipeline
3. **Modularity**: Add new protocols without touching existing code
4. **Simplicity**: Clean, readable code over clever abstractions

## Development Workflow

### Adding a new protocol

1. Create TVL adapter in `adapters/tvl/protocol_name.py`
2. Create liquidation adapter in `adapters/liquidations/protocol_name.py`
3. Add CSU config to `scripts/test_single_csu.py` (temporary)
4. Test: `python scripts/test_single_csu.py protocol_chain --tvl --liquidations`
5. Once working, add to batch collection script

### Adapter Structure

Each adapter should be a simple function:

```python
def get_protocol_tvl(web3, registry, block_number):
    """
    Extract TVL for protocol at given block.
    
    Returns:
        List[Dict]: One dict per market with keys:
            - market_address
            - symbol
            - total_supplied_raw
            - total_borrowed_raw
            - decimals
    """
    pass
```

## Migration from V1

Core components to port:
- [x] RPC configuration
- [x] Test runner framework
- [ ] All working adapters
- [ ] Price cache system
- [ ] Chain registry
- [ ] Batch collection orchestrator
- [ ] Data validation / audit tools

## Next Steps

1. Port first adapter (Aave V3) as template
2. Create adapter template/skeleton
3. Port remaining 29 CSUs systematically
4. Add batch collection script
5. Scale & parallelize

## Notes

- This is a clean rewrite, keeping original code in separate directory for safety
- Focus on working CSUs first (marked 'y' in units.csv)
- Defer non-working CSUs (Euler, Capyfi, etc.) until core is stable
