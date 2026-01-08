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
exports.MerklePriceUpdate = void 0;
const borsh = __importStar(require("@coral-xyz/borsh"));
class MerklePriceUpdate {
    message;
    proof;
    constructor(fields) {
        this.message = fields.message;
        this.proof = fields.proof;
    }
    static layout(property) {
        return borsh.struct([borsh.vecU8("message"), borsh.vec(borsh.array(borsh.u8(), 20), "proof")], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new MerklePriceUpdate({
            message: new Uint8Array(obj.message.buffer, obj.message.byteOffset, obj.message.length),
            proof: obj.proof,
        });
    }
    static toEncodable(fields) {
        return {
            message: Buffer.from(fields.message.buffer, fields.message.byteOffset, fields.message.length),
            proof: fields.proof,
        };
    }
    toJSON() {
        return {
            message: Array.from(this.message.values()),
            proof: this.proof,
        };
    }
    static fromJSON(obj) {
        return new MerklePriceUpdate({
            message: Uint8Array.from(obj.message),
            proof: obj.proof,
        });
    }
    toEncodable() {
        return MerklePriceUpdate.toEncodable(this);
    }
}
exports.MerklePriceUpdate = MerklePriceUpdate;
//# sourceMappingURL=MerklePriceUpdate.js.map