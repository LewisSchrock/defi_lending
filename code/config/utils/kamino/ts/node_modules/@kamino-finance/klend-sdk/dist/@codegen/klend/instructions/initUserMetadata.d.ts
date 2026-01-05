import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitUserMetadataArgs {
    userLookupTable: Address;
}
export interface InitUserMetadataAccounts {
    owner: TransactionSigner;
    feePayer: TransactionSigner;
    userMetadata: Address;
    referrerUserMetadata: Option<Address>;
    rent: Address;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<InitUserMetadataArgs>;
export declare function initUserMetadata(args: InitUserMetadataArgs, accounts: InitUserMetadataAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initUserMetadata.d.ts.map