"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.initFarmsForReserve = initFarmsForReserve;
const kit_1 = require("@solana/kit");
const src_1 = require("../../../src");
const types_1 = require("../../../src/@codegen/klend/types");
const farms_sdk_1 = require("@kamino-finance/farms-sdk");
const system_1 = require("@solana-program/system");
const sysvars_1 = require("@solana/sysvars");
const processor_1 = require("../tx/processor");
async function initFarmsForReserve(env, mode, reserve, kind) {
    const reserveState = await src_1.Reserve.fetch(env.c.rpc, reserve, env.klendProgramId);
    if (reserveState === null) {
        throw new Error(`Reserve ${reserve} not found`);
    }
    const { lendingMarket } = reserveState;
    const [lendingMarketAuthority] = await (0, src_1.lendingMarketAuthPda)(lendingMarket, env.klendProgramId);
    const market = await src_1.KaminoMarket.load(env.c.rpc, lendingMarket, src_1.DEFAULT_RECENT_SLOT_DURATION_MS, env.klendProgramId, false);
    if (!market) {
        throw new Error(`Market ${lendingMarket} not found`);
    }
    const signer = await env.getSigner(market);
    const SIZE_FARM_STATE = 8336n;
    const farmState = await (0, kit_1.generateKeyPairSigner)();
    const createFarmIx = (0, system_1.getCreateAccountInstruction)({
        payer: signer,
        newAccount: farmState,
        lamports: await env.c.rpc.getMinimumBalanceForRentExemption(SIZE_FARM_STATE).send(),
        space: SIZE_FARM_STATE,
        programAddress: env.farmsProgramId,
    });
    const ix = (0, src_1.initFarmsForReserve)({
        mode: types_1.ReserveFarmKind.fromDecoded({ [kind]: '' }).discriminator,
    }, {
        lendingMarketOwner: signer,
        lendingMarket,
        lendingMarketAuthority,
        reserve,
        farmsProgram: env.farmsProgramId,
        farmsGlobalConfig: env.farmsGlobalConfig,
        farmState: farmState.address,
        farmsVaultAuthority: await (0, farms_sdk_1.getFarmAuthorityPDA)(env.farmsProgramId, farmState.address),
        rent: sysvars_1.SYSVAR_RENT_ADDRESS,
        systemProgram: system_1.SYSTEM_PROGRAM_ADDRESS,
    });
    await (0, processor_1.processTx)(env.c, signer, [createFarmIx, ix], mode);
}
//# sourceMappingURL=initFarmsForReserve.js.map