import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface ReserveLiquidityFields {
    /** Reserve liquidity mint address */
    mintPubkey: Address;
    /** Reserve liquidity supply address */
    supplyVault: Address;
    /** Reserve liquidity fee collection address */
    feeVault: Address;
    /** Reserve liquidity available */
    availableAmount: BN;
    /** Reserve liquidity borrowed (scaled fraction) */
    borrowedAmountSf: BN;
    /** Reserve liquidity market price in quote currency (scaled fraction) */
    marketPriceSf: BN;
    /** Unix timestamp of the market price (from the oracle) */
    marketPriceLastUpdatedTs: BN;
    /** Reserve liquidity mint decimals */
    mintDecimals: BN;
    /**
     * Timestamp when the last refresh reserve detected that the liquidity amount is above the deposit cap. When this threshold is crossed, then redemptions (auto-deleverage) are enabled.
     * If the threshold is not crossed, then the timestamp is set to 0
     */
    depositLimitCrossedTimestamp: BN;
    /**
     * Timestamp when the last refresh reserve detected that the borrowed amount is above the borrow cap. When this threshold is crossed, then redemptions (auto-deleverage) are enabled.
     * If the threshold is not crossed, then the timestamp is set to 0
     */
    borrowLimitCrossedTimestamp: BN;
    /** Reserve liquidity cumulative borrow rate (scaled fraction) */
    cumulativeBorrowRateBsf: types.BigFractionBytesFields;
    /** Reserve cumulative protocol fees (scaled fraction) */
    accumulatedProtocolFeesSf: BN;
    /** Reserve cumulative referrer fees (scaled fraction) */
    accumulatedReferrerFeesSf: BN;
    /** Reserve pending referrer fees, to be claimed in refresh_obligation by referrer or protocol (scaled fraction) */
    pendingReferrerFeesSf: BN;
    /** Reserve referrer fee absolute rate calculated at each refresh_reserve operation (scaled fraction) */
    absoluteReferralRateSf: BN;
    /** Token program of the liquidity mint */
    tokenProgram: Address;
    padding2: Array<BN>;
    padding3: Array<BN>;
}
export interface ReserveLiquidityJSON {
    /** Reserve liquidity mint address */
    mintPubkey: string;
    /** Reserve liquidity supply address */
    supplyVault: string;
    /** Reserve liquidity fee collection address */
    feeVault: string;
    /** Reserve liquidity available */
    availableAmount: string;
    /** Reserve liquidity borrowed (scaled fraction) */
    borrowedAmountSf: string;
    /** Reserve liquidity market price in quote currency (scaled fraction) */
    marketPriceSf: string;
    /** Unix timestamp of the market price (from the oracle) */
    marketPriceLastUpdatedTs: string;
    /** Reserve liquidity mint decimals */
    mintDecimals: string;
    /**
     * Timestamp when the last refresh reserve detected that the liquidity amount is above the deposit cap. When this threshold is crossed, then redemptions (auto-deleverage) are enabled.
     * If the threshold is not crossed, then the timestamp is set to 0
     */
    depositLimitCrossedTimestamp: string;
    /**
     * Timestamp when the last refresh reserve detected that the borrowed amount is above the borrow cap. When this threshold is crossed, then redemptions (auto-deleverage) are enabled.
     * If the threshold is not crossed, then the timestamp is set to 0
     */
    borrowLimitCrossedTimestamp: string;
    /** Reserve liquidity cumulative borrow rate (scaled fraction) */
    cumulativeBorrowRateBsf: types.BigFractionBytesJSON;
    /** Reserve cumulative protocol fees (scaled fraction) */
    accumulatedProtocolFeesSf: string;
    /** Reserve cumulative referrer fees (scaled fraction) */
    accumulatedReferrerFeesSf: string;
    /** Reserve pending referrer fees, to be claimed in refresh_obligation by referrer or protocol (scaled fraction) */
    pendingReferrerFeesSf: string;
    /** Reserve referrer fee absolute rate calculated at each refresh_reserve operation (scaled fraction) */
    absoluteReferralRateSf: string;
    /** Token program of the liquidity mint */
    tokenProgram: string;
    padding2: Array<string>;
    padding3: Array<string>;
}
/** Reserve liquidity */
export declare class ReserveLiquidity {
    /** Reserve liquidity mint address */
    readonly mintPubkey: Address;
    /** Reserve liquidity supply address */
    readonly supplyVault: Address;
    /** Reserve liquidity fee collection address */
    readonly feeVault: Address;
    /** Reserve liquidity available */
    readonly availableAmount: BN;
    /** Reserve liquidity borrowed (scaled fraction) */
    readonly borrowedAmountSf: BN;
    /** Reserve liquidity market price in quote currency (scaled fraction) */
    readonly marketPriceSf: BN;
    /** Unix timestamp of the market price (from the oracle) */
    readonly marketPriceLastUpdatedTs: BN;
    /** Reserve liquidity mint decimals */
    readonly mintDecimals: BN;
    /**
     * Timestamp when the last refresh reserve detected that the liquidity amount is above the deposit cap. When this threshold is crossed, then redemptions (auto-deleverage) are enabled.
     * If the threshold is not crossed, then the timestamp is set to 0
     */
    readonly depositLimitCrossedTimestamp: BN;
    /**
     * Timestamp when the last refresh reserve detected that the borrowed amount is above the borrow cap. When this threshold is crossed, then redemptions (auto-deleverage) are enabled.
     * If the threshold is not crossed, then the timestamp is set to 0
     */
    readonly borrowLimitCrossedTimestamp: BN;
    /** Reserve liquidity cumulative borrow rate (scaled fraction) */
    readonly cumulativeBorrowRateBsf: types.BigFractionBytes;
    /** Reserve cumulative protocol fees (scaled fraction) */
    readonly accumulatedProtocolFeesSf: BN;
    /** Reserve cumulative referrer fees (scaled fraction) */
    readonly accumulatedReferrerFeesSf: BN;
    /** Reserve pending referrer fees, to be claimed in refresh_obligation by referrer or protocol (scaled fraction) */
    readonly pendingReferrerFeesSf: BN;
    /** Reserve referrer fee absolute rate calculated at each refresh_reserve operation (scaled fraction) */
    readonly absoluteReferralRateSf: BN;
    /** Token program of the liquidity mint */
    readonly tokenProgram: Address;
    readonly padding2: Array<BN>;
    readonly padding3: Array<BN>;
    constructor(fields: ReserveLiquidityFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.ReserveLiquidity;
    static toEncodable(fields: ReserveLiquidityFields): {
        mintPubkey: Address;
        supplyVault: Address;
        feeVault: Address;
        availableAmount: BN;
        borrowedAmountSf: BN;
        marketPriceSf: BN;
        marketPriceLastUpdatedTs: BN;
        mintDecimals: BN;
        depositLimitCrossedTimestamp: BN;
        borrowLimitCrossedTimestamp: BN;
        cumulativeBorrowRateBsf: {
            value: BN[];
            padding: BN[];
        };
        accumulatedProtocolFeesSf: BN;
        accumulatedReferrerFeesSf: BN;
        pendingReferrerFeesSf: BN;
        absoluteReferralRateSf: BN;
        tokenProgram: Address;
        padding2: BN[];
        padding3: BN[];
    };
    toJSON(): ReserveLiquidityJSON;
    static fromJSON(obj: ReserveLiquidityJSON): ReserveLiquidity;
    toEncodable(): {
        mintPubkey: Address;
        supplyVault: Address;
        feeVault: Address;
        availableAmount: BN;
        borrowedAmountSf: BN;
        marketPriceSf: BN;
        marketPriceLastUpdatedTs: BN;
        mintDecimals: BN;
        depositLimitCrossedTimestamp: BN;
        borrowLimitCrossedTimestamp: BN;
        cumulativeBorrowRateBsf: {
            value: BN[];
            padding: BN[];
        };
        accumulatedProtocolFeesSf: BN;
        accumulatedReferrerFeesSf: BN;
        pendingReferrerFeesSf: BN;
        absoluteReferralRateSf: BN;
        tokenProgram: Address;
        padding2: BN[];
        padding3: BN[];
    };
}
//# sourceMappingURL=ReserveLiquidity.d.ts.map