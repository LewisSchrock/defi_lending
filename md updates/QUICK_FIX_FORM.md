# Quick Fix Form - Please Provide Missing Information

## 1. Plasma RPC ✅ FIXED
Changed to: `https://plasma-mainnet.g.alchemy.com/v2/{key}`

---

## 2. Compound V3 Arbitrum (4 markets)

You mentioned: "USDC.e, USDC, WETH, USDT"

**Current registry:** `0xa5EDBDD9646f8dFFBf0e057b274Bdb8E11D2f8E0`

**Please provide:**

```
USDC.e Comet: 0x_____________________________________
USDC Comet:   0x_____________________________________
WETH Comet:   0x_____________________________________
USDT Comet:   0x_____________________________________
```

**OR**

If the current registry is a Configurator/Factory that lists all Comets:
- Function name to call: `_______________`
- Returns: array of Comet addresses? YES / NO

---

## 3. Fluid Base

**Current registry (TVL):** `0xdF4d3272FfAE8036d9a2E1626Df2Db5863b4b302` ✅

**Missing liquidation registry:**

```
liq_reg address: 0x_____________________________________
```

---

## 4. Sumer (CORE)

**Current setup (might be wrong):**
- RPC: `https://rpc.test2.btcs.network` (testnet)
- Registry: `0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B` (Ethereum mainnet address)

**Is Sumer on:**
- [ ] CORE Mainnet
- [ ] CORE Testnet

**Correct addresses:**

```
RPC URL:      https://___________________________________
Comptroller:  0x_____________________________________
```

---

## 5. Kinetic (Flare) - Verification

**Current:** `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419`

**Questions:**
- Did this work in sandbox? YES / NO
- Is this the Comptroller address? YES / NO
- Any special implementation notes: _________________

---

## 6. Cap (Ethereum) - Verification

**Current:** `0x8dee5bf2e5e68ab80cc00c3bb7fb7577ec719e04`

**Questions:**
- Did this work in sandbox? YES / NO
- Is this a vault address? YES / NO
- Are there multiple vaults we should query? YES / NO
  - If yes, provide addresses: ___________________

---

## Once You Fill This Out

Reply with the addresses and I'll:
1. Update all adapters
2. Retest all 7 failed protocols
3. Confirm 30/30 working

Should take ~10 minutes to fix once I have the info!
