"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.deleteReferrerStateAndShortUrl = deleteReferrerStateAndShortUrl;
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([153, 185, 99, 28, 228, 179, 187, 150]);
function deleteReferrerStateAndShortUrl(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.referrer.address, role: 3, signer: accounts.referrer },
        { address: accounts.referrerState, role: 1 },
        { address: accounts.shortUrl, role: 1 },
        { address: accounts.rent, role: 0 },
        { address: accounts.systemProgram, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=deleteReferrerStateAndShortUrl.js.map