"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getComputeBudgetAndPriorityFeeIxs = void 0;
exports.buildComputeBudgetIx = buildComputeBudgetIx;
exports.getLookupTableAccounts = getLookupTableAccounts;
exports.notEmpty = notEmpty;
exports.uniqueAccountsWithProgramIds = uniqueAccountsWithProgramIds;
exports.removeBudgetIxs = removeBudgetIxs;
const kit_1 = require("@solana/kit");
const kliquidity_sdk_1 = require("@kamino-finance/kliquidity-sdk");
const compute_budget_1 = require("@solana-program/compute-budget");
const address_lookup_table_1 = require("@solana-program/address-lookup-table");
const pubkey_1 = require("./pubkey");
function buildComputeBudgetIx(units) {
    return (0, compute_budget_1.getSetComputeUnitLimitInstruction)({ units });
}
async function getLookupTableAccounts(rpc, addresses) {
    return (0, kliquidity_sdk_1.batchFetch)(addresses, (batch) => (0, address_lookup_table_1.fetchAllAddressLookupTable)(rpc, batch));
}
const getComputeBudgetAndPriorityFeeIxs = (units, priorityFeeLamports) => {
    const ixs = [];
    ixs.push((0, compute_budget_1.getSetComputeUnitLimitInstruction)({ units }));
    if (priorityFeeLamports && priorityFeeLamports.gt(0)) {
        const unitPrice = priorityFeeLamports.mul(10 ** 6).div(units);
        ixs.push((0, compute_budget_1.getSetComputeUnitPriceInstruction)({ microLamports: BigInt(unitPrice.floor().toString()) }));
    }
    return ixs;
};
exports.getComputeBudgetAndPriorityFeeIxs = getComputeBudgetAndPriorityFeeIxs;
// filters null values from array and make typescript happy
function notEmpty(value) {
    if (value === null || value === undefined) {
        return false;
    }
    //
    // eslint-disable-next-line no-unused-vars,@typescript-eslint/no-unused-vars
    const testDummy = value;
    return true;
}
function uniqueAccountsWithProgramIds(ixs, addressLookupTables = []) {
    let luts;
    if (addressLookupTables.length > 0 &&
        typeof addressLookupTables[0] === 'string' &&
        (0, kit_1.isAddress)(addressLookupTables[0])) {
        luts = addressLookupTables;
    }
    else {
        luts = addressLookupTables.map((lut) => lut.address);
    }
    const uniqueAccounts = new Set(luts);
    ixs.forEach((ix) => {
        uniqueAccounts.add(ix.programAddress);
        (ix.accounts || []).forEach((key) => {
            uniqueAccounts.add(key.address);
        });
    });
    return [...uniqueAccounts];
}
function removeBudgetIxs(ixs) {
    return ixs.filter(({ programAddress }) => {
        return programAddress !== pubkey_1.COMPUTE_BUDGET_PROGRAM_ID;
    });
}
//# sourceMappingURL=instruction.js.map