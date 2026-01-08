import * as types from "../types";
export interface VrfProveParamsFields {
    proof: Uint8Array;
    idx: number;
}
export interface VrfProveParamsJSON {
    proof: Array<number>;
    idx: number;
}
export declare class VrfProveParams {
    readonly proof: Uint8Array;
    readonly idx: number;
    constructor(fields: VrfProveParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfProveParams;
    static toEncodable(fields: VrfProveParamsFields): {
        proof: Buffer<ArrayBufferLike>;
        idx: number;
    };
    toJSON(): VrfProveParamsJSON;
    static fromJSON(obj: VrfProveParamsJSON): VrfProveParams;
    toEncodable(): {
        proof: Buffer<ArrayBufferLike>;
        idx: number;
    };
}
//# sourceMappingURL=VrfProveParams.d.ts.map