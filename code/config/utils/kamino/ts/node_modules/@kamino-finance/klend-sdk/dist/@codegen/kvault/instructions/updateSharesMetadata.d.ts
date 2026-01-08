import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface UpdateSharesMetadataArgs {
    name: string;
    symbol: string;
    uri: string;
}
export interface UpdateSharesMetadataAccounts {
    vaultAdminAuthority: TransactionSigner;
    vaultState: Address;
    baseVaultAuthority: Address;
    sharesMetadata: Address;
    metadataProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<UpdateSharesMetadataArgs>;
export declare function updateSharesMetadata(args: UpdateSharesMetadataArgs, accounts: UpdateSharesMetadataAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=updateSharesMetadata.d.ts.map