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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.VrfProveAndVerifyParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class VrfProveAndVerifyParams {
    nonce;
    stateBump;
    idx;
    proof;
    proofEncoded;
    counter;
    constructor(fields) {
        this.nonce = fields.nonce;
        this.stateBump = fields.stateBump;
        this.idx = fields.idx;
        this.proof = fields.proof;
        this.proofEncoded = fields.proofEncoded;
        this.counter = fields.counter;
    }
    static layout(property) {
        return borsh.struct([
            borsh.option(borsh.u32(), "nonce"),
            borsh.u8("stateBump"),
            borsh.u32("idx"),
            borsh.vecU8("proof"),
            borsh.str("proofEncoded"),
            borsh.u128("counter"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new VrfProveAndVerifyParams({
            nonce: obj.nonce,
            stateBump: obj.stateBump,
            idx: obj.idx,
            proof: new Uint8Array(obj.proof.buffer, obj.proof.byteOffset, obj.proof.length),
            proofEncoded: obj.proofEncoded,
            counter: obj.counter,
        });
    }
    static toEncodable(fields) {
        return {
            nonce: fields.nonce,
            stateBump: fields.stateBump,
            idx: fields.idx,
            proof: Buffer.from(fields.proof.buffer, fields.proof.byteOffset, fields.proof.length),
            proofEncoded: fields.proofEncoded,
            counter: fields.counter,
        };
    }
    toJSON() {
        return {
            nonce: this.nonce,
            stateBump: this.stateBump,
            idx: this.idx,
            proof: Array.from(this.proof.values()),
            proofEncoded: this.proofEncoded,
            counter: this.counter.toString(),
        };
    }
    static fromJSON(obj) {
        return new VrfProveAndVerifyParams({
            nonce: obj.nonce,
            stateBump: obj.stateBump,
            idx: obj.idx,
            proof: Uint8Array.from(obj.proof),
            proofEncoded: obj.proofEncoded,
            counter: new bn_js_1.default(obj.counter),
        });
    }
    toEncodable() {
        return VrfProveAndVerifyParams.toEncodable(this);
    }
}
exports.VrfProveAndVerifyParams = VrfProveAndVerifyParams;
//# sourceMappingURL=VrfProveAndVerifyParams.js.map