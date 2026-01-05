import BN from "bn.js";
import * as types from "../types";
export interface SetTestOraclePriceParamsFields {
    price: BN;
    expo: number;
    conf: BN;
    publishTime: BN;
}
export interface SetTestOraclePriceParamsJSON {
    price: string;
    expo: number;
    conf: string;
    publishTime: string;
}
export declare class SetTestOraclePriceParams {
    readonly price: BN;
    readonly expo: number;
    readonly conf: BN;
    readonly publishTime: BN;
    constructor(fields: SetTestOraclePriceParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SetTestOraclePriceParams;
    static toEncodable(fields: SetTestOraclePriceParamsFields): {
        price: BN;
        expo: number;
        conf: BN;
        publishTime: BN;
    };
    toJSON(): SetTestOraclePriceParamsJSON;
    static fromJSON(obj: SetTestOraclePriceParamsJSON): SetTestOraclePriceParams;
    toEncodable(): {
        price: BN;
        expo: number;
        conf: BN;
        publishTime: BN;
    };
}
//# sourceMappingURL=SetTestOraclePriceParams.d.ts.map