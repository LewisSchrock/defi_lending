"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.initReferrerTokenState = initReferrerTokenState;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([116, 45, 66, 148, 58, 13, 218, 115]);
function initReferrerTokenState(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.payer.address, role: 3, signer: accounts.payer },
        { address: accounts.lendingMarket, role: 0 },
        { address: accounts.reserve, role: 0 },
        { address: accounts.referrer, role: 0 },
        { address: accounts.referrerTokenState, role: 1 },
        { address: accounts.rent, role: 0 },
        { address: accounts.systemProgram, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=initReferrerTokenState.js.map