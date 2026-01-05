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
exports.LastUpdate = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
/** Last update state */
class LastUpdate {
    /** Last slot when updated */
    slot;
    /** True when marked stale, false when slot updated */
    stale;
    /** Status of the prices used to calculate the last update */
    priceStatus;
    placeholder;
    constructor(fields) {
        this.slot = fields.slot;
        this.stale = fields.stale;
        this.priceStatus = fields.priceStatus;
        this.placeholder = fields.placeholder;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("slot"),
            borsh.u8("stale"),
            borsh.u8("priceStatus"),
            borsh.array(borsh.u8(), 6, "placeholder"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new LastUpdate({
            slot: obj.slot,
            stale: obj.stale,
            priceStatus: obj.priceStatus,
            placeholder: obj.placeholder,
        });
    }
    static toEncodable(fields) {
        return {
            slot: fields.slot,
            stale: fields.stale,
            priceStatus: fields.priceStatus,
            placeholder: fields.placeholder,
        };
    }
    toJSON() {
        return {
            slot: this.slot.toString(),
            stale: this.stale,
            priceStatus: this.priceStatus,
            placeholder: this.placeholder,
        };
    }
    static fromJSON(obj) {
        return new LastUpdate({
            slot: new bn_js_1.default(obj.slot),
            stale: obj.stale,
            priceStatus: obj.priceStatus,
            placeholder: obj.placeholder,
        });
    }
    toEncodable() {
        return LastUpdate.toEncodable(this);
    }
}
exports.LastUpdate = LastUpdate;
//# sourceMappingURL=LastUpdate.js.map