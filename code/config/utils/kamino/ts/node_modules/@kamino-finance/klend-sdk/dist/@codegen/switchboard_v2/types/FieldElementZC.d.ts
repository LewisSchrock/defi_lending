import BN from "bn.js";
import * as types from "../types";
export interface FieldElementZCFields {
    bytes: Array<BN>;
}
export interface FieldElementZCJSON {
    bytes: Array<string>;
}
export declare class FieldElementZC {
    readonly bytes: Array<BN>;
    constructor(fields: FieldElementZCFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.FieldElementZC;
    static toEncodable(fields: FieldElementZCFields): {
        bytes: BN[];
    };
    toJSON(): FieldElementZCJSON;
    static fromJSON(obj: FieldElementZCJSON): FieldElementZC;
    toEncodable(): {
        bytes: BN[];
    };
}
//# sourceMappingURL=FieldElementZC.d.ts.map