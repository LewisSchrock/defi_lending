/**
 * dump_kamino_reserves.ts
 *
 * Use the official Kamino Lend SDK to dump reserves for the main market into
 * a JSON file that Python can consume.
 *
 * Output: kamino_markets_main.json
 *   {
 *     "USDC": {
 *       "symbol": "USDC",
 *       "underlying_mint": "<mint pubkey>",
 *       "vault": "<liquidity supply vault pubkey>",
 *       "decimals": 6
 *     },
 *     ...
 *   }
 */

import { createSolanaRpc } from "@solana/kit";
import { address } from "@solana/addresses";
import {
  DEFAULT_RECENT_SLOT_DURATION_MS,
  KaminoMarket,
} from "@kamino-finance/klend-sdk";
import * as fs from "fs";
import * as path from "path";

// Main Kamino Lend market (this is your registry)
const MAIN_MARKET = address(
  "7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF"
);

// Output JSON path (next to this script)
const OUT_FILE = path.resolve(__dirname, "kamino_markets_main.json");

async function main() {
  const rpcUrl = process.env.SOLANA_RPC;
  if (!rpcUrl) {
    throw new Error("Please set SOLANA_RPC env var to a valid Solana RPC URL.");
  }

  console.log("[info] Using RPC:", rpcUrl);

  const rpc = createSolanaRpc(rpcUrl);
  console.log("[info] Solana Kit RPC client created.");

  console.log("[info] Loading Kamino market…");
  const market = await KaminoMarket.load(
    rpc,
    MAIN_MARKET,
    DEFAULT_RECENT_SLOT_DURATION_MS
  );
  if (!market) {
    throw new Error("Unable to load Kamino market");
  }
  console.log("[success] Market loaded.");

  console.log("[info] Loading reserves…");
  await market.loadReserves();
  console.log(`[success] Loaded ${market.reserves.size} reserves.`);

  const out: Record<
    string,
    {
      symbol: string;
      underlying_mint: string;
      vault: string;
      decimals: number;
    }
  > = {};

  for (const reserve of market.reserves.values()) {
    const sym = reserve.getTokenSymbol() || reserve.symbol || "UNKNOWN";
    const mint = reserve.state.liquidity.mintPubkey;
    const vault = reserve.state.liquidity.supplyVault;
    const decimals = reserve.getMintDecimals();

    if (!sym || !mint || !vault || Number.isNaN(decimals)) {
      console.warn("[warn] Skipping reserve with missing fields:", {
        symbol: sym,
        mint,
        vault,
        decimals,
      });
      continue;
    }

    out[sym] = {
      symbol: sym,
      underlying_mint: mint,
      vault: vault,
      decimals: decimals,
    };

    console.log(
      `[ok] Reserve ${sym}: mint=${mint}, vault=${vault}, decimals=${decimals}`
    );
  }

  fs.writeFileSync(OUT_FILE, JSON.stringify(out, null, 2), "utf8");
  console.log(
    `[done] Wrote ${Object.keys(out).length} reserves to ${OUT_FILE}`
  );
}

main().catch((err) => {
  console.error("[error] dump_kamino_reserves.ts failed:", err);
  process.exit(1);
});
