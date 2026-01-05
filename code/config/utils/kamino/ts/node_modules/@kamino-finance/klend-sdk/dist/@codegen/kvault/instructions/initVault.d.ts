import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitVaultAccounts {
    adminAuthority: TransactionSigner;
    vaultState: Address;
    baseVaultAuthority: Address;
    tokenVault: Address;
    baseTokenMint: Address;
    sharesMint: Address;
    adminTokenAccount: Address;
    systemProgram: Address;
    rent: Address;
    tokenProgram: Address;
    sharesTokenProgram: Address;
}
export declare function initVault(accounts: InitVaultAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initVault.d.ts.map