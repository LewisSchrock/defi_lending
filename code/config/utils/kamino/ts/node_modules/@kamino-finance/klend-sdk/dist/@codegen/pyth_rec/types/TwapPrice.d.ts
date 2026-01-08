import BN from "bn.js";
import * as types from "../types";
export interface TwapPriceFields {
    feedId: Array<number>;
    startTime: BN;
    endTime: BN;
    price: BN;
    conf: BN;
    exponent: number;
    /**
     * Ratio out of 1_000_000, where a value of 1_000_000 represents
     * all slots were missed and 0 represents no slots were missed.
     */
    downSlotsRatio: number;
}
export interface TwapPriceJSON {
    feedId: Array<number>;
    startTime: string;
    endTime: string;
    price: string;
    conf: string;
    exponent: number;
    /**
     * Ratio out of 1_000_000, where a value of 1_000_000 represents
     * all slots were missed and 0 represents no slots were missed.
     */
    downSlotsRatio: number;
}
/**
 * The time weighted average price & conf for a feed over the window [start_time, end_time].
 * This type is used to persist the calculated TWAP in TwapUpdate accounts on Solana.
 */
export declare class TwapPrice {
    readonly feedId: Array<number>;
    readonly startTime: BN;
    readonly endTime: BN;
    readonly price: BN;
    readonly conf: BN;
    readonly exponent: number;
    /**
     * Ratio out of 1_000_000, where a value of 1_000_000 represents
     * all slots were missed and 0 represents no slots were missed.
     */
    readonly downSlotsRatio: number;
    constructor(fields: TwapPriceFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.TwapPrice;
    static toEncodable(fields: TwapPriceFields): {
        feedId: number[];
        startTime: BN;
        endTime: BN;
        price: BN;
        conf: BN;
        exponent: number;
        downSlotsRatio: number;
    };
    toJSON(): TwapPriceJSON;
    static fromJSON(obj: TwapPriceJSON): TwapPrice;
    toEncodable(): {
        feedId: number[];
        startTime: BN;
        endTime: BN;
        price: BN;
        conf: BN;
        exponent: number;
        downSlotsRatio: number;
    };
}
//# sourceMappingURL=TwapPrice.d.ts.map