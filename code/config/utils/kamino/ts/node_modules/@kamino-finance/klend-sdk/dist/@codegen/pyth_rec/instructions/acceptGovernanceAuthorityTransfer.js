"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.acceptGovernanceAuthorityTransfer = acceptGovernanceAuthorityTransfer;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([254, 39, 222, 79, 64, 217, 205, 127]);
function acceptGovernanceAuthorityTransfer(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.payer.address, role: 2, signer: accounts.payer },
        { address: accounts.config, role: 1 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=acceptGovernanceAuthorityTransfer.js.map