#!/usr/bin/env python3
"""
Data Pipeline Status Dashboard

Shows progress across all data layers:
1. Block cache coverage (by chain and year)
2. Bronze TVL data (by CSU and year)
3. Silver TVL data / pricing (processed vs missing)
4. Liquidation data (by chain)
5. TODO box with next actions

Usage:
    python scripts/status_dashboard.py
    python scripts/status_dashboard.py --watch  # Auto-refresh every 30s
    python scripts/status_dashboard.py --detailed  # Show per-CSU breakdown
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import time
from datetime import date, timedelta, datetime
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import yaml

# Paths
CACHE_DIR = Path('data/cache')
BRONZE_DIR = Path('data/bronze/tvl')
SILVER_DIR = Path('data/silver/tvl')
LIQUIDATION_DIR = Path('data/bronze/liquidations')
PRICE_CACHE_DIR = Path('data/cache/prices')
CSU_CONFIG = Path('code/config/csu_config.yaml')
DEPLOYMENT_DATES = Path('code/config/deployment_dates.yaml')

# Date ranges
YEARS = {
    2024: ('2024-01-01', '2024-12-31'),
    2025: ('2025-01-01', '2025-12-31'),
}

# Block time estimates (seconds per block) for date estimation
BLOCK_TIMES = {
    'ethereum': 12,
    'arbitrum': 0.25,
    'avalanche': 2,
    'base': 2,
    'binance': 3,
    'cronos': 5.5,
    'flare': 1.8,
    'gnosis': 5,
    'ink': 2,
    'linea': 2,
    'meter': 2,
    'optimism': 2,
    'polygon': 2,
    'scroll': 3,
    'sonic': 0.4,
}


def iterate_dates(start_str: str, end_str: str) -> List[str]:
    """Generate list of dates from start to end (inclusive)."""
    dates = []
    d0 = date.fromisoformat(start_str)
    d1 = date.fromisoformat(end_str)
    d = d0
    while d <= d1:
        dates.append(d.isoformat())
        d += timedelta(days=1)
    return dates


def load_csu_config() -> Dict:
    """Load CSU configuration."""
    if not CSU_CONFIG.exists():
        return {}
    with open(CSU_CONFIG) as f:
        config = yaml.safe_load(f)
    return config.get('csus', config)


def load_deployment_dates() -> Dict[str, str]:
    """Load deployment dates for CSUs."""
    if not DEPLOYMENT_DATES.exists():
        return {}
    with open(DEPLOYMENT_DATES) as f:
        config = yaml.safe_load(f)
    return config.get('csus', {})


def estimate_date_from_block(chain: str, block_number: int, current_block: int = None) -> str:
    """Estimate the date for a given block number."""
    if not current_block:
        # Use approximate current blocks (updated Jan 2025)
        current_blocks = {
            'ethereum': 21_900_000,
            'arbitrum': 300_000_000,
            'avalanche': 56_000_000,
            'base': 26_000_000,
            'binance': 45_000_000,
            'cronos': 17_000_000,
            'flare': 35_000_000,
            'gnosis': 38_000_000,
            'ink': 15_000_000,
            'linea': 16_000_000,
            'meter': 65_000_000,
            'optimism': 132_000_000,
            'polygon': 67_000_000,
            'scroll': 13_000_000,
            'sonic': 20_000_000,
        }
        current_block = current_blocks.get(chain, 10_000_000)

    block_time = BLOCK_TIMES.get(chain, 2)
    blocks_behind = current_block - block_number
    seconds_behind = blocks_behind * block_time

    estimated_date = datetime.now() - timedelta(seconds=seconds_behind)
    return estimated_date.strftime('%Y-%m-%d')


def get_csus_by_chain() -> Dict[str, List[str]]:
    """Get mapping of chain -> list of CSUs."""
    csu_config = load_csu_config()
    chain_csus = defaultdict(list)

    for csu_name, csu_info in csu_config.items():
        chain = csu_info.get('chain')
        if chain:
            # Normalize chain name
            if chain == 'xdai':
                chain = 'gnosis'
            chain_csus[chain].append(csu_name)

    return dict(chain_csus)


# =============================================================================
# BLOCK CACHE STATUS
# =============================================================================

def get_block_cache_status() -> Dict:
    """Get block cache status by chain and year."""
    status = {}

    if not CACHE_DIR.exists():
        return status

    # Get all unique chains from CSU config
    csu_config = load_csu_config()
    chains = set()
    for csu in csu_config.values():
        chain = csu.get('chain')
        if chain:
            if chain == 'xdai':
                chain = 'gnosis'
            chains.add(chain)

    # Also check for cache files directly
    for cache_file in CACHE_DIR.glob('*_blocks_*.json'):
        chain = cache_file.name.split('_blocks_')[0]
        chains.add(chain)

    for chain in sorted(chains):
        status[chain] = {}

        for year, (start, end) in YEARS.items():
            expected_dates = set(iterate_dates(start, end))

            # Find cache files for this chain and year
            cache_files = list(CACHE_DIR.glob(f'{chain}_blocks_*{year}*.json'))

            if not cache_files:
                status[chain][year] = {
                    'total': len(expected_dates),
                    'cached': 0,
                    'missing': len(expected_dates),
                    'complete': False,
                }
                continue

            # Merge all cache files to get all cached dates
            cached_dates = set()
            for cache_file in cache_files:
                try:
                    with open(cache_file) as f:
                        cache = json.load(f)
                        cached_dates.update(cache.keys())
                except Exception:
                    continue

            # Filter to only dates in this year
            cached_in_year = cached_dates & expected_dates

            status[chain][year] = {
                'total': len(expected_dates),
                'cached': len(cached_in_year),
                'missing': len(expected_dates) - len(cached_in_year),
                'complete': len(cached_in_year) == len(expected_dates),
            }

    return status


# =============================================================================
# BRONZE TVL STATUS
# =============================================================================

def get_bronze_tvl_status() -> Dict:
    """Get bronze TVL data status by CSU and year."""
    status = {}

    csu_config = load_csu_config()
    deployment_dates = load_deployment_dates()

    for csu_name, csu_info in csu_config.items():
        status[csu_name] = {
            'chain': csu_info.get('chain', 'unknown'),
            'protocol': csu_info.get('protocol', 'unknown'),
        }

        csu_dir = BRONZE_DIR / csu_name

        for year, (start, end) in YEARS.items():
            expected_dates = iterate_dates(start, end)

            # Filter by deployment date
            deploy_date = deployment_dates.get(csu_name)
            if deploy_date:
                expected_dates = [d for d in expected_dates if d >= deploy_date]

            # Check which files exist
            existing = set()
            if csu_dir.exists():
                for f in csu_dir.glob('*.json'):
                    date_str = f.stem
                    if date_str.startswith(str(year)):
                        existing.add(date_str)

            expected_set = set(expected_dates)
            collected = existing & expected_set

            status[csu_name][year] = {
                'total': len(expected_set),
                'collected': len(collected),
                'missing': len(expected_set) - len(collected),
                'complete': len(collected) == len(expected_set) and len(expected_set) > 0,
            }

    return status


# =============================================================================
# SILVER TVL / PRICING STATUS
# =============================================================================

def get_silver_tvl_status() -> Dict:
    """Get silver TVL status and pricing gaps."""
    status = {
        'total_records': 0,
        'by_csu': defaultdict(int),
        'by_year': defaultdict(int),
        'tokens_with_prices': set(),
        'tokens_missing_prices': set(),
        'dates_not_processed': defaultdict(set),  # CSU -> dates without silver
        'total_supply_usd': 0.0,
        'total_borrow_usd': 0.0,
        'silver_csu_dates': defaultdict(set),  # CSU -> set of dates with silver data
    }

    # Check for consolidated silver file (daily_tvl.json)
    silver_json = SILVER_DIR / 'daily_tvl.json'
    if silver_json.exists():
        try:
            with open(silver_json) as f:
                records = json.load(f)
                status['total_records'] = len(records)

                for record in records:
                    csu = record.get('csu', 'unknown')
                    date_str = record.get('date', '')

                    # Count by CSU
                    status['by_csu'][csu] += 1

                    # Track which dates each CSU has
                    status['silver_csu_dates'][csu].add(date_str)

                    # Count by year
                    if date_str.startswith('2024'):
                        status['by_year'][2024] += 1
                    elif date_str.startswith('2025'):
                        status['by_year'][2025] += 1

                    # Accumulate totals
                    status['total_supply_usd'] += record.get('total_supply_usd', 0) or 0
                    status['total_borrow_usd'] += record.get('total_borrow_usd', 0) or 0
        except Exception:
            pass

    # Check price cache for tokens
    not_found_file = PRICE_CACHE_DIR / 'not_found.json'
    if not_found_file.exists():
        try:
            with open(not_found_file) as f:
                not_found = json.load(f)
                status['tokens_missing_prices'] = set(not_found.keys())
        except Exception:
            pass

    # Count price cache entries
    price_cache_count = 0
    if PRICE_CACHE_DIR.exists():
        for cache_file in PRICE_CACHE_DIR.glob('*.json'):
            if cache_file.name != 'not_found.json':
                try:
                    with open(cache_file) as f:
                        data = json.load(f)
                        price_cache_count += len(data)
                except Exception:
                    pass
    status['price_cache_entries'] = price_cache_count

    # Compare bronze vs silver to find unprocessed dates
    bronze_status = get_bronze_tvl_status()
    for csu_name, csu_info in bronze_status.items():
        bronze_dir = BRONZE_DIR / csu_name

        if not bronze_dir.exists():
            continue

        bronze_dates = {f.stem for f in bronze_dir.glob('*.json')}
        silver_dates = status['silver_csu_dates'].get(csu_name, set())

        unprocessed = bronze_dates - silver_dates
        if unprocessed:
            status['dates_not_processed'][csu_name] = unprocessed

    return status


# =============================================================================
# LIQUIDATION STATUS
# =============================================================================

def get_liquidation_status() -> Dict:
    """Get liquidation data status by chain."""
    status = {}
    chain_csus = get_csus_by_chain()

    if not LIQUIDATION_DIR.exists():
        # Return empty status for all chains with CSUs
        for chain, csus in chain_csus.items():
            status[chain] = {
                'events': 0,
                'last_block': None,
                'updated_at': None,
                'estimated_date': None,
                'csu_count': len(csus),
                'csus': csus,
            }
        return status

    # Get all chains with CSUs
    all_chains = set(chain_csus.keys())

    # Also add chains that have liquidation data
    for chain_dir in LIQUIDATION_DIR.iterdir():
        if chain_dir.is_dir():
            all_chains.add(chain_dir.name)

    for chain in sorted(all_chains):
        chain_dir = LIQUIDATION_DIR / chain
        events_file = chain_dir / 'events.jsonl'
        checkpoint_file = chain_dir / 'checkpoint.json'

        csus = chain_csus.get(chain, [])
        chain_status = {
            'events': 0,
            'last_block': None,
            'updated_at': None,
            'estimated_date': None,
            'csu_count': len(csus),
            'csus': csus,
        }

        # Count events
        if events_file.exists():
            with open(events_file) as f:
                chain_status['events'] = sum(1 for _ in f)

        # Load checkpoint
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file) as f:
                    checkpoint = json.load(f)
                    chain_status['last_block'] = checkpoint.get('last_block')
                    chain_status['updated_at'] = checkpoint.get('updated_at', '')[:10]

                    # Estimate date from block number
                    if chain_status['last_block']:
                        chain_status['estimated_date'] = estimate_date_from_block(
                            chain, chain_status['last_block']
                        )
            except Exception:
                pass

        status[chain] = chain_status

    return status


# =============================================================================
# TODO BOX - NEXT ACTIONS
# =============================================================================

def get_next_actions(block_status: Dict, bronze_status: Dict, silver_status: Dict, liq_status: Dict) -> List[Dict]:
    """Generate prioritized list of next actions."""
    actions = []
    chain_csus = get_csus_by_chain()

    today = date.today().isoformat()

    # 1. Check for missing block caches
    for chain, years in block_status.items():
        csus = chain_csus.get(chain, [])
        if not csus:
            continue

        for year, data in years.items():
            if not data['complete'] and data['missing'] > 0:
                # Only suggest if year is relevant (2024 always, 2025 up to today)
                if year == 2024 or (year == 2025 and today.startswith('2025')):
                    actions.append({
                        'priority': 1,
                        'type': 'block_cache',
                        'chain': chain,
                        'year': year,
                        'missing': data['missing'],
                        'csu_count': len(csus),
                        'csus': csus,
                        'command': f"python scripts/build_block_cache.py --chain {chain} --start-date {year}-01-01 --end-date {year}-12-31",
                        'description': f"Complete block cache for {chain} {year}",
                        'impact': f"Enables {len(csus)} CSUs: {', '.join(csus[:3])}{'...' if len(csus) > 3 else ''}"
                    })

    # 2. Check for missing bronze TVL data
    csus_needing_bronze = defaultdict(lambda: {'2024': 0, '2025': 0, 'csus': []})
    for csu_name, csu_data in bronze_status.items():
        chain = csu_data.get('chain', 'unknown')
        if chain == 'xdai':
            chain = 'gnosis'

        for year in [2024, 2025]:
            if year in csu_data and csu_data[year]['missing'] > 0:
                # Check if block cache exists for this chain/year
                if chain in block_status and year in block_status[chain]:
                    if block_status[chain][year]['complete']:
                        csus_needing_bronze[chain][str(year)] += csu_data[year]['missing']
                        if csu_name not in csus_needing_bronze[chain]['csus']:
                            csus_needing_bronze[chain]['csus'].append(csu_name)

    for chain, data in csus_needing_bronze.items():
        if data['2024'] > 0 or data['2025'] > 0:
            total_missing = data['2024'] + data['2025']
            actions.append({
                'priority': 2,
                'type': 'bronze_tvl',
                'chain': chain,
                'missing_days': total_missing,
                'csu_count': len(data['csus']),
                'csus': data['csus'],
                'command': f"python scripts/collect_tvl_parallel.py --start-date 2024-01-01 --end-date 2025-01-20",
                'description': f"Collect bronze TVL for {chain}",
                'impact': f"Fills {total_missing} missing days across {len(data['csus'])} CSUs"
            })

    # 3. Check for bronze data needing silver processing
    unprocessed_count = sum(len(dates) for dates in silver_status['dates_not_processed'].values())
    if unprocessed_count > 0:
        csus_to_process = list(silver_status['dates_not_processed'].keys())
        actions.append({
            'priority': 3,
            'type': 'silver_build',
            'missing_days': unprocessed_count,
            'csu_count': len(csus_to_process),
            'csus': csus_to_process,
            'command': "python scripts/build_silver_tvl.py",
            'description': "Build silver TVL from bronze data",
            'impact': f"Process {unprocessed_count} CSU-days into USD values"
        })

    # 4. Check for liquidation collection opportunities
    # Sort chains by CSU count (highest impact first)
    chains_by_impact = sorted(
        [(chain, data) for chain, data in liq_status.items() if data['csu_count'] > 0],
        key=lambda x: (-x[1]['csu_count'], x[0])
    )

    for chain, data in chains_by_impact:
        if data['events'] == 0:
            # No data yet - high priority
            actions.append({
                'priority': 4,
                'type': 'liquidation',
                'chain': chain,
                'events': 0,
                'csu_count': data['csu_count'],
                'csus': data['csus'],
                'command': f"python scripts/collect_liquidations_unified.py --chain {chain} --start-date 2024-01-01 --end-date 2025-01-20",
                'description': f"Start liquidation collection for {chain}",
                'impact': f"Covers {data['csu_count']} CSUs: {', '.join(data['csus'][:3])}{'...' if len(data['csus']) > 3 else ''}"
            })
        elif data['estimated_date'] and data['estimated_date'] < today:
            # Partial data - needs continuation
            days_behind = (date.fromisoformat(today) - date.fromisoformat(data['estimated_date'])).days
            if days_behind > 1:
                actions.append({
                    'priority': 5,
                    'type': 'liquidation_continue',
                    'chain': chain,
                    'events': data['events'],
                    'last_date': data['estimated_date'],
                    'days_behind': days_behind,
                    'csu_count': data['csu_count'],
                    'csus': data['csus'],
                    'command': f"python scripts/collect_liquidations_unified.py --chain {chain} --start-date 2024-01-01 --end-date 2025-01-20",
                    'description': f"Continue liquidation collection for {chain}",
                    'impact': f"{days_behind} days behind, {data['csu_count']} CSUs"
                })

    # Sort by priority
    actions.sort(key=lambda x: (x['priority'], -x.get('csu_count', 0)))

    return actions


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def print_header(title: str):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print('='*70)


def print_block_cache_status(status: Dict):
    """Display block cache status."""
    print_header("BLOCK CACHE STATUS")

    chain_csus = get_csus_by_chain()

    print(f"\n{'Chain':<15} {'CSUs':>5} {'2024':^20} {'2025':^20}")
    print(f"{'':<15} {'':>5} {'Cached/Total':^20} {'Cached/Total':^20}")
    print('-'*65)

    for chain in sorted(status.keys()):
        chain_data = status[chain]
        csu_count = len(chain_csus.get(chain, []))

        parts = [f"{chain:<15}", f"{csu_count:>5}"]

        for year in [2024, 2025]:
            if year in chain_data:
                data = chain_data[year]
                cached = data['cached']
                total = data['total']
                pct = (cached / total * 100) if total > 0 else 0

                if data['complete']:
                    mark = '✅'
                elif cached > 0:
                    mark = '🔄'
                else:
                    mark = '❌'

                parts.append(f"{mark} {cached:>3}/{total:<3} ({pct:>5.1f}%)")
            else:
                parts.append(f"{'N/A':^20}")

        print(' '.join(parts))

    # Summary
    complete_2024 = sum(1 for c in status.values() if c.get(2024, {}).get('complete', False))
    complete_2025 = sum(1 for c in status.values() if c.get(2025, {}).get('complete', False))
    total_chains = len(status)

    print('-'*65)
    print(f"{'Complete:':<15} {'':>5} {complete_2024:>3}/{total_chains:<3} chains      {complete_2025:>3}/{total_chains:<3} chains")


def print_bronze_tvl_status(status: Dict, detailed: bool = False):
    """Display bronze TVL status."""
    print_header("BRONZE TVL STATUS")

    # Summary by year
    summary = {2024: {'total': 0, 'collected': 0, 'csus_complete': 0},
               2025: {'total': 0, 'collected': 0, 'csus_complete': 0}}

    for csu_name, csu_data in status.items():
        for year in [2024, 2025]:
            if year in csu_data:
                summary[year]['total'] += csu_data[year]['total']
                summary[year]['collected'] += csu_data[year]['collected']
                if csu_data[year]['complete']:
                    summary[year]['csus_complete'] += 1

    total_csus = len(status)

    print(f"\n{'Year':<8} {'CSUs Complete':<18} {'Records':<25} {'Progress':<15}")
    print('-'*66)

    for year in [2024, 2025]:
        s = summary[year]
        pct = (s['collected'] / s['total'] * 100) if s['total'] > 0 else 0
        print(f"{year:<8} {s['csus_complete']:>3}/{total_csus:<3} CSUs       "
              f"{s['collected']:>6,}/{s['total']:>6,} records    {pct:>5.1f}%")

    if detailed:
        print(f"\n{'CSU':<35} {'Chain':<12} {'2024':^15} {'2025':^15}")
        print('-'*77)

        for csu_name in sorted(status.keys()):
            csu_data = status[csu_name]
            chain = csu_data.get('chain', '?')[:10]

            parts = [f"{csu_name[:34]:<35}", f"{chain:<12}"]

            for year in [2024, 2025]:
                if year in csu_data:
                    d = csu_data[year]
                    if d['complete']:
                        parts.append(f"{'✅ Complete':^15}")
                    elif d['collected'] > 0:
                        parts.append(f"🔄 {d['collected']:>3}/{d['total']:<3}")
                    else:
                        parts.append(f"{'❌ None':^15}")
                else:
                    parts.append(f"{'N/A':^15}")

            print(' '.join(parts))


def print_silver_pricing_status(status: Dict):
    """Display silver TVL and pricing status."""
    print_header("SILVER TVL & PRICING STATUS")

    print(f"\n📊 Silver Records: {status['total_records']:,}")
    print(f"   2024: {status['by_year'].get(2024, 0):,}")
    print(f"   2025: {status['by_year'].get(2025, 0):,}")
    print(f"   CSUs with data: {len(status['by_csu']):,}")

    # Show TVL totals if available
    if status.get('total_supply_usd', 0) > 0:
        total_supply = status['total_supply_usd'] / 1e9
        total_borrow = status['total_borrow_usd'] / 1e9
        print(f"\n💵 Cumulative TVL (sum across all CSU-days):")
        print(f"   Total Supply: ${total_supply:,.2f}B")
        print(f"   Total Borrow: ${total_borrow:,.2f}B")

    print(f"\n💰 Token Pricing:")
    print(f"   Price cache entries: {status.get('price_cache_entries', 0):,}")
    print(f"   Tokens missing prices: {len(status['tokens_missing_prices']):,}")

    if status['tokens_missing_prices']:
        missing = sorted(status['tokens_missing_prices'])[:20]
        print(f"   Missing: {', '.join(missing)}")
        if len(status['tokens_missing_prices']) > 20:
            print(f"   ... and {len(status['tokens_missing_prices']) - 20} more")

    # Dates not processed
    unprocessed_count = sum(len(dates) for dates in status['dates_not_processed'].values())
    print(f"\n⏳ Bronze → Silver Processing:")
    print(f"   Dates not yet processed: {unprocessed_count:,}")

    if status['dates_not_processed']:
        print("\n   CSUs with unprocessed bronze data:")
        for csu_name, dates in sorted(status['dates_not_processed'].items(),
                                       key=lambda x: -len(x[1]))[:10]:
            print(f"     {csu_name}: {len(dates)} dates")


def print_liquidation_status(status: Dict):
    """Display liquidation data status."""
    print_header("LIQUIDATION STATUS")

    if not status:
        print("\n  No liquidation data found.")
        return

    print(f"\n{'Chain':<15} {'CSUs':>6} {'Events':>10} {'Last Block':>14} {'~Date':>12} {'Updated':<12}")
    print('-'*75)

    total_events = 0
    total_csus = 0

    # Sort by CSU count (highest first)
    sorted_chains = sorted(status.items(), key=lambda x: (-x[1]['csu_count'], x[0]))

    for chain, data in sorted_chains:
        events = data['events']
        total_events += events
        total_csus += data['csu_count']

        last_block = f"{data['last_block']:,}" if data['last_block'] else '-'
        updated = data['updated_at'] or '-'
        est_date = data['estimated_date'] or '-'
        csu_count = data['csu_count']

        # Status indicator
        if events == 0:
            indicator = '❌'
        elif data['estimated_date'] and data['estimated_date'] < date.today().isoformat():
            indicator = '🔄'
        else:
            indicator = '✅'

        print(f"{indicator} {chain:<13} {csu_count:>5} {events:>10,} {last_block:>14} {est_date:>12} {updated:<12}")

    print('-'*75)
    print(f"{'Total':<15} {total_csus:>6} {total_events:>10,}")


def print_todo_box(actions: List[Dict], max_items: int = 10):
    """Display prioritized TODO box with next actions."""
    print_header("📋 NEXT ACTIONS (Priority Order)")

    if not actions:
        print("\n  ✅ All data collection tasks complete!")
        return

    print()

    for i, action in enumerate(actions[:max_items], 1):
        action_type = action['type']

        # Format based on action type
        if action_type == 'block_cache':
            print(f"  {i}. 📦 {action['description']}")
            print(f"     Missing: {action['missing']} days")
            print(f"     Impact: {action['impact']}")
            print(f"     Run: {action['command']}")

        elif action_type == 'bronze_tvl':
            print(f"  {i}. 🔶 {action['description']}")
            print(f"     Impact: {action['impact']}")
            print(f"     CSUs: {', '.join(action['csus'][:5])}{'...' if len(action['csus']) > 5 else ''}")
            print(f"     Run: {action['command']}")

        elif action_type == 'silver_build':
            print(f"  {i}. 🥈 {action['description']}")
            print(f"     Impact: {action['impact']}")
            print(f"     Run: {action['command']}")

        elif action_type == 'liquidation':
            print(f"  {i}. 💧 {action['description']}")
            print(f"     Impact: {action['impact']}")
            print(f"     Run: {action['command']}")

        elif action_type == 'liquidation_continue':
            print(f"  {i}. 💧 {action['description']} (from {action['last_date']})")
            print(f"     Status: {action['events']:,} events collected, {action['days_behind']} days behind")
            print(f"     Impact: {action['impact']}")
            print(f"     Run: {action['command']}")

        print()

    if len(actions) > max_items:
        print(f"  ... and {len(actions) - max_items} more actions")
        print()


def print_dashboard(detailed: bool = False):
    """Print full status dashboard."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{'#'*70}")
    print(f"#  DATA PIPELINE STATUS DASHBOARD")
    print(f"#  Generated: {timestamp}")
    print(f"{'#'*70}")

    # Block cache
    block_status = get_block_cache_status()
    print_block_cache_status(block_status)

    # Bronze TVL
    bronze_status = get_bronze_tvl_status()
    print_bronze_tvl_status(bronze_status, detailed=detailed)

    # Silver / Pricing
    silver_status = get_silver_tvl_status()
    print_silver_pricing_status(silver_status)

    # Liquidations
    liq_status = get_liquidation_status()
    print_liquidation_status(liq_status)

    # TODO Box
    actions = get_next_actions(block_status, bronze_status, silver_status, liq_status)
    print_todo_box(actions)

    print(f"{'='*70}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Data Pipeline Status Dashboard')
    parser.add_argument('--watch', action='store_true',
                       help='Auto-refresh every 30 seconds')
    parser.add_argument('--interval', type=int, default=30,
                       help='Refresh interval in seconds (default: 30)')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed per-CSU breakdown')

    args = parser.parse_args()

    if args.watch:
        try:
            while True:
                # Clear screen
                print('\033[2J\033[H', end='')
                print_dashboard(detailed=args.detailed)
                print(f"Auto-refreshing every {args.interval}s. Press Ctrl+C to exit.")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nExiting dashboard.")
    else:
        print_dashboard(detailed=args.detailed)


if __name__ == '__main__':
    main()
