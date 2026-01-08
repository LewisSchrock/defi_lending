import { Address } from "@solana/kit";
import * as types from "../types";
export interface AccountMetaZCFields {
    pubkey: Address;
    isSigner: boolean;
    isWritable: boolean;
}
export interface AccountMetaZCJSON {
    pubkey: string;
    isSigner: boolean;
    isWritable: boolean;
}
export declare class AccountMetaZC {
    readonly pubkey: Address;
    readonly isSigner: boolean;
    readonly isWritable: boolean;
    constructor(fields: AccountMetaZCFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AccountMetaZC;
    static toEncodable(fields: AccountMetaZCFields): {
        pubkey: Address;
        isSigner: boolean;
        isWritable: boolean;
    };
    toJSON(): AccountMetaZCJSON;
    static fromJSON(obj: AccountMetaZCJSON): AccountMetaZC;
    toEncodable(): {
        pubkey: Address;
        isSigner: boolean;
        isWritable: boolean;
    };
}
//# sourceMappingURL=AccountMetaZC.d.ts.map