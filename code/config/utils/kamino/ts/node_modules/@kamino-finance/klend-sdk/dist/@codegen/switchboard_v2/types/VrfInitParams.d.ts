import { Address } from "@solana/kit";
import * as types from "../types";
export interface VrfInitParamsFields {
    callback: types.CallbackFields;
    stateBump: number;
}
export interface VrfInitParamsJSON {
    callback: types.CallbackJSON;
    stateBump: number;
}
export declare class VrfInitParams {
    readonly callback: types.Callback;
    readonly stateBump: number;
    constructor(fields: VrfInitParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfInitParams;
    static toEncodable(fields: VrfInitParamsFields): {
        callback: {
            programId: Address;
            accounts: {
                pubkey: Address;
                isSigner: boolean;
                isWritable: boolean;
            }[];
            ixData: Buffer<ArrayBufferLike>;
        };
        stateBump: number;
    };
    toJSON(): VrfInitParamsJSON;
    static fromJSON(obj: VrfInitParamsJSON): VrfInitParams;
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
        stateBump: number;
    };
}
//# sourceMappingURL=VrfInitParams.d.ts.map