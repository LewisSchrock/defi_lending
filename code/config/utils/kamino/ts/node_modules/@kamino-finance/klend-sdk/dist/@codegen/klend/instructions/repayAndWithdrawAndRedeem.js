"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.layout = exports.DISCRIMINATOR = void 0;
exports.repayAndWithdrawAndRedeem = repayAndWithdrawAndRedeem;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([2, 54, 152, 3, 148, 96, 109, 218]);
exports.layout = borsh.struct([
    borsh.u64("repayAmount"),
    borsh.u64("withdrawCollateralAmount"),
]);
function repayAndWithdrawAndRedeem(args, accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        {
            address: accounts.repayAccounts.owner.address,
            role: 2,
            signer: accounts.repayAccounts.owner,
        },
        { address: accounts.repayAccounts.obligation, role: 1 },
        { address: accounts.repayAccounts.lendingMarket, role: 0 },
        { address: accounts.repayAccounts.repayReserve, role: 1 },
        { address: accounts.repayAccounts.reserveLiquidityMint, role: 0 },
        { address: accounts.repayAccounts.reserveDestinationLiquidity, role: 1 },
        { address: accounts.repayAccounts.userSourceLiquidity, role: 1 },
        { address: accounts.repayAccounts.tokenProgram, role: 0 },
        { address: accounts.repayAccounts.instructionSysvarAccount, role: 0 },
        {
            address: accounts.withdrawAccounts.owner.address,
            role: 3,
            signer: accounts.withdrawAccounts.owner,
        },
        { address: accounts.withdrawAccounts.obligation, role: 1 },
        { address: accounts.withdrawAccounts.lendingMarket, role: 0 },
        { address: accounts.withdrawAccounts.lendingMarketAuthority, role: 0 },
        { address: accounts.withdrawAccounts.withdrawReserve, role: 1 },
        { address: accounts.withdrawAccounts.reserveLiquidityMint, role: 0 },
        { address: accounts.withdrawAccounts.reserveSourceCollateral, role: 1 },
        { address: accounts.withdrawAccounts.reserveCollateralMint, role: 1 },
        { address: accounts.withdrawAccounts.reserveLiquiditySupply, role: 1 },
        { address: accounts.withdrawAccounts.userDestinationLiquidity, role: 1 },
        (0, kit_1.isSome)(accounts.withdrawAccounts.placeholderUserDestinationCollateral)
            ? {
                address: accounts.withdrawAccounts.placeholderUserDestinationCollateral
                    .value,
                role: 0,
            }
            : { address: programAddress, role: 0 },
        { address: accounts.withdrawAccounts.collateralTokenProgram, role: 0 },
        { address: accounts.withdrawAccounts.liquidityTokenProgram, role: 0 },
        { address: accounts.withdrawAccounts.instructionSysvarAccount, role: 0 },
        (0, kit_1.isSome)(accounts.collateralFarmsAccounts.obligationFarmUserState)
            ? {
                address: accounts.collateralFarmsAccounts.obligationFarmUserState.value,
                role: 1,
            }
            : { address: programAddress, role: 0 },
        (0, kit_1.isSome)(accounts.collateralFarmsAccounts.reserveFarmState)
            ? {
                address: accounts.collateralFarmsAccounts.reserveFarmState.value,
                role: 1,
            }
            : { address: programAddress, role: 0 },
        (0, kit_1.isSome)(accounts.debtFarmsAccounts.obligationFarmUserState)
            ? {
                address: accounts.debtFarmsAccounts.obligationFarmUserState.value,
                role: 1,
            }
            : { address: programAddress, role: 0 },
        (0, kit_1.isSome)(accounts.debtFarmsAccounts.reserveFarmState)
            ? { address: accounts.debtFarmsAccounts.reserveFarmState.value, role: 1 }
            : { address: programAddress, role: 0 },
        { address: accounts.farmsProgram, role: 0 },
        ...remainingAccounts,
    ];
    const buffer = Buffer.alloc(1000);
    const len = exports.layout.encode({
        repayAmount: args.repayAmount,
        withdrawCollateralAmount: args.withdrawCollateralAmount,
    }, buffer);
    const data = Buffer.concat([exports.DISCRIMINATOR, buffer]).slice(0, 8 + len);
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=repayAndWithdrawAndRedeem.js.map