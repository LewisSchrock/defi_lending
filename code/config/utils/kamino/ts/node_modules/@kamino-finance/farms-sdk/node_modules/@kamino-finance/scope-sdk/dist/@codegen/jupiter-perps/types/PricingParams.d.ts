import BN from "bn.js";
import * as types from "../types";
export interface PricingParamsFields {
    tradeSpreadLong: BN;
    tradeSpreadShort: BN;
    swapSpread: BN;
    maxLeverage: BN;
    maxGlobalLongSizes: BN;
    maxGlobalShortSizes: BN;
}
export interface PricingParamsJSON {
    tradeSpreadLong: string;
    tradeSpreadShort: string;
    swapSpread: string;
    maxLeverage: string;
    maxGlobalLongSizes: string;
    maxGlobalShortSizes: string;
}
export declare class PricingParams {
    readonly tradeSpreadLong: BN;
    readonly tradeSpreadShort: BN;
    readonly swapSpread: BN;
    readonly maxLeverage: BN;
    readonly maxGlobalLongSizes: BN;
    readonly maxGlobalShortSizes: BN;
    constructor(fields: PricingParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PricingParams;
    static toEncodable(fields: PricingParamsFields): {
        tradeSpreadLong: BN;
        tradeSpreadShort: BN;
        swapSpread: BN;
        maxLeverage: BN;
        maxGlobalLongSizes: BN;
        maxGlobalShortSizes: BN;
    };
    toJSON(): PricingParamsJSON;
    static fromJSON(obj: PricingParamsJSON): PricingParams;
    toEncodable(): {
        tradeSpreadLong: BN;
        tradeSpreadShort: BN;
        swapSpread: BN;
        maxLeverage: BN;
        maxGlobalLongSizes: BN;
        maxGlobalShortSizes: BN;
    };
}
//# sourceMappingURL=PricingParams.d.ts.map