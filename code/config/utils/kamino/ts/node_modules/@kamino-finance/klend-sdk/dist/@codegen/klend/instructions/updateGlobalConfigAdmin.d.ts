import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface UpdateGlobalConfigAdminAccounts {
    pendingAdmin: TransactionSigner;
    globalConfig: Address;
}
export declare function updateGlobalConfigAdmin(accounts: UpdateGlobalConfigAdminAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=updateGlobalConfigAdmin.d.ts.map