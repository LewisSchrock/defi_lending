import { Address } from "@solana/kit";
import * as types from "../types";
export interface CallbackZCFields {
    programId: Address;
    accounts: Array<types.AccountMetaZCFields>;
    accountsLen: number;
    ixData: Array<number>;
    ixDataLen: number;
}
export interface CallbackZCJSON {
    programId: string;
    accounts: Array<types.AccountMetaZCJSON>;
    accountsLen: number;
    ixData: Array<number>;
    ixDataLen: number;
}
export declare class CallbackZC {
    readonly programId: Address;
    readonly accounts: Array<types.AccountMetaZC>;
    readonly accountsLen: number;
    readonly ixData: Array<number>;
    readonly ixDataLen: number;
    constructor(fields: CallbackZCFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.CallbackZC;
    static toEncodable(fields: CallbackZCFields): {
        programId: Address;
        accounts: {
            pubkey: Address;
            isSigner: boolean;
            isWritable: boolean;
        }[];
        accountsLen: number;
        ixData: number[];
        ixDataLen: number;
    };
    toJSON(): CallbackZCJSON;
    static fromJSON(obj: CallbackZCJSON): CallbackZC;
    toEncodable(): {
        programId: Address;
        accounts: {
            pubkey: Address;
            isSigner: boolean;
            isWritable: boolean;
        }[];
        accountsLen: number;
        ixData: number[];
        ixDataLen: number;
    };
}
//# sourceMappingURL=CallbackZC.d.ts.map