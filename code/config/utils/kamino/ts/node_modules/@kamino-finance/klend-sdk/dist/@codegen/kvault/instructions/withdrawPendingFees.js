"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.withdrawPendingFees = withdrawPendingFees;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([
    131, 194, 200, 140, 175, 244, 217, 183,
]);
function withdrawPendingFees(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        {
            address: accounts.vaultAdminAuthority.address,
            role: 3,
            signer: accounts.vaultAdminAuthority,
        },
        { address: accounts.vaultState, role: 1 },
        { address: accounts.reserve, role: 1 },
        { address: accounts.tokenVault, role: 1 },
        { address: accounts.ctokenVault, role: 1 },
        { address: accounts.baseVaultAuthority, role: 1 },
        { address: accounts.tokenAta, role: 1 },
        { address: accounts.tokenMint, role: 1 },
        { address: accounts.lendingMarket, role: 0 },
        { address: accounts.lendingMarketAuthority, role: 0 },
        { address: accounts.reserveLiquiditySupply, role: 1 },
        { address: accounts.reserveCollateralMint, role: 1 },
        { address: accounts.klendProgram, role: 0 },
        { address: accounts.tokenProgram, role: 0 },
        { address: accounts.reserveCollateralTokenProgram, role: 0 },
        { address: accounts.instructionSysvarAccount, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=withdrawPendingFees.js.map