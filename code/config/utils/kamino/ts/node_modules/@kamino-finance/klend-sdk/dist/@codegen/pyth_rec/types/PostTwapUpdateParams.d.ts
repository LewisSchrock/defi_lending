import * as types from "../types";
export interface PostTwapUpdateParamsFields {
    startMerklePriceUpdate: types.MerklePriceUpdateFields;
    endMerklePriceUpdate: types.MerklePriceUpdateFields;
    treasuryId: number;
}
export interface PostTwapUpdateParamsJSON {
    startMerklePriceUpdate: types.MerklePriceUpdateJSON;
    endMerklePriceUpdate: types.MerklePriceUpdateJSON;
    treasuryId: number;
}
export declare class PostTwapUpdateParams {
    readonly startMerklePriceUpdate: types.MerklePriceUpdate;
    readonly endMerklePriceUpdate: types.MerklePriceUpdate;
    readonly treasuryId: number;
    constructor(fields: PostTwapUpdateParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PostTwapUpdateParams;
    static toEncodable(fields: PostTwapUpdateParamsFields): {
        startMerklePriceUpdate: {
            message: Buffer<ArrayBufferLike>;
            proof: number[][];
        };
        endMerklePriceUpdate: {
            message: Buffer<ArrayBufferLike>;
            proof: number[][];
        };
        treasuryId: number;
    };
    toJSON(): PostTwapUpdateParamsJSON;
    static fromJSON(obj: PostTwapUpdateParamsJSON): PostTwapUpdateParams;
    toEncodable(): {
        startMerklePriceUpdate: {
            message: Buffer<ArrayBufferLike>;
            proof: number[][];
        };
        endMerklePriceUpdate: {
            message: Buffer<ArrayBufferLike>;
            proof: number[][];
        };
        treasuryId: number;
    };
}
//# sourceMappingURL=PostTwapUpdateParams.d.ts.map