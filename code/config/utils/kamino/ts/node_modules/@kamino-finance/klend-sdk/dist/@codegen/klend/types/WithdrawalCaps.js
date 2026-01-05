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
exports.WithdrawalCaps = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
/** Reserve Withdrawal Caps State */
class WithdrawalCaps {
    configCapacity;
    currentTotal;
    lastIntervalStartTimestamp;
    configIntervalLengthSeconds;
    constructor(fields) {
        this.configCapacity = fields.configCapacity;
        this.currentTotal = fields.currentTotal;
        this.lastIntervalStartTimestamp = fields.lastIntervalStartTimestamp;
        this.configIntervalLengthSeconds = fields.configIntervalLengthSeconds;
    }
    static layout(property) {
        return borsh.struct([
            borsh.i64("configCapacity"),
            borsh.i64("currentTotal"),
            borsh.u64("lastIntervalStartTimestamp"),
            borsh.u64("configIntervalLengthSeconds"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new WithdrawalCaps({
            configCapacity: obj.configCapacity,
            currentTotal: obj.currentTotal,
            lastIntervalStartTimestamp: obj.lastIntervalStartTimestamp,
            configIntervalLengthSeconds: obj.configIntervalLengthSeconds,
        });
    }
    static toEncodable(fields) {
        return {
            configCapacity: fields.configCapacity,
            currentTotal: fields.currentTotal,
            lastIntervalStartTimestamp: fields.lastIntervalStartTimestamp,
            configIntervalLengthSeconds: fields.configIntervalLengthSeconds,
        };
    }
    toJSON() {
        return {
            configCapacity: this.configCapacity.toString(),
            currentTotal: this.currentTotal.toString(),
            lastIntervalStartTimestamp: this.lastIntervalStartTimestamp.toString(),
            configIntervalLengthSeconds: this.configIntervalLengthSeconds.toString(),
        };
    }
    static fromJSON(obj) {
        return new WithdrawalCaps({
            configCapacity: new bn_js_1.default(obj.configCapacity),
            currentTotal: new bn_js_1.default(obj.currentTotal),
            lastIntervalStartTimestamp: new bn_js_1.default(obj.lastIntervalStartTimestamp),
            configIntervalLengthSeconds: new bn_js_1.default(obj.configIntervalLengthSeconds),
        });
    }
    toEncodable() {
        return WithdrawalCaps.toEncodable(this);
    }
}
exports.WithdrawalCaps = WithdrawalCaps;
//# sourceMappingURL=WithdrawalCaps.js.map