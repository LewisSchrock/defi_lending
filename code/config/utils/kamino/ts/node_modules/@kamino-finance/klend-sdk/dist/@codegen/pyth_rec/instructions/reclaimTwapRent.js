"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.reclaimTwapRent = reclaimTwapRent;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([84, 3, 32, 238, 108, 217, 135, 39]);
function reclaimTwapRent(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.payer.address, role: 3, signer: accounts.payer },
        { address: accounts.twapUpdateAccount, role: 1 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=reclaimTwapRent.js.map