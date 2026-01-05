"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getProgramAccounts = getProgramAccounts;
exports.getAccountOwner = getAccountOwner;
const kit_1 = require("@solana/kit");
const buffer_1 = require("buffer");
const zstddec_1 = require("zstddec");
const decoder = new zstddec_1.ZSTDDecoder();
(async () => {
    await decoder.init();
})();
/**
 * Uses zstd compression when fetching all accounts owned by a program for a smaller response size
 * Uses axios instead of node-fetch to work around a bug in node-fetch that causes subsequent requests with different encoding to fail
 * @param rpc
 * @param programId
 * @param structSize - the size of the decompressed account data struct
 * @param filters
 * @param dataSlice
 */
async function getProgramAccounts(rpc, programId, structSize, filters, dataSlice) {
    const res = await rpc
        .getProgramAccounts(programId, {
        encoding: 'base64+zstd',
        filters,
        dataSlice,
    })
        .send();
    const deser = res.map(async (account) => await deserializeAccountInfo(account, structSize));
    const x = await Promise.all(deser);
    return x;
}
async function getAccountOwner(rpc, address) {
    const acc = await (0, kit_1.fetchEncodedAccount)(rpc, address);
    if (!acc.exists) {
        throw Error(`Could not fetch mint ${address.toString()}`);
    }
    return acc.programAddress;
}
async function deserializeAccountInfo(accountInfo, size) {
    const data = decoder.decode(buffer_1.Buffer.from(accountInfo.account.data[0], 'base64'), size);
    return {
        programAddress: accountInfo.account.owner,
        lamports: accountInfo.account.lamports,
        executable: accountInfo.account.executable,
        space: accountInfo.account.space,
        address: accountInfo.pubkey,
        data: buffer_1.Buffer.from(data),
    };
}
//# sourceMappingURL=rpc.js.map