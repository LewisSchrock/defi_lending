"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.withdrawReferrerFees = withdrawReferrerFees;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([
    171, 118, 121, 201, 233, 140, 23, 228,
]);
function withdrawReferrerFees(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.referrer.address, role: 3, signer: accounts.referrer },
        { address: accounts.referrerTokenState, role: 1 },
        { address: accounts.reserve, role: 1 },
        { address: accounts.reserveLiquidityMint, role: 0 },
        { address: accounts.reserveSupplyLiquidity, role: 1 },
        { address: accounts.referrerTokenAccount, role: 1 },
        { address: accounts.lendingMarket, role: 0 },
        { address: accounts.lendingMarketAuthority, role: 0 },
        { address: accounts.tokenProgram, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=withdrawReferrerFees.js.map