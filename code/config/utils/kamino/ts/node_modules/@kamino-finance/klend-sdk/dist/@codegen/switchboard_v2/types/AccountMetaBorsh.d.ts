import { Address } from "@solana/kit";
import * as types from "../types";
export interface AccountMetaBorshFields {
    pubkey: Address;
    isSigner: boolean;
    isWritable: boolean;
}
export interface AccountMetaBorshJSON {
    pubkey: string;
    isSigner: boolean;
    isWritable: boolean;
}
export declare class AccountMetaBorsh {
    readonly pubkey: Address;
    readonly isSigner: boolean;
    readonly isWritable: boolean;
    constructor(fields: AccountMetaBorshFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AccountMetaBorsh;
    static toEncodable(fields: AccountMetaBorshFields): {
        pubkey: Address;
        isSigner: boolean;
        isWritable: boolean;
    };
    toJSON(): AccountMetaBorshJSON;
    static fromJSON(obj: AccountMetaBorshJSON): AccountMetaBorsh;
    toEncodable(): {
        pubkey: Address;
        isSigner: boolean;
        isWritable: boolean;
    };
}
//# sourceMappingURL=AccountMetaBorsh.d.ts.map