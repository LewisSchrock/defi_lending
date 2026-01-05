"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.COMPUTE_BUDGET_PROGRAM_ID = exports.NULL_PUBKEY = exports.WRAPPED_SOL_MINT = exports.DEFAULT_PUBLIC_KEY = void 0;
exports.isNotNullPubkey = isNotNullPubkey;
const kit_1 = require("@solana/kit");
exports.DEFAULT_PUBLIC_KEY = (0, kit_1.address)('11111111111111111111111111111111');
exports.WRAPPED_SOL_MINT = (0, kit_1.address)('So11111111111111111111111111111111111111112');
exports.NULL_PUBKEY = (0, kit_1.address)('nu11111111111111111111111111111111111111111');
exports.COMPUTE_BUDGET_PROGRAM_ID = (0, kit_1.address)('ComputeBudget111111111111111111111111111111');
/**
 * Helper function to check if a configured pubkey is null or default.
 * @param pubkey
 * @returns {boolean}
 */
function isNotNullPubkey(pubkey) {
    return pubkey && pubkey !== exports.NULL_PUBKEY && pubkey !== exports.DEFAULT_PUBLIC_KEY;
}
//# sourceMappingURL=pubkey.js.map