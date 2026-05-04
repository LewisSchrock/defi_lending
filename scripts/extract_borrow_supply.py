#!/usr/bin/env python3
"""
Extract daily total_borrow_usd and total_supply_usd per CSU from bronze TVL snapshots.

Output: data/analysis/tvl_borrow_supply_daily.parquet

Usage:
    PYTHONUNBUFFERED=1 python3 scripts/extract_borrow_supply.py
"""

import json
import glob
import os
import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

BRONZE_TVL_DIR = PROJECT_ROOT / 'data' / 'bronze' / 'tvl'
OUTPUT_PATH = PROJECT_ROOT / 'data' / 'analysis' / 'tvl_borrow_supply_daily.parquet'


def load_price_caches():
    """Load both price caches."""
    t0 = time.time()
    print("Loading price caches...")

    oracle_path = PROJECT_ROOT / 'data' / 'cache' / 'prices' / 'protocol_oracle_prices.json'
    with open(oracle_path) as f:
        oracle = json.load(f)
    print(f"  Oracle cache: {len(oracle):,} entries ({time.time()-t0:.1f}s)")

    t1 = time.time()
    symbol_path = PROJECT_ROOT / 'data' / 'reference' / 'price_cache_all.json'
    with open(symbol_path) as f:
        symbol = json.load(f)
    print(f"  Symbol cache: {len(symbol):,} entries ({time.time()-t1:.1f}s)")

    print(f"  Total load time: {time.time()-t0:.1f}s")
    return oracle, symbol


STABLECOINS = {
    'USDC', 'USDT', 'DAI', 'FRAX', 'LUSD', 'sDAI', 'USDC.e', 'USDbC',
    'PYUSD', 'GHO', 'crvUSD', 'DOLA', 'USDS', 'sUSDe', 'USDe',
    'TUSD', 'BUSD', 'GUSD', 'USDP', 'USD+', 'USDD', 'MIM', 'FDUSD',
    'EURS', 'jEUR', 'EURA', 'agEUR', 'EURe', 'stEUR',
}


def get_price(oracle, symbol_cache, chain, address, symbol, date):
    # 1. Oracle cache: "chain:lowercaseaddr:date"
    if address and oracle:
        key = f"{chain}:{address.lower()}:{date}"
        price = oracle.get(key)
        if price is not None and price > 0:
            return price

    # 2. Symbol cache: "date_SYMBOL"
    price = symbol_cache.get(f"{date}_{symbol}")
    if price is not None and price > 0:
        return price

    # 3. Try uppercase
    price = symbol_cache.get(f"{date}_{symbol.upper()}")
    if price is not None and price > 0:
        return price

    # 4. Stablecoin fallback
    if symbol.upper() in STABLECOINS or symbol in STABLECOINS:
        return 1.0

    return None


NATIVE_TOKEN = {
    'ethereum': 'ETH', 'arbitrum': 'ETH', 'optimism': 'ETH',
    'base': 'ETH', 'linea': 'ETH', 'scroll': 'ETH', 'ink': 'ETH',
    'binance': 'BNB', 'polygon': 'MATIC', 'avalanche': 'AVAX',
    'gnosis': 'WXDAI', 'xdai': 'WXDAI', 'fantom': 'FTM',
    'cronos': 'CRO', 'flare': 'FLR', 'meter': 'MTR', 'sonic': 'S',
    'core': 'CORE',
}


def get_symbol(market, chain):
    sym = (
        market.get('underlying_symbol') or
        market.get('symbol') or
        market.get('token_symbol') or
        market.get('asset_symbol') or
        market.get('loan_symbol') or
        ''
    )
    if sym == 'NATIVE':
        return NATIVE_TOKEN.get(chain, 'ETH')
    return sym


def get_decimals(market):
    d = (
        market.get('underlying_decimals') or
        market.get('decimals') or
        market.get('token_decimals') or
        market.get('loan_decimals') or
        18
    )
    return int(d)


def get_supply_raw(market):
    if 'supplied_raw' in market:
        return market['supplied_raw'] or 0
    if 'tvl_underlying_raw' in market:
        return market['tvl_underlying_raw'] or 0
    if 'get_cash_raw' in market:
        cash = market.get('get_cash_raw', 0) or 0
        borrows = market.get('total_borrows_raw', 0) or 0
        return cash + borrows
    if 'total_assets_raw' in market:
        return market['total_assets_raw'] or 0
    if 'total_supply_assets_raw' in market:
        return market['total_supply_assets_raw'] or 0
    return market.get('total_supply_raw', 0) or 0


def get_borrow_raw(market):
    # Aave V2/V3
    br = (market.get('variable_debt_raw', 0) or 0) + (market.get('stable_debt_raw', 0) or 0)
    if br > 0:
        return br
    # Compound V2 / Venus / Benqi / Sonne / Mendi
    if 'total_borrows_raw' in market:
        return market['total_borrows_raw'] or 0
    # Fluid / Gearbox
    if 'total_borrow_raw' in market:
        return market['total_borrow_raw'] or 0
    if 'borrowed_raw' in market:
        return market['borrowed_raw'] or 0
    # Morpho Blue
    return market.get('total_borrow_assets_raw', 0) or 0


