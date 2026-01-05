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
exports.depositReserveLiquidity = depositReserveLiquidity;
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([169, 201, 30, 126, 6, 205, 102, 68]);
exports.layout = borsh.struct([
    borsh.u64("liquidityAmount"),
]);
function depositReserveLiquidity(args, accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.owner.address, role: 2, signer: accounts.owner },
        { address: accounts.reserve, role: 1 },
        { address: accounts.lendingMarket, role: 0 },
        { address: accounts.lendingMarketAuthority, role: 0 },
        { address: accounts.reserveLiquidityMint, role: 0 },
        { address: accounts.reserveLiquiditySupply, role: 1 },
        { address: accounts.reserveCollateralMint, role: 1 },
        { address: accounts.userSourceLiquidity, role: 1 },
        { address: accounts.userDestinationCollateral, role: 1 },
        { address: accounts.collateralTokenProgram, role: 0 },
        { address: accounts.liquidityTokenProgram, role: 0 },
        { address: accounts.instructionSysvarAccount, role: 0 },
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
//# sourceMappingURL=depositReserveLiquidity.js.map