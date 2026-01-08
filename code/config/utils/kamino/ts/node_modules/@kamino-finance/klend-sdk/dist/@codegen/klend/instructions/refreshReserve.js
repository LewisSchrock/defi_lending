"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DISCRIMINATOR = void 0;
exports.refreshReserve = refreshReserve;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([2, 218, 138, 235, 79, 201, 25, 102]);
function refreshReserve(accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.reserve, role: 1 },
        { address: accounts.lendingMarket, role: 0 },
        (0, kit_1.isSome)(accounts.pythOracle)
            ? { address: accounts.pythOracle.value, role: 0 }
            : { address: programAddress, role: 0 },
        (0, kit_1.isSome)(accounts.switchboardPriceOracle)
            ? { address: accounts.switchboardPriceOracle.value, role: 0 }
            : { address: programAddress, role: 0 },
        (0, kit_1.isSome)(accounts.switchboardTwapOracle)
            ? { address: accounts.switchboardTwapOracle.value, role: 0 }
            : { address: programAddress, role: 0 },
        (0, kit_1.isSome)(accounts.scopePrices)
            ? { address: accounts.scopePrices.value, role: 0 }
            : { address: programAddress, role: 0 },
        ...remainingAccounts,
    ];
    const data = exports.DISCRIMINATOR;
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=refreshReserve.js.map