def normalize_chain(chain):
    aliases = {
        'bsc': 'binance', 'xdai': 'gnosis', 'matic': 'polygon',
        'avax': 'avalanche', 'ftm': 'fantom', 'op': 'optimism',
        'arb': 'arbitrum',
    }
    return aliases.get(chain.lower(), chain.lower()) if chain else ''


def get_chain_from_csu(csu):
    parts = csu.split('_')
    return parts[-1] if len(parts) >= 2 else ''


def process_csu(csu, oracle, symbol_cache):
    """Process all snapshots for one CSU, return list of (date, supply, borrow) tuples."""
    csu_dir = BRONZE_TVL_DIR / csu
    if not csu_dir.is_dir():
        return []

    chain = get_chain_from_csu(csu)
    results = []

    files = sorted(csu_dir.glob('*.json'))
    n_files = len(files)
    for fi, jf in enumerate(files, 1):
        if fi % 100 == 0 or fi == n_files:
            print(f"    {csu}: {fi}/{n_files} files", flush=True)
        try:
            with open(jf) as f:
                snap = json.load(f)
        except:
            continue

        date = snap.get('date')
        if not date:
            continue

        snap_chain = normalize_chain(snap.get('chain') or chain)
        markets = snap.get('data', snap.get('markets', []))

        total_supply = 0.0
        total_borrow = 0.0

        for m in markets:
            sym = get_symbol(m, snap_chain)
            dec = get_decimals(m)
            sr = get_supply_raw(m)
            br = get_borrow_raw(m)

            if sr == 0 and br == 0:
                continue

            addr = (m.get('underlying') or m.get('underlying_address') or
                    m.get('token_address') or m.get('loan_token') or
                    m.get('collateral_token') or m.get('address') or '')

            price = get_price(oracle, symbol_cache, snap_chain, addr, sym, date)
            if price is None or price <= 0:
                continue

            total_supply += (sr / 10**dec) * price
            total_borrow += (br / 10**dec) * price

        if total_supply > 0:
            results.append((date, total_supply, total_borrow))

    return results


def main():
    t_start = time.time()

    oracle, symbol_cache = load_price_caches()

    # Get target CSUs
    qual_path = PROJECT_ROOT / 'data' / 'analysis' / 'panel_svar_data_qualified.parquet'
    qual = pd.read_parquet(qual_path)
    target_csus = sorted(qual['csu'].unique())
    print(f"\nTarget CSUs: {len(target_csus)}")

    # Resume: load existing output and skip CSUs already done
    existing_records = []
    done_csus = set()
    if OUTPUT_PATH.exists():
        prior = pd.read_parquet(OUTPUT_PATH)
        done_csus = set(prior['csu'].unique())
        existing_records = list(prior.itertuples(index=False, name=None))
        print(f"Resuming: {len(done_csus)} CSUs already processed, {len(existing_records):,} rows loaded")

    all_records = list(existing_records)
    for i, csu in enumerate(target_csus):
        if csu in done_csus:
            print(f"  [{i+1:2d}/{len(target_csus)}] {csu:45s} SKIP (already done)")
            continue

        rows = process_csu(csu, oracle, symbol_cache)
        for date, supply, borrow in rows:
            all_records.append((date, csu, supply, borrow))

        # Checkpoint: save after each CSU
        tvl_ckpt = pd.DataFrame(all_records, columns=['date', 'csu', 'tvl_supply_usd', 'tvl_borrow_usd'])
        tvl_ckpt['date'] = pd.to_datetime(tvl_ckpt['date'])
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        tvl_ckpt.to_parquet(OUTPUT_PATH, index=False)

        elapsed = time.time() - t_start
        print(f"  [{i+1:2d}/{len(target_csus)}] {csu:45s} {len(rows):4d} snapshots  ({elapsed:.0f}s) [saved]")

    # Final sort
    tvl = pd.DataFrame(all_records, columns=['date', 'csu', 'tvl_supply_usd', 'tvl_borrow_usd'])
    tvl['date'] = pd.to_datetime(tvl['date'])
    tvl = tvl.sort_values(['csu', 'date']).reset_index(drop=True)

    print(f"\n{'='*60}")
    print(f"Extracted: {len(tvl):,} rows, {tvl['csu'].nunique()} CSUs")
    print(f"Supply USD: mean={tvl['tvl_supply_usd'].mean():,.0f}, median={tvl['tvl_supply_usd'].median():,.0f}")
    print(f"Borrow USD: mean={tvl['tvl_borrow_usd'].mean():,.0f}, median={tvl['tvl_borrow_usd'].median():,.0f}")

    # Save
    tvl.to_parquet(OUTPUT_PATH, index=False)
    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"Total time: {time.time()-t_start:.1f}s")


if __name__ == '__main__':
    main()