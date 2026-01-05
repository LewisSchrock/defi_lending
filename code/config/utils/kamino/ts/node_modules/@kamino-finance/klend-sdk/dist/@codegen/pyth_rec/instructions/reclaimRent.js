"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.reclaimRent = reclaimRent;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([218, 200, 19, 197, 227, 89, 192, 22]);
function reclaimRent(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.payer.address, role: 3, signer: accounts.payer },
        { address: accounts.priceUpdateAccount, role: 1 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=reclaimRent.js.map