import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface TransferAdminArgs {
    params: types.TransferAdminParamsFields;
}
export interface TransferAdminAccounts {
    admin: TransactionSigner;
    newAdmin: Address;
    perpetuals: Address;
}
export declare const layout: import("buffer-layout").Layout<TransferAdminArgs>;
export declare function transferAdmin(args: TransferAdminArgs, accounts: TransferAdminAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=transferAdmin.d.ts.map