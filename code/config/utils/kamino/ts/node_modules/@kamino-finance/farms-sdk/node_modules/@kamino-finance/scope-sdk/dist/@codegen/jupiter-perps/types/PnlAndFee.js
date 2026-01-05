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
exports.PnlAndFee = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class PnlAndFee {
    hasProfit;
    pnlDelta;
    openPositionFeeUsd;
    closePositionFeeUsd;
    fundingFeeUsd;
    liquidationPrice;
    constructor(fields) {
        this.hasProfit = fields.hasProfit;
        this.pnlDelta = fields.pnlDelta;
        this.openPositionFeeUsd = fields.openPositionFeeUsd;
        this.closePositionFeeUsd = fields.closePositionFeeUsd;
        this.fundingFeeUsd = fields.fundingFeeUsd;
        this.liquidationPrice = fields.liquidationPrice;
    }
    static layout(property) {
        return borsh.struct([
            borsh.bool("hasProfit"),
            borsh.u64("pnlDelta"),
            borsh.u64("openPositionFeeUsd"),
            borsh.u64("closePositionFeeUsd"),
            borsh.u64("fundingFeeUsd"),
            borsh.u64("liquidationPrice"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new PnlAndFee({
            hasProfit: obj.hasProfit,
            pnlDelta: obj.pnlDelta,
            openPositionFeeUsd: obj.openPositionFeeUsd,
            closePositionFeeUsd: obj.closePositionFeeUsd,
            fundingFeeUsd: obj.fundingFeeUsd,
            liquidationPrice: obj.liquidationPrice,
        });
    }
    static toEncodable(fields) {
        return {
            hasProfit: fields.hasProfit,
            pnlDelta: fields.pnlDelta,
            openPositionFeeUsd: fields.openPositionFeeUsd,
            closePositionFeeUsd: fields.closePositionFeeUsd,
            fundingFeeUsd: fields.fundingFeeUsd,
            liquidationPrice: fields.liquidationPrice,
        };
    }
    toJSON() {
        return {
            hasProfit: this.hasProfit,
            pnlDelta: this.pnlDelta.toString(),
            openPositionFeeUsd: this.openPositionFeeUsd.toString(),
            closePositionFeeUsd: this.closePositionFeeUsd.toString(),
            fundingFeeUsd: this.fundingFeeUsd.toString(),
            liquidationPrice: this.liquidationPrice.toString(),
        };
    }
    static fromJSON(obj) {
        return new PnlAndFee({
            hasProfit: obj.hasProfit,
            pnlDelta: new bn_js_1.default(obj.pnlDelta),
            openPositionFeeUsd: new bn_js_1.default(obj.openPositionFeeUsd),
            closePositionFeeUsd: new bn_js_1.default(obj.closePositionFeeUsd),
            fundingFeeUsd: new bn_js_1.default(obj.fundingFeeUsd),
            liquidationPrice: new bn_js_1.default(obj.liquidationPrice),
        });
    }
    toEncodable() {
        return PnlAndFee.toEncodable(this);
    }
}
exports.PnlAndFee = PnlAndFee;
//# sourceMappingURL=PnlAndFee.js.map