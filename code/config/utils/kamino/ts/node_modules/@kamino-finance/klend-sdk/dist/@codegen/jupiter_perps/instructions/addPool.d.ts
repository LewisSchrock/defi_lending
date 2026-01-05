import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface AddPoolArgs {
    params: types.AddPoolParamsFields;
}
export interface AddPoolAccounts {
    admin: TransactionSigner;
    transferAuthority: Address;
    perpetuals: Address;
    pool: Address;
    lpTokenMint: Address;
    systemProgram: Address;
    tokenProgram: Address;
    rent: Address;
}
export declare const layout: import("buffer-layout").Layout<AddPoolArgs>;
export declare function addPool(args: AddPoolArgs, accounts: AddPoolAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=addPool.d.ts.map