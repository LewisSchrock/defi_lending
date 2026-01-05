import * as types from "../types";
export interface PostUpdateParamsFields {
    merklePriceUpdate: types.MerklePriceUpdateFields;
    treasuryId: number;
}
export interface PostUpdateParamsJSON {
    merklePriceUpdate: types.MerklePriceUpdateJSON;
    treasuryId: number;
}
export declare class PostUpdateParams {
    readonly merklePriceUpdate: types.MerklePriceUpdate;
    readonly treasuryId: number;
    constructor(fields: PostUpdateParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PostUpdateParams;
    static toEncodable(fields: PostUpdateParamsFields): {
        merklePriceUpdate: {
            message: Buffer<ArrayBufferLike>;
            proof: number[][];
        };
        treasuryId: number;
    };
    toJSON(): PostUpdateParamsJSON;
    static fromJSON(obj: PostUpdateParamsJSON): PostUpdateParams;
    toEncodable(): {
        merklePriceUpdate: {
            message: Buffer<ArrayBufferLike>;
            proof: number[][];
        };
        treasuryId: number;
    };
}
//# sourceMappingURL=PostUpdateParams.d.ts.map