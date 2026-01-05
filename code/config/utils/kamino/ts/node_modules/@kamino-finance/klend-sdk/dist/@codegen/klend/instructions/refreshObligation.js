"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.refreshObligation = refreshObligation;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([33, 132, 147, 228, 151, 192, 72, 89]);
function refreshObligation(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.lendingMarket, role: 0 },
        { address: accounts.obligation, role: 1 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=refreshObligation.js.map