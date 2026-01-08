import BN from "bn.js";
import * as types from "../types";
export interface VrfProveAndVerifyParamsFields {
    nonce: number | null;
    stateBump: number;
    idx: number;
    proof: Uint8Array;
    proofEncoded: string;
    counter: BN;
}
export interface VrfProveAndVerifyParamsJSON {
    nonce: number | null;
    stateBump: number;
    idx: number;
    proof: Array<number>;
    proofEncoded: string;
    counter: string;
}
export declare class VrfProveAndVerifyParams {
    readonly nonce: number | null;
    readonly stateBump: number;
    readonly idx: number;
    readonly proof: Uint8Array;
    readonly proofEncoded: string;
    readonly counter: BN;
    constructor(fields: VrfProveAndVerifyParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfProveAndVerifyParams;
    static toEncodable(fields: VrfProveAndVerifyParamsFields): {
        nonce: number | null;
        stateBump: number;
        idx: number;
        proof: Buffer<ArrayBufferLike>;
        proofEncoded: string;
        counter: BN;
    };
    toJSON(): VrfProveAndVerifyParamsJSON;
    static fromJSON(obj: VrfProveAndVerifyParamsJSON): VrfProveAndVerifyParams;
    toEncodable(): {
        nonce: number | null;
        stateBump: number;
        idx: number;
        proof: Buffer<ArrayBufferLike>;
        proofEncoded: string;
        counter: BN;
    };
}
//# sourceMappingURL=VrfProveAndVerifyParams.d.ts.map