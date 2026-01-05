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
exports.IncreasePositionInfo = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class IncreasePositionInfo {
    price;
    liquidationPrice;
    feeUsd;
    collateralUsd;
    constructor(fields) {
        this.price = fields.price;
        this.liquidationPrice = fields.liquidationPrice;
        this.feeUsd = fields.feeUsd;
        this.collateralUsd = fields.collateralUsd;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("price"),
            borsh.u64("liquidationPrice"),
            borsh.u64("feeUsd"),
            borsh.u64("collateralUsd"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new IncreasePositionInfo({
            price: obj.price,
            liquidationPrice: obj.liquidationPrice,
            feeUsd: obj.feeUsd,
            collateralUsd: obj.collateralUsd,
        });
    }
    static toEncodable(fields) {
        return {
            price: fields.price,
            liquidationPrice: fields.liquidationPrice,
            feeUsd: fields.feeUsd,
            collateralUsd: fields.collateralUsd,
        };
    }
    toJSON() {
        return {
            price: this.price.toString(),
            liquidationPrice: this.liquidationPrice.toString(),
            feeUsd: this.feeUsd.toString(),
            collateralUsd: this.collateralUsd.toString(),
        };
    }
    static fromJSON(obj) {
        return new IncreasePositionInfo({
            price: new bn_js_1.default(obj.price),
            liquidationPrice: new bn_js_1.default(obj.liquidationPrice),
            feeUsd: new bn_js_1.default(obj.feeUsd),
            collateralUsd: new bn_js_1.default(obj.collateralUsd),
        });
    }
    toEncodable() {
        return IncreasePositionInfo.toEncodable(this);
    }
}
exports.IncreasePositionInfo = IncreasePositionInfo;
//# sourceMappingURL=IncreasePositionInfo.js.map