import { Address } from "@solana/kit";
import * as types from "../types";
export interface VrfPoolRequestParamsFields {
    callback: types.CallbackFields | null;
}
export interface VrfPoolRequestParamsJSON {
    callback: types.CallbackJSON | null;
}
export declare class VrfPoolRequestParams {
    readonly callback: types.Callback | null;
    constructor(fields: VrfPoolRequestParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfPoolRequestParams;
    static toEncodable(fields: VrfPoolRequestParamsFields): {
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
    toJSON(): VrfPoolRequestParamsJSON;
    static fromJSON(obj: VrfPoolRequestParamsJSON): VrfPoolRequestParams;
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
//# sourceMappingURL=VrfPoolRequestParams.d.ts.map