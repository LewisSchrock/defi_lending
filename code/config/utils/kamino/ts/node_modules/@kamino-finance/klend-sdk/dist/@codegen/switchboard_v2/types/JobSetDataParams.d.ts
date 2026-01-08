import * as types from "../types";
export interface JobSetDataParamsFields {
    data: Uint8Array;
    chunkIdx: number;
}
export interface JobSetDataParamsJSON {
    data: Array<number>;
    chunkIdx: number;
}
export declare class JobSetDataParams {
    readonly data: Uint8Array;
    readonly chunkIdx: number;
    constructor(fields: JobSetDataParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.JobSetDataParams;
    static toEncodable(fields: JobSetDataParamsFields): {
        data: Buffer<ArrayBufferLike>;
        chunkIdx: number;
    };
    toJSON(): JobSetDataParamsJSON;
    static fromJSON(obj: JobSetDataParamsJSON): JobSetDataParams;
    toEncodable(): {
        data: Buffer<ArrayBufferLike>;
        chunkIdx: number;
    };
}
//# sourceMappingURL=JobSetDataParams.d.ts.map