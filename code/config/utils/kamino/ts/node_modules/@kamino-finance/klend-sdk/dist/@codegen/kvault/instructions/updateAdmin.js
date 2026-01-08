"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.updateAdmin = updateAdmin;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([161, 176, 40, 213, 60, 184, 179, 228]);
function updateAdmin(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        {
            address: accounts.pendingAdmin.address,
            role: 3,
            signer: accounts.pendingAdmin,
        },
        { address: accounts.vaultState, role: 1 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=updateAdmin.js.map