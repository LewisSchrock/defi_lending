import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DeleteReferrerStateAndShortUrlAccounts {
    referrer: TransactionSigner;
    referrerState: Address;
    shortUrl: Address;
    rent: Address;
    systemProgram: Address;
}
export declare function deleteReferrerStateAndShortUrl(accounts: DeleteReferrerStateAndShortUrlAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=deleteReferrerStateAndShortUrl.d.ts.map