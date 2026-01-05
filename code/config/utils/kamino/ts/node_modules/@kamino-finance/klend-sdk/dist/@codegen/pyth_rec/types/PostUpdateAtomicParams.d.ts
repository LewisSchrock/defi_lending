import * as types from "../types";
export interface PostUpdateAtomicParamsFields {
    vaa: Uint8Array;
    merklePriceUpdate: types.MerklePriceUpdateFields;
    treasuryId: number;
}
export interface PostUpdateAtomicParamsJSON {
    vaa: Array<number>;
    merklePriceUpdate: types.MerklePriceUpdateJSON;
    treasuryId: number;
}
export declare class PostUpdateAtomicParams {
    readonly vaa: Uint8Array;
    readonly merklePriceUpdate: types.MerklePriceUpdate;
    readonly treasuryId: number;
    constructor(fields: PostUpdateAtomicParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PostUpdateAtomicParams;
    static toEncodable(fields: PostUpdateAtomicParamsFields): {
        vaa: Buffer<ArrayBufferLike>;
        merklePriceUpdate: {
            message: Buffer<ArrayBufferLike>;
            proof: number[][];
        };
        treasuryId: number;
    };
    toJSON(): PostUpdateAtomicParamsJSON;
    static fromJSON(obj: PostUpdateAtomicParamsJSON): PostUpdateAtomicParams;
    toEncodable(): {
        vaa: Buffer<ArrayBufferLike>;
        merklePriceUpdate: {
            message: Buffer<ArrayBufferLike>;
            proof: number[][];
        };
        treasuryId: number;
    };
}
//# sourceMappingURL=PostUpdateAtomicParams.d.ts.map