"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseKeypairFile = parseKeypairFile;
exports.noopSigner = noopSigner;
const kit_1 = require("@solana/kit");
async function parseKeypairFile(path) {
    const wallet = Buffer.from(JSON.parse(require('fs').readFileSync(path)));
    return await (0, kit_1.createKeyPairSignerFromBytes)(wallet);
}
function noopSigner(address) {
    const signer = {
        address,
        async signTransactions() {
            // Return an array of empty SignatureDictionary objects — one per transaction
            return [];
        },
    };
    return signer;
}
//# sourceMappingURL=signer.js.map