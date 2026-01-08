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
exports.ReserveLiquidity = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
/** Reserve liquidity */
class ReserveLiquidity {
    /** Reserve liquidity mint address */
    mintPubkey;
    /** Reserve liquidity supply address */
    supplyVault;
    /** Reserve liquidity fee collection address */
    feeVault;
    /** Reserve liquidity available */
    availableAmount;
    /** Reserve liquidity borrowed (scaled fraction) */
    borrowedAmountSf;
    /** Reserve liquidity market price in quote currency (scaled fraction) */
    marketPriceSf;
    /** Unix timestamp of the market price (from the oracle) */
    marketPriceLastUpdatedTs;
    /** Reserve liquidity mint decimals */
    mintDecimals;
    /**
     * Timestamp when the last refresh reserve detected that the liquidity amount is above the deposit cap. When this threshold is crossed, then redemptions (auto-deleverage) are enabled.
     * If the threshold is not crossed, then the timestamp is set to 0
     */
    depositLimitCrossedTimestamp;
    /**
     * Timestamp when the last refresh reserve detected that the borrowed amount is above the borrow cap. When this threshold is crossed, then redemptions (auto-deleverage) are enabled.
     * If the threshold is not crossed, then the timestamp is set to 0
     */
    borrowLimitCrossedTimestamp;
    /** Reserve liquidity cumulative borrow rate (scaled fraction) */
    cumulativeBorrowRateBsf;
    /** Reserve cumulative protocol fees (scaled fraction) */
    accumulatedProtocolFeesSf;
    /** Reserve cumulative referrer fees (scaled fraction) */
    accumulatedReferrerFeesSf;
    /** Reserve pending referrer fees, to be claimed in refresh_obligation by referrer or protocol (scaled fraction) */
    pendingReferrerFeesSf;
    /** Reserve referrer fee absolute rate calculated at each refresh_reserve operation (scaled fraction) */
    absoluteReferralRateSf;
    /** Token program of the liquidity mint */
    tokenProgram;
    padding2;
    padding3;
    constructor(fields) {
        this.mintPubkey = fields.mintPubkey;
        this.supplyVault = fields.supplyVault;
        this.feeVault = fields.feeVault;
        this.availableAmount = fields.availableAmount;
        this.borrowedAmountSf = fields.borrowedAmountSf;
        this.marketPriceSf = fields.marketPriceSf;
        this.marketPriceLastUpdatedTs = fields.marketPriceLastUpdatedTs;
        this.mintDecimals = fields.mintDecimals;
        this.depositLimitCrossedTimestamp = fields.depositLimitCrossedTimestamp;
        this.borrowLimitCrossedTimestamp = fields.borrowLimitCrossedTimestamp;
        this.cumulativeBorrowRateBsf = new types.BigFractionBytes({
            ...fields.cumulativeBorrowRateBsf,
        });
        this.accumulatedProtocolFeesSf = fields.accumulatedProtocolFeesSf;
        this.accumulatedReferrerFeesSf = fields.accumulatedReferrerFeesSf;
        this.pendingReferrerFeesSf = fields.pendingReferrerFeesSf;
        this.absoluteReferralRateSf = fields.absoluteReferralRateSf;
        this.tokenProgram = fields.tokenProgram;
        this.padding2 = fields.padding2;
        this.padding3 = fields.padding3;
    }
    static layout(property) {
        return borsh.struct([
            (0, utils_1.borshAddress)("mintPubkey"),
            (0, utils_1.borshAddress)("supplyVault"),
            (0, utils_1.borshAddress)("feeVault"),
            borsh.u64("availableAmount"),
            borsh.u128("borrowedAmountSf"),
            borsh.u128("marketPriceSf"),
            borsh.u64("marketPriceLastUpdatedTs"),
            borsh.u64("mintDecimals"),
            borsh.u64("depositLimitCrossedTimestamp"),
            borsh.u64("borrowLimitCrossedTimestamp"),
            types.BigFractionBytes.layout("cumulativeBorrowRateBsf"),
            borsh.u128("accumulatedProtocolFeesSf"),
            borsh.u128("accumulatedReferrerFeesSf"),
            borsh.u128("pendingReferrerFeesSf"),
            borsh.u128("absoluteReferralRateSf"),
            (0, utils_1.borshAddress)("tokenProgram"),
            borsh.array(borsh.u64(), 51, "padding2"),
            borsh.array(borsh.u128(), 32, "padding3"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new ReserveLiquidity({
            mintPubkey: obj.mintPubkey,
            supplyVault: obj.supplyVault,
            feeVault: obj.feeVault,
            availableAmount: obj.availableAmount,
            borrowedAmountSf: obj.borrowedAmountSf,
            marketPriceSf: obj.marketPriceSf,
            marketPriceLastUpdatedTs: obj.marketPriceLastUpdatedTs,
            mintDecimals: obj.mintDecimals,
            depositLimitCrossedTimestamp: obj.depositLimitCrossedTimestamp,
            borrowLimitCrossedTimestamp: obj.borrowLimitCrossedTimestamp,
            cumulativeBorrowRateBsf: types.BigFractionBytes.fromDecoded(obj.cumulativeBorrowRateBsf),
            accumulatedProtocolFeesSf: obj.accumulatedProtocolFeesSf,
            accumulatedReferrerFeesSf: obj.accumulatedReferrerFeesSf,
            pendingReferrerFeesSf: obj.pendingReferrerFeesSf,
            absoluteReferralRateSf: obj.absoluteReferralRateSf,
            tokenProgram: obj.tokenProgram,
            padding2: obj.padding2,
            padding3: obj.padding3,
        });
    }
    static toEncodable(fields) {
        return {
            mintPubkey: fields.mintPubkey,
            supplyVault: fields.supplyVault,
            feeVault: fields.feeVault,
            availableAmount: fields.availableAmount,
            borrowedAmountSf: fields.borrowedAmountSf,
            marketPriceSf: fields.marketPriceSf,
            marketPriceLastUpdatedTs: fields.marketPriceLastUpdatedTs,
            mintDecimals: fields.mintDecimals,
            depositLimitCrossedTimestamp: fields.depositLimitCrossedTimestamp,
            borrowLimitCrossedTimestamp: fields.borrowLimitCrossedTimestamp,
            cumulativeBorrowRateBsf: types.BigFractionBytes.toEncodable(fields.cumulativeBorrowRateBsf),
            accumulatedProtocolFeesSf: fields.accumulatedProtocolFeesSf,
            accumulatedReferrerFeesSf: fields.accumulatedReferrerFeesSf,
            pendingReferrerFeesSf: fields.pendingReferrerFeesSf,
            absoluteReferralRateSf: fields.absoluteReferralRateSf,
            tokenProgram: fields.tokenProgram,
            padding2: fields.padding2,
            padding3: fields.padding3,
        };
    }
    toJSON() {
        return {
            mintPubkey: this.mintPubkey,
            supplyVault: this.supplyVault,
            feeVault: this.feeVault,
            availableAmount: this.availableAmount.toString(),
            borrowedAmountSf: this.borrowedAmountSf.toString(),
            marketPriceSf: this.marketPriceSf.toString(),
            marketPriceLastUpdatedTs: this.marketPriceLastUpdatedTs.toString(),
            mintDecimals: this.mintDecimals.toString(),
            depositLimitCrossedTimestamp: this.depositLimitCrossedTimestamp.toString(),
            borrowLimitCrossedTimestamp: this.borrowLimitCrossedTimestamp.toString(),
            cumulativeBorrowRateBsf: this.cumulativeBorrowRateBsf.toJSON(),
            accumulatedProtocolFeesSf: this.accumulatedProtocolFeesSf.toString(),
            accumulatedReferrerFeesSf: this.accumulatedReferrerFeesSf.toString(),
            pendingReferrerFeesSf: this.pendingReferrerFeesSf.toString(),
            absoluteReferralRateSf: this.absoluteReferralRateSf.toString(),
            tokenProgram: this.tokenProgram,
            padding2: this.padding2.map((item) => item.toString()),
            padding3: this.padding3.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new ReserveLiquidity({
            mintPubkey: (0, kit_1.address)(obj.mintPubkey),
            supplyVault: (0, kit_1.address)(obj.supplyVault),
            feeVault: (0, kit_1.address)(obj.feeVault),
            availableAmount: new bn_js_1.default(obj.availableAmount),
            borrowedAmountSf: new bn_js_1.default(obj.borrowedAmountSf),
            marketPriceSf: new bn_js_1.default(obj.marketPriceSf),
            marketPriceLastUpdatedTs: new bn_js_1.default(obj.marketPriceLastUpdatedTs),
            mintDecimals: new bn_js_1.default(obj.mintDecimals),
            depositLimitCrossedTimestamp: new bn_js_1.default(obj.depositLimitCrossedTimestamp),
            borrowLimitCrossedTimestamp: new bn_js_1.default(obj.borrowLimitCrossedTimestamp),
            cumulativeBorrowRateBsf: types.BigFractionBytes.fromJSON(obj.cumulativeBorrowRateBsf),
            accumulatedProtocolFeesSf: new bn_js_1.default(obj.accumulatedProtocolFeesSf),
            accumulatedReferrerFeesSf: new bn_js_1.default(obj.accumulatedReferrerFeesSf),
            pendingReferrerFeesSf: new bn_js_1.default(obj.pendingReferrerFeesSf),
            absoluteReferralRateSf: new bn_js_1.default(obj.absoluteReferralRateSf),
            tokenProgram: (0, kit_1.address)(obj.tokenProgram),
            padding2: obj.padding2.map((item) => new bn_js_1.default(item)),
            padding3: obj.padding3.map((item) => new bn_js_1.default(item)),
        });
    }
    toEncodable() {
        return ReserveLiquidity.toEncodable(this);
    }
}
exports.ReserveLiquidity = ReserveLiquidity;
//# sourceMappingURL=ReserveLiquidity.js.map