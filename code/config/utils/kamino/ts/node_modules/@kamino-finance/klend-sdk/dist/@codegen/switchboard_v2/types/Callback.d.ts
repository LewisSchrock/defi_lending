import { Address } from "@solana/kit";
import * as types from "../types";
export interface CallbackFields {
    programId: Address;
    accounts: Array<types.AccountMetaBorshFields>;
    ixData: Uint8Array;
}
export interface CallbackJSON {
    programId: string;
    accounts: Array<types.AccountMetaBorshJSON>;
    ixData: Array<number>;
}
export declare class Callback {
    readonly programId: Address;
    readonly accounts: Array<types.AccountMetaBorsh>;
    readonly ixData: Uint8Array;
    constructor(fields: CallbackFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.Callback;
    static toEncodable(fields: CallbackFields): {
        programId: Address;
        accounts: {
            pubkey: Address;
            isSigner: boolean;
            isWritable: boolean;
        }[];
        ixData: Buffer<ArrayBufferLike>;
    };
    toJSON(): CallbackJSON;
    static fromJSON(obj: CallbackJSON): Callback;
    toEncodable(): {
        programId: Address;
        accounts: {
            pubkey: Address;
            isSigner: boolean;
            isWritable: boolean;
        }[];
        ixData: Buffer<ArrayBufferLike>;
    };
}
//# sourceMappingURL=Callback.d.ts.map