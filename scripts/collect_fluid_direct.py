"""
Direct Fluid TVL collection script.
Bypasses the RPC pool and uses dRPC directly with controlled pacing.
Designed to fill in gaps left by the parallel collector.
"""
import json
import os
import sys
import time
import yaml
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from web3 import Web3
from adapters.tvl.fluid import get_fluid_tvl

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

BRONZE_DIR = Path('data/bronze/tvl')

# dRPC configuration - extract key from per-chain env vars
def get_drpc_key() -> str:
    """Extract dRPC key from environment."""
    # Try generic key first
    for i in range(1, 10):
        key = os.environ.get(f'DRPC_KEY_{i}', '')
        if key and 'drpc' not in key:
            return key

    # Extract from per-chain URL format: https://lb.drpc.live/{chain}/{key}
    for env_name in ['DRPC_KEY_ETHEREUM', 'DRPC_KEY_ARBITRUM', 'DRPC_KEY_BASE']:
        url = os.environ.get(env_name, '')
        if url and 'drpc' in url:
            raw_key = url.rstrip('/').rsplit('/', 1)[-1]
            if raw_key and raw_key != 'YOUR_KEY':
                return raw_key
    return ''


DRPC_KEY = get_drpc_key()


def get_drpc_url(chain: str) -> str:
    chain_map = {
        'ethereum': 'ethereum',
        'arbitrum': 'arbitrum',
        'base': 'base',
    }
    drpc_chain = chain_map.get(chain, chain)
    return f'https://lb.drpc.org/ogrpc?network={drpc_chain}&dkey={DRPC_KEY}'


def iterate_dates(start_str: str, end_str: str):
    d0 = date.fromisoformat(start_str)
    d1 = date.fromisoformat(end_str)
    d = d0
    while d <= d1:
        yield d.isoformat()
        d += timedelta(days=1)


def load_block_cache(chain: str) -> dict:
    """Load all block caches for a chain."""
    cache_dir = Path('data/cache')
    chain_alias = {'xdai': 'gnosis'}.get(chain, chain)

    merged = {}
    for cf in cache_dir.glob(f'{chain_alias}_blocks_*.json'):
        with open(cf) as f:
            merged.update(json.load(f))
    # Also check original name
    if chain != chain_alias:
        for cf in cache_dir.glob(f'{chain}_blocks_*.json'):
            with open(cf) as f:
                merged.update(json.load(f))
    return merged


def collect_single_date(w3, csu_name, chain, registry, date_str, block_number, output_dir):
    """Collect and save a single date."""
    output_file = output_dir / f'{date_str}.json'
    if output_file.exists():
        # Check if existing file has data
        try:
            with open(output_file) as f:
                existing = json.load(f)
            if existing.get('data') and len(existing['data']) > 0:
                return 'skip'
        except:
            pass

    try:
        # Get block timestamp
        block_data = w3.eth.get_block(block_number)
        timestamp = block_data['timestamp']

        # Call adapter
        markets = get_fluid_tvl(w3, registry, block=block_number)

        if not markets:
            return 'empty'

        # Build bronze output
        output = {
            'csu': csu_name,
            'chain': chain,
            'protocol': 'fluid',
            'version': 'v1',
            'date': date_str,
            'block': block_number,
            'timestamp': timestamp,
            'ts_start_utc': f'{date_str}T00:00:00Z',
            'ts_end_utc': f'{date_str}T23:59:59Z',
            'num_markets': len(markets),
            'data': markets,
        }

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        return 'ok'

    except Exception as e:
        return f'error: {str(e)[:80]}'


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--csu', required=True, help='CSU name')
    parser.add_argument('--start', required=True, help='Start date YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='End date YYYY-MM-DD')
    parser.add_argument('--delay', type=float, default=0.3, help='Seconds between requests')
    args = parser.parse_args()

    # Load config
    with open('code/config/csu_config.yaml') as f:
        cfg = yaml.safe_load(f)

    csu_config = cfg['csus'][args.csu]
    chain = csu_config['chain']
    registry = csu_config['registry']

    # Setup Web3 with dRPC
    if DRPC_KEY:
        rpc_url = get_drpc_url(chain)
        print(f"Using dRPC for {chain}")
    else:
        rpc_url = csu_config.get('rpc', '')
        print(f"Using config RPC for {chain}")

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
    print(f"Connected: {w3.is_connected()}")

    # Load block cache
    block_cache = load_block_cache(chain)
    print(f"Block cache: {len(block_cache)} entries")

    # Setup output dir
    output_dir = BRONZE_DIR / args.csu
    output_dir.mkdir(parents=True, exist_ok=True)

    # Count what needs collection
    dates = list(iterate_dates(args.start, args.end))
    existing = set(f.stem for f in output_dir.glob('*.json'))

    # Check which existing files actually have data
    need_collect = []
    for d in dates:
        if d not in block_cache:
            continue
        f = output_dir / f'{d}.json'
        if f.exists():
            try:
                with open(f) as fp:
                    data = json.load(fp)
                if data.get('data') and len(data['data']) > 0:
                    continue  # Already good
            except:
                pass
        need_collect.append(d)

    print(f"\nDates to collect: {len(need_collect)} (of {len(dates)} total)")

    if not need_collect:
        print("Nothing to collect!")
        return

    # Collect
    ok = 0
    empty = 0
    errors = 0
    skipped = 0

    for i, d in enumerate(need_collect):
        block = block_cache[d]['block']
        result = collect_single_date(w3, args.csu, chain, registry, d, block, output_dir)

        if result == 'ok':
            ok += 1
        elif result == 'skip':
            skipped += 1
        elif result == 'empty':
            empty += 1
        else:
            errors += 1
            if errors <= 5:
                print(f"  Error on {d}: {result}")

        # Progress
        if (i + 1) % 20 == 0:
            total = ok + empty + errors + skipped
            print(f"  [{i+1}/{len(need_collect)}] ok={ok} empty={empty} err={errors} skip={skipped}")

        # Rate limiting
        if result != 'skip':
            time.sleep(args.delay)

    print(f"\n{'='*60}")
    print(f"Done! ok={ok} empty={empty} errors={errors} skipped={skipped}")
    total_files = len(list(output_dir.glob('*.json')))
    print(f"Total files in {args.csu}: {total_files}")


if __name__ == '__main__':
    main()
