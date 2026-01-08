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
exports.ObligationCollateral = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
/** Obligation collateral state */
class ObligationCollateral {
    /** Reserve collateral is deposited to */
    depositReserve;
    /** Amount of collateral deposited */
    depositedAmount;
    /** Collateral market value in quote currency (scaled fraction) */
    marketValueSf;
    /**
     * Debt amount (lamport) taken against this collateral.
     * (only meaningful if this obligation is part of an elevation group, otherwise 0)
     * This is only indicative of the debt computed on the last refresh obligation.
     * If the obligation have multiple collateral this value is the same for all of them.
     */
    borrowedAmountAgainstThisCollateralInElevationGroup;
    padding;
    constructor(fields) {
        this.depositReserve = fields.depositReserve;
        this.depositedAmount = fields.depositedAmount;
        this.marketValueSf = fields.marketValueSf;
        this.borrowedAmountAgainstThisCollateralInElevationGroup =
            fields.borrowedAmountAgainstThisCollateralInElevationGroup;
        this.padding = fields.padding;
    }
    static layout(property) {
        return borsh.struct([
            (0, utils_1.borshAddress)("depositReserve"),
            borsh.u64("depositedAmount"),
            borsh.u128("marketValueSf"),
            borsh.u64("borrowedAmountAgainstThisCollateralInElevationGroup"),
            borsh.array(borsh.u64(), 9, "padding"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new ObligationCollateral({
            depositReserve: obj.depositReserve,
            depositedAmount: obj.depositedAmount,
            marketValueSf: obj.marketValueSf,
            borrowedAmountAgainstThisCollateralInElevationGroup: obj.borrowedAmountAgainstThisCollateralInElevationGroup,
            padding: obj.padding,
        });
    }
    static toEncodable(fields) {
        return {
            depositReserve: fields.depositReserve,
            depositedAmount: fields.depositedAmount,
            marketValueSf: fields.marketValueSf,
            borrowedAmountAgainstThisCollateralInElevationGroup: fields.borrowedAmountAgainstThisCollateralInElevationGroup,
            padding: fields.padding,
        };
    }
    toJSON() {
        return {
            depositReserve: this.depositReserve,
            depositedAmount: this.depositedAmount.toString(),
            marketValueSf: this.marketValueSf.toString(),
            borrowedAmountAgainstThisCollateralInElevationGroup: this.borrowedAmountAgainstThisCollateralInElevationGroup.toString(),
            padding: this.padding.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new ObligationCollateral({
            depositReserve: (0, kit_1.address)(obj.depositReserve),
            depositedAmount: new bn_js_1.default(obj.depositedAmount),
            marketValueSf: new bn_js_1.default(obj.marketValueSf),
            borrowedAmountAgainstThisCollateralInElevationGroup: new bn_js_1.default(obj.borrowedAmountAgainstThisCollateralInElevationGroup),
            padding: obj.padding.map((item) => new bn_js_1.default(item)),
        });
    }
    toEncodable() {
        return ObligationCollateral.toEncodable(this);
    }
}
exports.ObligationCollateral = ObligationCollateral;
//# sourceMappingURL=ObligationCollateral.js.map