import * as types from "../types";
export interface ScalarFields {
    bytes: Array<number>;
}
export interface ScalarJSON {
    bytes: Array<number>;
}
export declare class Scalar {
    readonly bytes: Array<number>;
    constructor(fields: ScalarFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.Scalar;
    static toEncodable(fields: ScalarFields): {
        bytes: number[];
    };
    toJSON(): ScalarJSON;
    static fromJSON(obj: ScalarJSON): Scalar;
    toEncodable(): {
        bytes: number[];
    };
}
//# sourceMappingURL=Scalar.d.ts.map