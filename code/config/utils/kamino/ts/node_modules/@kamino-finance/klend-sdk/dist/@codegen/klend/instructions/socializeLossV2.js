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
exports.socializeLossV2 = socializeLossV2;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([238, 95, 98, 220, 187, 40, 204, 154]);
exports.layout = borsh.struct([
    borsh.u64("liquidityAmount"),
]);
function socializeLossV2(args, accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        {
            address: accounts.socializeLossAccounts.riskCouncil.address,
            role: 2,
            signer: accounts.socializeLossAccounts.riskCouncil,
        },
        { address: accounts.socializeLossAccounts.obligation, role: 1 },
        { address: accounts.socializeLossAccounts.lendingMarket, role: 0 },
        { address: accounts.socializeLossAccounts.reserve, role: 1 },
        {
            address: accounts.socializeLossAccounts.instructionSysvarAccount,
            role: 0,
        },
        (0, kit_1.isSome)(accounts.farmsAccounts.obligationFarmUserState)
            ? {
                address: accounts.farmsAccounts.obligationFarmUserState.value,
                role: 1,
            }
            : { address: programAddress, role: 0 },
        (0, kit_1.isSome)(accounts.farmsAccounts.reserveFarmState)
            ? { address: accounts.farmsAccounts.reserveFarmState.value, role: 1 }
            : { address: programAddress, role: 0 },
        { address: accounts.lendingMarketAuthority, role: 0 },
        { address: accounts.farmsProgram, role: 0 },
        ...remainingAccounts,
    ];
    const buffer = Buffer.alloc(1000);
    const len = exports.layout.encode({
        liquidityAmount: args.liquidityAmount,
    }, buffer);
    const data = Buffer.concat([exports.DISCRIMINATOR, buffer]).slice(0, 8 + len);
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=socializeLossV2.js.map