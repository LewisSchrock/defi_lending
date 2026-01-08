import BN from "bn.js";
import * as types from "../types";
export interface VrfLiteProveAndVerifyParamsFields {
    nonce: number | null;
    proof: Uint8Array;
    proofEncoded: string;
    counter: BN;
}
export interface VrfLiteProveAndVerifyParamsJSON {
    nonce: number | null;
    proof: Array<number>;
    proofEncoded: string;
    counter: string;
}
export declare class VrfLiteProveAndVerifyParams {
    readonly nonce: number | null;
    readonly proof: Uint8Array;
    readonly proofEncoded: string;
    readonly counter: BN;
    constructor(fields: VrfLiteProveAndVerifyParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfLiteProveAndVerifyParams;
    static toEncodable(fields: VrfLiteProveAndVerifyParamsFields): {
        nonce: number | null;
        proof: Buffer<ArrayBufferLike>;
        proofEncoded: string;
        counter: BN;
    };
    toJSON(): VrfLiteProveAndVerifyParamsJSON;
    static fromJSON(obj: VrfLiteProveAndVerifyParamsJSON): VrfLiteProveAndVerifyParams;
    toEncodable(): {
        nonce: number | null;
        proof: Buffer<ArrayBufferLike>;
        proofEncoded: string;
        counter: BN;
    };
}
//# sourceMappingURL=VrfLiteProveAndVerifyParams.d.ts.map