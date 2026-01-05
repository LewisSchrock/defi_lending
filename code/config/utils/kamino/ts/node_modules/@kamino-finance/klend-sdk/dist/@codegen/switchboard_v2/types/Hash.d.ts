import * as types from "../types";
export interface HashFields {
    data: Array<number>;
}
export interface HashJSON {
    data: Array<number>;
}
export declare class Hash {
    readonly data: Array<number>;
    constructor(fields: HashFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.Hash;
    static toEncodable(fields: HashFields): {
        data: number[];
    };
    toJSON(): HashJSON;
    static fromJSON(obj: HashJSON): Hash;
    toEncodable(): {
        data: number[];
    };
}
//# sourceMappingURL=Hash.d.ts.map