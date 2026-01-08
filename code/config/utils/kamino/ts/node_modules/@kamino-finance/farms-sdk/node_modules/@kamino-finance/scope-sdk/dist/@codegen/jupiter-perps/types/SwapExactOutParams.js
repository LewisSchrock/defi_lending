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
exports.SwapExactOutParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class SwapExactOutParams {
    amountOut;
    maxAmountIn;
    constructor(fields) {
        this.amountOut = fields.amountOut;
        this.maxAmountIn = fields.maxAmountIn;
    }
    static layout(property) {
        return borsh.struct([borsh.u64("amountOut"), borsh.u64("maxAmountIn")], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new SwapExactOutParams({
            amountOut: obj.amountOut,
            maxAmountIn: obj.maxAmountIn,
        });
    }
    static toEncodable(fields) {
        return {
            amountOut: fields.amountOut,
            maxAmountIn: fields.maxAmountIn,
        };
    }
    toJSON() {
        return {
            amountOut: this.amountOut.toString(),
            maxAmountIn: this.maxAmountIn.toString(),
        };
    }
    static fromJSON(obj) {
        return new SwapExactOutParams({
            amountOut: new bn_js_1.default(obj.amountOut),
            maxAmountIn: new bn_js_1.default(obj.maxAmountIn),
        });
    }
    toEncodable() {
        return SwapExactOutParams.toEncodable(this);
    }
}
exports.SwapExactOutParams = SwapExactOutParams;
//# sourceMappingURL=SwapExactOutParams.js.map