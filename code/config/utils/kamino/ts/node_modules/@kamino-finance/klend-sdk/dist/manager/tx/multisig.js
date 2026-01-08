"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.printMultisigTx = printMultisigTx;
const kit_1 = require("@solana/kit");
const simulate_1 = require("./simulate");
const priorityFee_1 = require("./priorityFee");
const base58Decoder = (0, kit_1.getBase58Decoder)();
async function printMultisigTx(payer, ixs, luts = []) {
    const lutsByAddress = {};
    if (luts.length > 0) {
        for (const acc of luts) {
            lutsByAddress[acc.address] = acc.data.addresses;
        }
    }
    const ixsWithoutBudgetAndAtas = (0, priorityFee_1.removeComputeBudgetProgramInstructions)(ixs);
    const transactionMessage = (0, kit_1.pipe)((0, kit_1.createTransactionMessage)({ version: 'legacy' }), (tx) => (0, kit_1.setTransactionMessageFeePayer)(payer.address, tx), (tx) => (0, kit_1.appendTransactionMessageInstructions)(ixsWithoutBudgetAndAtas, tx), (tx) => (0, kit_1.setTransactionMessageLifetimeUsingBlockhash)(simulate_1.INVALID_BUT_SUFFICIENT_FOR_COMPILATION_BLOCKHASH, tx));
    const compiled = (0, kit_1.compileTransactionMessage)(transactionMessage);
    const encodedMessageBytes = (0, kit_1.getCompiledTransactionMessageEncoder)().encode(compiled);
    const base58EncodedMessage = base58Decoder.decode(encodedMessageBytes);
    console.log('Base58 encoded tx:', base58EncodedMessage);
}
//# sourceMappingURL=multisig.js.map