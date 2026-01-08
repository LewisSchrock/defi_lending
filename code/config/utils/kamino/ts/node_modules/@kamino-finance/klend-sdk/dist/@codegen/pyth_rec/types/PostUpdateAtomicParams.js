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
exports.PostUpdateAtomicParams = void 0;
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class PostUpdateAtomicParams {
    vaa;
    merklePriceUpdate;
    treasuryId;
    constructor(fields) {
        this.vaa = fields.vaa;
        this.merklePriceUpdate = new types.MerklePriceUpdate({
            ...fields.merklePriceUpdate,
        });
        this.treasuryId = fields.treasuryId;
    }
    static layout(property) {
        return borsh.struct([
            borsh.vecU8("vaa"),
            types.MerklePriceUpdate.layout("merklePriceUpdate"),
            borsh.u8("treasuryId"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new PostUpdateAtomicParams({
            vaa: new Uint8Array(obj.vaa.buffer, obj.vaa.byteOffset, obj.vaa.length),
            merklePriceUpdate: types.MerklePriceUpdate.fromDecoded(obj.merklePriceUpdate),
            treasuryId: obj.treasuryId,
        });
    }
    static toEncodable(fields) {
        return {
            vaa: Buffer.from(fields.vaa.buffer, fields.vaa.byteOffset, fields.vaa.length),
            merklePriceUpdate: types.MerklePriceUpdate.toEncodable(fields.merklePriceUpdate),
            treasuryId: fields.treasuryId,
        };
    }
    toJSON() {
        return {
            vaa: Array.from(this.vaa.values()),
            merklePriceUpdate: this.merklePriceUpdate.toJSON(),
            treasuryId: this.treasuryId,
        };
    }
    static fromJSON(obj) {
        return new PostUpdateAtomicParams({
            vaa: Uint8Array.from(obj.vaa),
            merklePriceUpdate: types.MerklePriceUpdate.fromJSON(obj.merklePriceUpdate),
            treasuryId: obj.treasuryId,
        });
    }
    toEncodable() {
        return PostUpdateAtomicParams.toEncodable(this);
    }
}
exports.PostUpdateAtomicParams = PostUpdateAtomicParams;
//# sourceMappingURL=PostUpdateAtomicParams.js.map