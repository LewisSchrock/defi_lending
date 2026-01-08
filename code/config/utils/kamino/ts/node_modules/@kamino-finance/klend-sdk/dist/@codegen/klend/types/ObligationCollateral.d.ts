import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface ObligationCollateralFields {
    /** Reserve collateral is deposited to */
    depositReserve: Address;
    /** Amount of collateral deposited */
    depositedAmount: BN;
    /** Collateral market value in quote currency (scaled fraction) */
    marketValueSf: BN;
    /**
     * Debt amount (lamport) taken against this collateral.
     * (only meaningful if this obligation is part of an elevation group, otherwise 0)
     * This is only indicative of the debt computed on the last refresh obligation.
     * If the obligation have multiple collateral this value is the same for all of them.
     */
    borrowedAmountAgainstThisCollateralInElevationGroup: BN;
    padding: Array<BN>;
}
export interface ObligationCollateralJSON {
    /** Reserve collateral is deposited to */
    depositReserve: string;
    /** Amount of collateral deposited */
    depositedAmount: string;
    /** Collateral market value in quote currency (scaled fraction) */
    marketValueSf: string;
    /**
     * Debt amount (lamport) taken against this collateral.
     * (only meaningful if this obligation is part of an elevation group, otherwise 0)
     * This is only indicative of the debt computed on the last refresh obligation.
     * If the obligation have multiple collateral this value is the same for all of them.
     */
    borrowedAmountAgainstThisCollateralInElevationGroup: string;
    padding: Array<string>;
}
/** Obligation collateral state */
export declare class ObligationCollateral {
    /** Reserve collateral is deposited to */
    readonly depositReserve: Address;
    /** Amount of collateral deposited */
    readonly depositedAmount: BN;
    /** Collateral market value in quote currency (scaled fraction) */
    readonly marketValueSf: BN;
    /**
     * Debt amount (lamport) taken against this collateral.
     * (only meaningful if this obligation is part of an elevation group, otherwise 0)
     * This is only indicative of the debt computed on the last refresh obligation.
     * If the obligation have multiple collateral this value is the same for all of them.
     */
    readonly borrowedAmountAgainstThisCollateralInElevationGroup: BN;
    readonly padding: Array<BN>;
    constructor(fields: ObligationCollateralFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.ObligationCollateral;
    static toEncodable(fields: ObligationCollateralFields): {
        depositReserve: Address;
        depositedAmount: BN;
        marketValueSf: BN;
        borrowedAmountAgainstThisCollateralInElevationGroup: BN;
        padding: BN[];
    };
    toJSON(): ObligationCollateralJSON;
    static fromJSON(obj: ObligationCollateralJSON): ObligationCollateral;
    toEncodable(): {
        depositReserve: Address;
        depositedAmount: BN;
        marketValueSf: BN;
        borrowedAmountAgainstThisCollateralInElevationGroup: BN;
        padding: BN[];
    };
}
//# sourceMappingURL=ObligationCollateral.d.ts.map