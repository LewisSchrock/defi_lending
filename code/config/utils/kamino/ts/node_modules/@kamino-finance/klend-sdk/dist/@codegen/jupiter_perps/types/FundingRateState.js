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
exports.FundingRateState = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class FundingRateState {
    cumulativeInterestRate;
    lastUpdate;
    hourlyFundingBps;
    constructor(fields) {
        this.cumulativeInterestRate = fields.cumulativeInterestRate;
        this.lastUpdate = fields.lastUpdate;
        this.hourlyFundingBps = fields.hourlyFundingBps;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u128("cumulativeInterestRate"),
            borsh.i64("lastUpdate"),
            borsh.u64("hourlyFundingBps"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new FundingRateState({
            cumulativeInterestRate: obj.cumulativeInterestRate,
            lastUpdate: obj.lastUpdate,
            hourlyFundingBps: obj.hourlyFundingBps,
        });
    }
    static toEncodable(fields) {
        return {
            cumulativeInterestRate: fields.cumulativeInterestRate,
            lastUpdate: fields.lastUpdate,
            hourlyFundingBps: fields.hourlyFundingBps,
        };
    }
    toJSON() {
        return {
            cumulativeInterestRate: this.cumulativeInterestRate.toString(),
            lastUpdate: this.lastUpdate.toString(),
            hourlyFundingBps: this.hourlyFundingBps.toString(),
        };
    }
    static fromJSON(obj) {
        return new FundingRateState({
            cumulativeInterestRate: new bn_js_1.default(obj.cumulativeInterestRate),
            lastUpdate: new bn_js_1.default(obj.lastUpdate),
            hourlyFundingBps: new bn_js_1.default(obj.hourlyFundingBps),
        });
    }
    toEncodable() {
        return FundingRateState.toEncodable(this);
    }
}
exports.FundingRateState = FundingRateState;
//# sourceMappingURL=FundingRateState.js.map