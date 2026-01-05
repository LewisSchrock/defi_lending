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
exports.BufferRelayerRound = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class BufferRelayerRound {
    numSuccess;
    numError;
    roundOpenSlot;
    roundOpenTimestamp;
    oraclePubkey;
    constructor(fields) {
        this.numSuccess = fields.numSuccess;
        this.numError = fields.numError;
        this.roundOpenSlot = fields.roundOpenSlot;
        this.roundOpenTimestamp = fields.roundOpenTimestamp;
        this.oraclePubkey = fields.oraclePubkey;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u32("numSuccess"),
            borsh.u32("numError"),
            borsh.u64("roundOpenSlot"),
            borsh.i64("roundOpenTimestamp"),
            (0, utils_1.borshAddress)("oraclePubkey"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new BufferRelayerRound({
            numSuccess: obj.numSuccess,
            numError: obj.numError,
            roundOpenSlot: obj.roundOpenSlot,
            roundOpenTimestamp: obj.roundOpenTimestamp,
            oraclePubkey: obj.oraclePubkey,
        });
    }
    static toEncodable(fields) {
        return {
            numSuccess: fields.numSuccess,
            numError: fields.numError,
            roundOpenSlot: fields.roundOpenSlot,
            roundOpenTimestamp: fields.roundOpenTimestamp,
            oraclePubkey: fields.oraclePubkey,
        };
    }
    toJSON() {
        return {
            numSuccess: this.numSuccess,
            numError: this.numError,
            roundOpenSlot: this.roundOpenSlot.toString(),
            roundOpenTimestamp: this.roundOpenTimestamp.toString(),
            oraclePubkey: this.oraclePubkey,
        };
    }
    static fromJSON(obj) {
        return new BufferRelayerRound({
            numSuccess: obj.numSuccess,
            numError: obj.numError,
            roundOpenSlot: new bn_js_1.default(obj.roundOpenSlot),
            roundOpenTimestamp: new bn_js_1.default(obj.roundOpenTimestamp),
            oraclePubkey: (0, kit_1.address)(obj.oraclePubkey),
        });
    }
    toEncodable() {
        return BufferRelayerRound.toEncodable(this);
    }
}
exports.BufferRelayerRound = BufferRelayerRound;
//# sourceMappingURL=BufferRelayerRound.js.map