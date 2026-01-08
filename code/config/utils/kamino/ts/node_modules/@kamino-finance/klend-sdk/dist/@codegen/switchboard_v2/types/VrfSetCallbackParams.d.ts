import { Address } from "@solana/kit";
import * as types from "../types";
export interface VrfSetCallbackParamsFields {
    callback: types.CallbackFields;
}
export interface VrfSetCallbackParamsJSON {
    callback: types.CallbackJSON;
}
export declare class VrfSetCallbackParams {
    readonly callback: types.Callback;
    constructor(fields: VrfSetCallbackParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfSetCallbackParams;
    static toEncodable(fields: VrfSetCallbackParamsFields): {
        callback: {
            programId: Address;
            accounts: {
                pubkey: Address;
                isSigner: boolean;
                isWritable: boolean;
            }[];
            ixData: Buffer<ArrayBufferLike>;
        };
    };
    toJSON(): VrfSetCallbackParamsJSON;
    static fromJSON(obj: VrfSetCallbackParamsJSON): VrfSetCallbackParams;
    toEncodable(): {
        callback: {
            programId: Address;
            accounts: {
                pubkey: Address;
                isSigner: boolean;
                isWritable: boolean;
            }[];
            ixData: Buffer<ArrayBufferLike>;
        };
    };
}
//# sourceMappingURL=VrfSetCallbackParams.d.ts.map