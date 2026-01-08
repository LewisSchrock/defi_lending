"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.layout = exports.DISCRIMINATOR = void 0;
exports.initReferrerStateAndShortUrl = initReferrerStateAndShortUrl;
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
exports.DISCRIMINATOR = Buffer.from([165, 19, 25, 127, 100, 55, 31, 90]);
exports.layout = borsh.struct([
    borsh.str("shortUrl"),
]);
function initReferrerStateAndShortUrl(args, accounts, remainingAccounts = [], programAddress = programId_1.PROGRAM_ID) {
    const keys = [
        { address: accounts.referrer.address, role: 3, signer: accounts.referrer },
        { address: accounts.referrerState, role: 1 },
        { address: accounts.referrerShortUrl, role: 1 },
        { address: accounts.referrerUserMetadata, role: 0 },
        { address: accounts.rent, role: 0 },
        { address: accounts.systemProgram, role: 0 },
        ...remainingAccounts,
    ];
    const buffer = Buffer.alloc(1000);
    const len = exports.layout.encode({
        shortUrl: args.shortUrl,
    }, buffer);
    const data = Buffer.concat([exports.DISCRIMINATOR, buffer]).slice(0, 8 + len);
    const ix = { accounts: keys, programAddress, data };
    return ix;
}
//# sourceMappingURL=initReferrerStateAndShortUrl.js.map