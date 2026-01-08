"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.getOraclePrice = getOraclePrice;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([200, 20, 0, 106, 56, 210, 230, 140]);
function getOraclePrice(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.perpetuals, role: 0 },
        { address: accounts.pool, role: 0 },
        { address: accounts.custody, role: 0 },
        { address: accounts.custodyOracleAccount, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=getOraclePrice.js.map