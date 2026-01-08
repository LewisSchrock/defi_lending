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
exports.AccountMetaZC = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class AccountMetaZC {
    pubkey;
    isSigner;
    isWritable;
    constructor(fields) {
        this.pubkey = fields.pubkey;
        this.isSigner = fields.isSigner;
        this.isWritable = fields.isWritable;
    }
    static layout(property) {
        return borsh.struct([
            (0, utils_1.borshAddress)("pubkey"),
            borsh.bool("isSigner"),
            borsh.bool("isWritable"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new AccountMetaZC({
            pubkey: obj.pubkey,
            isSigner: obj.isSigner,
            isWritable: obj.isWritable,
        });
    }
    static toEncodable(fields) {
        return {
            pubkey: fields.pubkey,
            isSigner: fields.isSigner,
            isWritable: fields.isWritable,
        };
    }
    toJSON() {
        return {
            pubkey: this.pubkey,
            isSigner: this.isSigner,
            isWritable: this.isWritable,
        };
    }
    static fromJSON(obj) {
        return new AccountMetaZC({
            pubkey: (0, kit_1.address)(obj.pubkey),
            isSigner: obj.isSigner,
            isWritable: obj.isWritable,
        });
    }
    toEncodable() {
        return AccountMetaZC.toEncodable(this);
    }
}
exports.AccountMetaZC = AccountMetaZC;
//# sourceMappingURL=AccountMetaZC.js.map