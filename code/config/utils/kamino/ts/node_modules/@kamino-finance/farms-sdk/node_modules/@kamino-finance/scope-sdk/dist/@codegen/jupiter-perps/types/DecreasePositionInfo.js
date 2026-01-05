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
exports.DecreasePositionInfo = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class DecreasePositionInfo {
    price;
    liquidationPrice;
    feeUsd;
    collateralUsd;
    hasProfit;
    pnlDelta;
    transferAmountUsd;
    transferToken;
    constructor(fields) {
        this.price = fields.price;
        this.liquidationPrice = fields.liquidationPrice;
        this.feeUsd = fields.feeUsd;
        this.collateralUsd = fields.collateralUsd;
        this.hasProfit = fields.hasProfit;
        this.pnlDelta = fields.pnlDelta;
        this.transferAmountUsd = fields.transferAmountUsd;
        this.transferToken = fields.transferToken;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("price"),
            borsh.u64("liquidationPrice"),
            borsh.u64("feeUsd"),
            borsh.u64("collateralUsd"),
            borsh.bool("hasProfit"),
            borsh.u64("pnlDelta"),
            borsh.u64("transferAmountUsd"),
            borsh.u64("transferToken"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new DecreasePositionInfo({
            price: obj.price,
            liquidationPrice: obj.liquidationPrice,
            feeUsd: obj.feeUsd,
            collateralUsd: obj.collateralUsd,
            hasProfit: obj.hasProfit,
            pnlDelta: obj.pnlDelta,
            transferAmountUsd: obj.transferAmountUsd,
            transferToken: obj.transferToken,
        });
    }
    static toEncodable(fields) {
        return {
            price: fields.price,
            liquidationPrice: fields.liquidationPrice,
            feeUsd: fields.feeUsd,
            collateralUsd: fields.collateralUsd,
            hasProfit: fields.hasProfit,
            pnlDelta: fields.pnlDelta,
            transferAmountUsd: fields.transferAmountUsd,
            transferToken: fields.transferToken,
        };
    }
    toJSON() {
        return {
            price: this.price.toString(),
            liquidationPrice: this.liquidationPrice.toString(),
            feeUsd: this.feeUsd.toString(),
            collateralUsd: this.collateralUsd.toString(),
            hasProfit: this.hasProfit,
            pnlDelta: this.pnlDelta.toString(),
            transferAmountUsd: this.transferAmountUsd.toString(),
            transferToken: this.transferToken.toString(),
        };
    }
    static fromJSON(obj) {
        return new DecreasePositionInfo({
            price: new bn_js_1.default(obj.price),
            liquidationPrice: new bn_js_1.default(obj.liquidationPrice),
            feeUsd: new bn_js_1.default(obj.feeUsd),
            collateralUsd: new bn_js_1.default(obj.collateralUsd),
            hasProfit: obj.hasProfit,
            pnlDelta: new bn_js_1.default(obj.pnlDelta),
            transferAmountUsd: new bn_js_1.default(obj.transferAmountUsd),
            transferToken: new bn_js_1.default(obj.transferToken),
        });
    }
    toEncodable() {
        return DecreasePositionInfo.toEncodable(this);
    }
}
exports.DecreasePositionInfo = DecreasePositionInfo;
//# sourceMappingURL=DecreasePositionInfo.js.map