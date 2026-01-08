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
exports.SlidingWindowElement = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class SlidingWindowElement {
    oracleKey;
    value;
    slot;
    timestamp;
    constructor(fields) {
        this.oracleKey = fields.oracleKey;
        this.value = new types.SwitchboardDecimal({ ...fields.value });
        this.slot = fields.slot;
        this.timestamp = fields.timestamp;
    }
    static layout(property) {
        return borsh.struct([
            (0, utils_1.borshAddress)("oracleKey"),
            types.SwitchboardDecimal.layout("value"),
            borsh.u64("slot"),
            borsh.i64("timestamp"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new SlidingWindowElement({
            oracleKey: obj.oracleKey,
            value: types.SwitchboardDecimal.fromDecoded(obj.value),
            slot: obj.slot,
            timestamp: obj.timestamp,
        });
    }
    static toEncodable(fields) {
        return {
            oracleKey: fields.oracleKey,
            value: types.SwitchboardDecimal.toEncodable(fields.value),
            slot: fields.slot,
            timestamp: fields.timestamp,
        };
    }
    toJSON() {
        return {
            oracleKey: this.oracleKey,
            value: this.value.toJSON(),
            slot: this.slot.toString(),
            timestamp: this.timestamp.toString(),
        };
    }
    static fromJSON(obj) {
        return new SlidingWindowElement({
            oracleKey: (0, kit_1.address)(obj.oracleKey),
            value: types.SwitchboardDecimal.fromJSON(obj.value),
            slot: new bn_js_1.default(obj.slot),
            timestamp: new bn_js_1.default(obj.timestamp),
        });
    }
    toEncodable() {
        return SlidingWindowElement.toEncodable(this);
    }
}
exports.SlidingWindowElement = SlidingWindowElement;
//# sourceMappingURL=SlidingWindowElement.js.map