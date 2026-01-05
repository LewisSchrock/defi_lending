import BN from "bn.js";
import * as types from "../types";
export interface BigFractionBytesFields {
    value: Array<BN>;
    padding: Array<BN>;
}
export interface BigFractionBytesJSON {
    value: Array<string>;
    padding: Array<string>;
}
export declare class BigFractionBytes {
    readonly value: Array<BN>;
    readonly padding: Array<BN>;
    constructor(fields: BigFractionBytesFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.BigFractionBytes;
    static toEncodable(fields: BigFractionBytesFields): {
        value: BN[];
        padding: BN[];
    };
    toJSON(): BigFractionBytesJSON;
    static fromJSON(obj: BigFractionBytesJSON): BigFractionBytes;
    toEncodable(): {
        value: BN[];
        padding: BN[];
    };
}
//# sourceMappingURL=BigFractionBytes.d.ts.map