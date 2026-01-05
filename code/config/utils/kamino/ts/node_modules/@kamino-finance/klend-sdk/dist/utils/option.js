"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.defaultPubkeyIfNone = defaultPubkeyIfNone;
const kit_1 = require("@solana/kit");
const pubkey_1 = require("./pubkey");
function defaultPubkeyIfNone(address) {
    if ((0, kit_1.isNone)(address)) {
        return pubkey_1.DEFAULT_PUBLIC_KEY;
    }
    return address.value;
}
//# sourceMappingURL=option.js.map