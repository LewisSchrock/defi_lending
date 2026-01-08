import * as types from "../types";
export interface MerklePriceUpdateFields {
    message: Uint8Array;
    proof: Array<Array<number>>;
}
export interface MerklePriceUpdateJSON {
    message: Array<number>;
    proof: Array<Array<number>>;
}
export declare class MerklePriceUpdate {
    readonly message: Uint8Array;
    readonly proof: Array<Array<number>>;
    constructor(fields: MerklePriceUpdateFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.MerklePriceUpdate;
    static toEncodable(fields: MerklePriceUpdateFields): {
        message: Buffer<ArrayBufferLike>;
        proof: number[][];
    };
    toJSON(): MerklePriceUpdateJSON;
    static fromJSON(obj: MerklePriceUpdateJSON): MerklePriceUpdate;
    toEncodable(): {
        message: Buffer<ArrayBufferLike>;
        proof: number[][];
    };
}
//# sourceMappingURL=MerklePriceUpdate.d.ts.map