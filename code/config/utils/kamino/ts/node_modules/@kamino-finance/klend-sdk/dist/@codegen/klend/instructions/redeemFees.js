"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.redeemFees = redeemFees;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([215, 39, 180, 41, 173, 46, 248, 220]);
function redeemFees(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.reserve, role: 1 },
        { address: accounts.reserveLiquidityMint, role: 0 },
        { address: accounts.reserveLiquidityFeeReceiver, role: 1 },
        { address: accounts.reserveSupplyLiquidity, role: 1 },
        { address: accounts.lendingMarket, role: 0 },
        { address: accounts.lendingMarketAuthority, role: 0 },
        { address: accounts.tokenProgram, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=redeemFees.js.map