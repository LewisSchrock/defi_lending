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
exports.Fees = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class Fees {
    increasePositionBps;
    decreasePositionBps;
    addRemoveLiquidityBps;
    swapBps;
    taxBps;
    stableSwapBps;
    stableSwapTaxBps;
    liquidationRewardBps;
    protocolShareBps;
    constructor(fields) {
        this.increasePositionBps = fields.increasePositionBps;
        this.decreasePositionBps = fields.decreasePositionBps;
        this.addRemoveLiquidityBps = fields.addRemoveLiquidityBps;
        this.swapBps = fields.swapBps;
        this.taxBps = fields.taxBps;
        this.stableSwapBps = fields.stableSwapBps;
        this.stableSwapTaxBps = fields.stableSwapTaxBps;
        this.liquidationRewardBps = fields.liquidationRewardBps;
        this.protocolShareBps = fields.protocolShareBps;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("increasePositionBps"),
            borsh.u64("decreasePositionBps"),
            borsh.u64("addRemoveLiquidityBps"),
            borsh.u64("swapBps"),
            borsh.u64("taxBps"),
            borsh.u64("stableSwapBps"),
            borsh.u64("stableSwapTaxBps"),
            borsh.u64("liquidationRewardBps"),
            borsh.u64("protocolShareBps"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new Fees({
            increasePositionBps: obj.increasePositionBps,
            decreasePositionBps: obj.decreasePositionBps,
            addRemoveLiquidityBps: obj.addRemoveLiquidityBps,
            swapBps: obj.swapBps,
            taxBps: obj.taxBps,
            stableSwapBps: obj.stableSwapBps,
            stableSwapTaxBps: obj.stableSwapTaxBps,
            liquidationRewardBps: obj.liquidationRewardBps,
            protocolShareBps: obj.protocolShareBps,
        });
    }
    static toEncodable(fields) {
        return {
            increasePositionBps: fields.increasePositionBps,
            decreasePositionBps: fields.decreasePositionBps,
            addRemoveLiquidityBps: fields.addRemoveLiquidityBps,
            swapBps: fields.swapBps,
            taxBps: fields.taxBps,
            stableSwapBps: fields.stableSwapBps,
            stableSwapTaxBps: fields.stableSwapTaxBps,
            liquidationRewardBps: fields.liquidationRewardBps,
            protocolShareBps: fields.protocolShareBps,
        };
    }
    toJSON() {
        return {
            increasePositionBps: this.increasePositionBps.toString(),
            decreasePositionBps: this.decreasePositionBps.toString(),
            addRemoveLiquidityBps: this.addRemoveLiquidityBps.toString(),
            swapBps: this.swapBps.toString(),
            taxBps: this.taxBps.toString(),
            stableSwapBps: this.stableSwapBps.toString(),
            stableSwapTaxBps: this.stableSwapTaxBps.toString(),
            liquidationRewardBps: this.liquidationRewardBps.toString(),
            protocolShareBps: this.protocolShareBps.toString(),
        };
    }
    static fromJSON(obj) {
        return new Fees({
            increasePositionBps: new bn_js_1.default(obj.increasePositionBps),
            decreasePositionBps: new bn_js_1.default(obj.decreasePositionBps),
            addRemoveLiquidityBps: new bn_js_1.default(obj.addRemoveLiquidityBps),
            swapBps: new bn_js_1.default(obj.swapBps),
            taxBps: new bn_js_1.default(obj.taxBps),
            stableSwapBps: new bn_js_1.default(obj.stableSwapBps),
            stableSwapTaxBps: new bn_js_1.default(obj.stableSwapTaxBps),
            liquidationRewardBps: new bn_js_1.default(obj.liquidationRewardBps),
            protocolShareBps: new bn_js_1.default(obj.protocolShareBps),
        });
    }
    toEncodable() {
        return Fees.toEncodable(this);
    }
}
exports.Fees = Fees;
//# sourceMappingURL=Fees.js.map