import argparse
from .aggregator import run_chain
from .config import PROVIDERS

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csu", required=True, help="CSU key from config/csu_config.yaml")
    p.add_argument("--out-root", default="data/out", help="Root directory for output CSVs")
    p.add_argument("--no-write", action="store_true", help="Do not write CSV files; just print")
    args = p.parse_args()
    import yaml, os
    with open(os.path.join(os.path.dirname(__file__), "../config/csu_config.yaml"), "r") as f:
        csu_cfg = yaml.safe_load(f)
    cfg = csu_cfg["csus"][args.csu]
    run_chain(
        protocol=cfg["protocol"],
        chain=cfg["chain"],
        rpc_url=cfg["rpc"],
        provider_addr=cfg.get("registry"),
        out_root=cfg.get("outputs_dir", "data/out"),
        no_write=args.no_write,
        price_mode="cache",                     # You want cache mode
        registry_path="price_cache/token_registry.yaml",
        price_cache_dir="price_cache/pricing",
        price_requests_dir="price_cache/pricing/requests",
        asof_ts=None,
        asof_tolerance_sec=3600,
    )

if __name__ == "__main__":
    main()