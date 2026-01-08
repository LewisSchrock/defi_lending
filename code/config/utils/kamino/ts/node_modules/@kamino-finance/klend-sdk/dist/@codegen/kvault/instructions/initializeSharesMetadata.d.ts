import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitializeSharesMetadataArgs {
    name: string;
    symbol: string;
    uri: string;
}
export interface InitializeSharesMetadataAccounts {
    vaultAdminAuthority: TransactionSigner;
    vaultState: Address;
    sharesMint: Address;
    baseVaultAuthority: Address;
    sharesMetadata: Address;
    systemProgram: Address;
    rent: Address;
    metadataProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<InitializeSharesMetadataArgs>;
export declare function initializeSharesMetadata(args: InitializeSharesMetadataArgs, accounts: InitializeSharesMetadataAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initializeSharesMetadata.d.ts.map