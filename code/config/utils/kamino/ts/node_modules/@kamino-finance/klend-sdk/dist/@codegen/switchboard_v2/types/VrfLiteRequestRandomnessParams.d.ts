import { Address } from "@solana/kit";
import * as types from "../types";
export interface VrfLiteRequestRandomnessParamsFields {
    callback: types.CallbackFields | null;
}
export interface VrfLiteRequestRandomnessParamsJSON {
    callback: types.CallbackJSON | null;
}
export declare class VrfLiteRequestRandomnessParams {
    readonly callback: types.Callback | null;
    constructor(fields: VrfLiteRequestRandomnessParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfLiteRequestRandomnessParams;
    static toEncodable(fields: VrfLiteRequestRandomnessParamsFields): {
        callback: {
            programId: Address;
            accounts: {
                pubkey: Address;
                isSigner: boolean;
                isWritable: boolean;
            }[];
            ixData: Buffer<ArrayBufferLike>;
        } | null;
    };
    toJSON(): VrfLiteRequestRandomnessParamsJSON;
    static fromJSON(obj: VrfLiteRequestRandomnessParamsJSON): VrfLiteRequestRandomnessParams;
    toEncodable(): {
        callback: {
            programId: Address;
            accounts: {
                pubkey: Address;
                isSigner: boolean;
                isWritable: boolean;
            }[];
            ixData: Buffer<ArrayBufferLike>;
        } | null;
    };
}
//# sourceMappingURL=VrfLiteRequestRandomnessParams.d.ts.map