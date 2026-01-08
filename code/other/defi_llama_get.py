#SCRAPING DeFi Llama script

import requests
import pandas as pd
from tqdm import tqdm
import json

url = "https://api.llama.fi/protocols"
resp = requests.get(url)
data = resp.json()

# Filter for lending protocols
lending = [p for p in data if p.get("category") == "Lending"]

# Filter to protocols which have a TVL > 100M
lending = [
    p
    for p in lending
    if isinstance(p.get("tvl"), (int, float)) and p["tvl"] > 100_000_000
]

# Normalize to dataframe
df = pd.json_normalize(lending)
df = df[['name', 'id', 'chains', 'tvl']].explode('chains')
df = df.sort_values('tvl', ascending=False)

df.to_csv("lending_protocols_by_chain.csv", index=False)

#make a list of the different protocol IDs from the CSV 

protocol_ids = df['name'].unique().tolist()

# Prepare list to collect data
tvl_data = []

# use the GET /v2/historicalChainTvl/{protocol} to get to TVL per protocol x chain

for pid in tqdm(protocol_ids):
    url = f"https://api.llama.fi/v2/historicalChainTvl/{pid}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"⚠️ Request failed for {pid}: {e}")
        continue

    # Inspect top-level structure
    if not isinstance(data, dict):
        print(f"❌ Unexpected top-level structure for {pid}:")
        print(json.dumps(data, indent=2))
        continue

    for version, chains in data.items():
        if not isinstance(chains, dict):
            print(f"❌ Unexpected version format in {pid} -> version: {version}")
            print("Data dump:")
            print(json.dumps(data, indent=2))
            continue

        for chain, tvl_series in chains.items():
            if not isinstance(tvl_series, list) or not tvl_series:
                continue  # skip missing or malformed data

            latest = tvl_series[-1]
            if "date" not in latest or "tvl" not in latest:
                print(f"❌ Missing expected keys in latest data for {pid} → {chain}")
                print("Data:", latest)
                continue

            tvl_data.append({
                "protocol_id": pid,
                "protocol_version": version,
                "chain": chain,
                "date": pd.to_datetime(latest["date"], unit="s"),
                "tvl": latest["tvl"]
            })

# Step 3: Save to CSV
df_tvl = pd.DataFrame(tvl_data)
df_tvl = df_tvl.sort_values('tvl', ascending=False)
df_tvl.to_csv("protocol_chain_latest_tvl.csv", index=False)