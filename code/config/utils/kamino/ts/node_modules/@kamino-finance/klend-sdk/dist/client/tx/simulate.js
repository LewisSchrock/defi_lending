"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.INVALID_BUT_SUFFICIENT_FOR_COMPILATION_BLOCKHASH = void 0;
exports.printSimulateTx = printSimulateTx;
const kit_1 = require("@solana/kit");
exports.INVALID_BUT_SUFFICIENT_FOR_COMPILATION_BLOCKHASH = {
    blockhash: '11111111111111111111111111111111',
    lastValidBlockHeight: 0n,
    slot: 0n,
};
async function printSimulateTx(c, payer, ixs, luts = []) {
    const lutsByAddress = {};
    if (luts.length > 0) {
        for (const acc of luts) {
            lutsByAddress[acc.address] = acc.data.addresses;
        }
    }
    const transactionMessage = (0, kit_1.pipe)((0, kit_1.createTransactionMessage)({ version: 0 }), (tx) => (0, kit_1.setTransactionMessageFeePayer)(payer.address, tx), (tx) => (0, kit_1.appendTransactionMessageInstructions)(ixs, tx), (tx) => (0, kit_1.compressTransactionMessageUsingAddressLookupTables)(tx, lutsByAddress), (tx) => (0, kit_1.setTransactionMessageLifetimeUsingBlockhash)(exports.INVALID_BUT_SUFFICIENT_FOR_COMPILATION_BLOCKHASH, tx));
    const compiledTransaction = (0, kit_1.compileTransaction)(transactionMessage);
    const wireTransactionBytes = (0, kit_1.getBase64EncodedWireTransaction)(compiledTransaction);
    const compiled = (0, kit_1.compileTransactionMessage)(transactionMessage);
    const encodedMessageBytes = (0, kit_1.getCompiledTransactionMessageEncoder)().encode(compiled);
    const encodedTxMessage = Buffer.from(encodedMessageBytes).toString('base64');
    const simulationUrl = `https://explorer.solana.com/tx/inspector?message=${encodeURIComponent(encodedTxMessage)}&signatures=${encodeURIComponent(`[${payer.address}]`)}`;
    console.log('Simulation URL:', simulationUrl);
    const res = await c.rpc
        .simulateTransaction(wireTransactionBytes, {
        encoding: 'base64',
        replaceRecentBlockhash: true,
        sigVerify: false,
    })
        .send();
    console.log('Simulate Response:', res);
    console.log('');
}
//# sourceMappingURL=simulate.js.map