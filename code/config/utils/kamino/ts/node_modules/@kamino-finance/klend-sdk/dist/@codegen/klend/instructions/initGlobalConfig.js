"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.initGlobalConfig = initGlobalConfig;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([140, 136, 214, 48, 87, 0, 120, 255]);
function initGlobalConfig(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.payer.address, role: 3, signer: accounts.payer },
        { address: accounts.globalConfig, role: 1 },
        { address: accounts.programData, role: 0 },
        { address: accounts.systemProgram, role: 0 },
        { address: accounts.rent, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=initGlobalConfig.js.map