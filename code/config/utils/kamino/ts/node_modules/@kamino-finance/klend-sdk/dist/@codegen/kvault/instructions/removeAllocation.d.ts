import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RemoveAllocationAccounts {
    vaultAdminAuthority: TransactionSigner;
    vaultState: Address;
    reserve: Address;
}
export declare function removeAllocation(accounts: RemoveAllocationAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=removeAllocation.d.ts.map