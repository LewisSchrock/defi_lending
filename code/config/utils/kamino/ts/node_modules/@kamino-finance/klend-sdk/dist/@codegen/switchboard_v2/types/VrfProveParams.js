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
exports.VrfProveParams = void 0;
const borsh = __importStar(require("@coral-xyz/borsh"));
class VrfProveParams {
    proof;
    idx;
    constructor(fields) {
        this.proof = fields.proof;
        this.idx = fields.idx;
    }
    static layout(property) {
        return borsh.struct([borsh.vecU8("proof"), borsh.u32("idx")], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new VrfProveParams({
            proof: new Uint8Array(obj.proof.buffer, obj.proof.byteOffset, obj.proof.length),
            idx: obj.idx,
        });
    }
    static toEncodable(fields) {
        return {
            proof: Buffer.from(fields.proof.buffer, fields.proof.byteOffset, fields.proof.length),
            idx: fields.idx,
        };
    }
    toJSON() {
        return {
            proof: Array.from(this.proof.values()),
            idx: this.idx,
        };
    }
    static fromJSON(obj) {
        return new VrfProveParams({
            proof: Uint8Array.from(obj.proof),
            idx: obj.idx,
        });
    }
    toEncodable() {
        return VrfProveParams.toEncodable(this);
    }
}
exports.VrfProveParams = VrfProveParams;
//# sourceMappingURL=VrfProveParams.js.map