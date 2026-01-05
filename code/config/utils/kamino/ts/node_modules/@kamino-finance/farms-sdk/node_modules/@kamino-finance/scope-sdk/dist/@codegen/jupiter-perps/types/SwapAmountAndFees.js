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
exports.SwapAmountAndFees = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class SwapAmountAndFees {
    amountIn;
    amountOut;
    feeBps;
    feeToken;
    constructor(fields) {
        this.amountIn = fields.amountIn;
        this.amountOut = fields.amountOut;
        this.feeBps = fields.feeBps;
        this.feeToken = fields.feeToken;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("amountIn"),
            borsh.u64("amountOut"),
            borsh.u64("feeBps"),
            borsh.u64("feeToken"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new SwapAmountAndFees({
            amountIn: obj.amountIn,
            amountOut: obj.amountOut,
            feeBps: obj.feeBps,
            feeToken: obj.feeToken,
        });
    }
    static toEncodable(fields) {
        return {
            amountIn: fields.amountIn,
            amountOut: fields.amountOut,
            feeBps: fields.feeBps,
            feeToken: fields.feeToken,
        };
    }
    toJSON() {
        return {
            amountIn: this.amountIn.toString(),
            amountOut: this.amountOut.toString(),
            feeBps: this.feeBps.toString(),
            feeToken: this.feeToken.toString(),
        };
    }
    static fromJSON(obj) {
        return new SwapAmountAndFees({
            amountIn: new bn_js_1.default(obj.amountIn),
            amountOut: new bn_js_1.default(obj.amountOut),
            feeBps: new bn_js_1.default(obj.feeBps),
            feeToken: new bn_js_1.default(obj.feeToken),
        });
    }
    toEncodable() {
        return SwapAmountAndFees.toEncodable(this);
    }
}
exports.SwapAmountAndFees = SwapAmountAndFees;
//# sourceMappingURL=SwapAmountAndFees.js.map