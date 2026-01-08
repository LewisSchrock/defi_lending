"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.initVault = initVault;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([77, 79, 85, 150, 33, 217, 52, 106]);
function initVault(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        {
            address: accounts.adminAuthority.address,
            role: 3,
            signer: accounts.adminAuthority,
        },
        { address: accounts.vaultState, role: 1 },
        { address: accounts.baseVaultAuthority, role: 0 },
        { address: accounts.tokenVault, role: 1 },
        { address: accounts.baseTokenMint, role: 0 },
        { address: accounts.sharesMint, role: 1 },
        { address: accounts.adminTokenAccount, role: 1 },
        { address: accounts.systemProgram, role: 0 },
        { address: accounts.rent, role: 0 },
        { address: accounts.tokenProgram, role: 0 },
        { address: accounts.sharesTokenProgram, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=initVault.js.map