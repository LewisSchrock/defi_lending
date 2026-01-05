import BN from "bn.js";
import * as types from "../types";
export interface OraclePriceFields {
    price: BN;
    exponent: number;
}
export interface OraclePriceJSON {
    price: string;
    exponent: number;
}
export declare class OraclePrice {
    readonly price: BN;
    readonly exponent: number;
    constructor(fields: OraclePriceFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.OraclePrice;
    static toEncodable(fields: OraclePriceFields): {
        price: BN;
        exponent: number;
    };
    toJSON(): OraclePriceJSON;
    static fromJSON(obj: OraclePriceJSON): OraclePrice;
    toEncodable(): {
        price: BN;
        exponent: number;
    };
}
//# sourceMappingURL=OraclePrice.d.ts.map