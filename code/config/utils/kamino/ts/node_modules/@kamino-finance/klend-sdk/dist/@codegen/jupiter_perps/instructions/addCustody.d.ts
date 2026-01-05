import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface AddCustodyArgs {
    params: types.AddCustodyParamsFields;
}
export interface AddCustodyAccounts {
    admin: TransactionSigner;
    transferAuthority: Address;
    perpetuals: Address;
    pool: Address;
    custody: Address;
    custodyTokenAccount: Address;
    custodyTokenMint: Address;
    systemProgram: Address;
    tokenProgram: Address;
    rent: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function addCustody(args: AddCustodyArgs, accounts: AddCustodyAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=addCustody.d.ts.map