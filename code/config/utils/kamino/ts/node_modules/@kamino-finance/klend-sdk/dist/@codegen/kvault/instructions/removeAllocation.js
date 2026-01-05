"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.removeAllocation = removeAllocation;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([32, 220, 211, 141, 209, 231, 73, 76]);
function removeAllocation(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        {
            address: accounts.vaultAdminAuthority.address,
            role: 3,
            signer: accounts.vaultAdminAuthority,
        },
        { address: accounts.vaultState, role: 1 },
        { address: accounts.reserve, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=removeAllocation.js.map