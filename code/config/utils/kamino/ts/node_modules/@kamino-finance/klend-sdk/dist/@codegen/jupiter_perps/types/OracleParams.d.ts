import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface OracleParamsFields {
    oracleAccount: Address;
    oracleType: types.OracleTypeKind;
    maxPriceError: BN;
    maxPriceAgeSec: number;
}
export interface OracleParamsJSON {
    oracleAccount: string;
    oracleType: types.OracleTypeJSON;
    maxPriceError: string;
    maxPriceAgeSec: number;
}
export declare class OracleParams {
    readonly oracleAccount: Address;
    readonly oracleType: types.OracleTypeKind;
    readonly maxPriceError: BN;
    readonly maxPriceAgeSec: number;
    constructor(fields: OracleParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.OracleParams;
    static toEncodable(fields: OracleParamsFields): {
        oracleAccount: Address;
        oracleType: {
            None: {};
        } | {
            Test: {};
        } | {
            Pyth: {};
        };
        maxPriceError: BN;
        maxPriceAgeSec: number;
    };
    toJSON(): OracleParamsJSON;
    static fromJSON(obj: OracleParamsJSON): OracleParams;
    toEncodable(): {
        oracleAccount: Address;
        oracleType: {
            None: {};
        } | {
            Test: {};
        } | {
            Pyth: {};
        };
        maxPriceError: BN;
        maxPriceAgeSec: number;
    };
}
//# sourceMappingURL=OracleParams.d.ts.map