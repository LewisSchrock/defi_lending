"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.extendLookupTableIxs = void 0;
exports.printAddressLookupTable = printAddressLookupTable;
exports.createLookupTableIx = createLookupTableIx;
exports.extendLookupTableChunkIx = extendLookupTableChunkIx;
exports.initLookupTableIx = initLookupTableIx;
exports.deactivateLookupTableIx = deactivateLookupTableIx;
exports.closeLookupTableIx = closeLookupTableIx;
exports.getAccountsInLut = getAccountsInLut;
exports.insertIntoLookupTableIxs = insertIntoLookupTableIxs;
const address_lookup_table_1 = require("@solana-program/address-lookup-table");
const pubkey_1 = require("./pubkey");
const system_1 = require("@solana-program/system");
async function printAddressLookupTable(rpc, lookupTablePk) {
    const lookupTableAccount = (await (0, address_lookup_table_1.fetchAddressLookupTable)(rpc, lookupTablePk)).data;
    if (!lookupTableAccount) {
        console.error('Lookup table is not found');
    }
    console.log(`Lookup table account, ${lookupTablePk.toString()}`);
    lookupTableAccount.addresses.forEach((address, index) => {
        console.log(`Address: ${address.toString()} at index ${index}`);
    });
}
async function createLookupTableIx(connection, authority) {
    const recentSlot = await connection.getSlot({ commitment: 'finalized' }).send();
    return initLookupTableIx(authority, recentSlot);
}
function extendLookupTableChunkIx(authority, lookupTablePk, keys, payer = authority) {
    return (0, address_lookup_table_1.getExtendLookupTableInstruction)({
        authority,
        payer,
        address: lookupTablePk,
        addresses: keys,
    });
}
const extendLookupTableIxs = (authority, table, keys, payer = authority) => {
    const chunkSize = 25;
    const extendLookupIxs = [];
    for (let i = 0; i < keys.length; i += chunkSize) {
        const chunk = keys.slice(i, i + chunkSize);
        extendLookupIxs.push(extendLookupTableChunkIx(authority, table, chunk, payer));
    }
    return extendLookupIxs;
};
exports.extendLookupTableIxs = extendLookupTableIxs;
/**
 * This method returns an instruction that creates a lookup table, alongside the pubkey of the lookup table
 * @param authority - the owner of the lookup table
 * @param recentSlot - the current slot
 * @returns - the instruction to create the lookup table and its address
 */
async function initLookupTableIx(authority, recentSlot) {
    const address = await (0, address_lookup_table_1.findAddressLookupTablePda)({ authority: authority.address, recentSlot });
    const createLookupTableIx = (0, address_lookup_table_1.getCreateLookupTableInstruction)({
        authority,
        payer: authority,
        recentSlot,
        address,
    });
    return [createLookupTableIx, address[0]];
}
/**
 * This method retuns an instruction that deactivates a lookup table, which is needed to close it
 * @param authority - the owner of the lookup table
 * @param lookupTable - the lookup table to deactivate
 * @returns - the instruction to deactivate the lookup table
 */
function deactivateLookupTableIx(authority, lookupTable) {
    return (0, address_lookup_table_1.getDeactivateLookupTableInstruction)({
        authority,
        address: lookupTable,
    });
}
/**
 * This method returns an instruction that closes a lookup table. That lookup table needs to be disabled at least 500 blocks before closing it.
 * @param authority - the owner of the lookup table
 * @param lookupTable - the lookup table to close
 * @returns - the instruction to close the lookup table
 */
/// this require the LUT to be deactivated at least 500 blocks before
function closeLookupTableIx(authority, lookupTable) {
    return (0, address_lookup_table_1.getCloseLookupTableInstruction)({
        authority,
        address: lookupTable,
        recipient: authority.address,
    });
}
/**
 * Returns the accounts in a lookup table
 * @param rpc
 * @param lookupTable - lookup table to get the accounts from
 * @returns - an array of accounts in the lookup table or an empty array if the lookup table does not exist
 */
async function getAccountsInLut(rpc, lookupTable) {
    try {
        const lutState = await (0, address_lookup_table_1.fetchAddressLookupTable)(rpc, lookupTable);
        return lutState.data.addresses;
    }
    catch (error) {
        console.error(`Error fetching accounts in lookup table ${lookupTable.toString()}`, error);
        return [];
    }
}
/**
 * This method inserts the missing keys from the provided keys into an existent lookup table
 * @param authority - payer wallet pubkey
 * @param lookupTable - lookup table to insert the keys into
 * @param keys - keys to insert into the lookup table
 * @param [accountsInLut] - the existent accounts in the lookup table. Optional. If provided, the function will not fetch the accounts in the lookup table
 * @returns - an array of instructions to insert the missing keys into the lookup table
 */
async function insertIntoLookupTableIxs(rpc, authority, lookupTable, keys, accountsInLut) {
    let lutContentsList = accountsInLut;
    if (!accountsInLut) {
        lutContentsList = await getAccountsInLut(rpc, lookupTable);
    }
    else {
        lutContentsList = accountsInLut;
    }
    const lutContents = new Set(lutContentsList);
    const missingAccounts = keys.filter((key) => !lutContents.has(key) && key !== pubkey_1.DEFAULT_PUBLIC_KEY);
    // deduplicate missing accounts and remove default accounts and convert it back to an array
    const missingAccountsList = [...new Set(missingAccounts)];
    const chunkSize = 20;
    const ixs = [];
    for (let i = 0; i < missingAccountsList.length; i += chunkSize) {
        const chunk = missingAccountsList.slice(i, i + chunkSize);
        ixs.push((0, address_lookup_table_1.getExtendLookupTableInstruction)({
            payer: authority,
            authority,
            address: lookupTable,
            systemProgram: system_1.SYSTEM_PROGRAM_ADDRESS,
            addresses: chunk,
        }));
    }
    return ixs;
}
//# sourceMappingURL=lookupTable.js.map