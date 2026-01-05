"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.updateGlobalConfigAdmin = updateGlobalConfigAdmin;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([184, 87, 23, 193, 156, 238, 175, 119]);
function updateGlobalConfigAdmin(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        {
            address: accounts.pendingAdmin.address,
            role: 2,
            signer: accounts.pendingAdmin,
        },
        { address: accounts.globalConfig, role: 1 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=updateGlobalConfigAdmin.js.map