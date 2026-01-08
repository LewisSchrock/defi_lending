import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitReferrerStateAndShortUrlArgs {
    shortUrl: string;
}
export interface InitReferrerStateAndShortUrlAccounts {
    referrer: TransactionSigner;
    referrerState: Address;
    referrerShortUrl: Address;
    referrerUserMetadata: Address;
    rent: Address;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<InitReferrerStateAndShortUrlArgs>;
export declare function initReferrerStateAndShortUrl(args: InitReferrerStateAndShortUrlArgs, accounts: InitReferrerStateAndShortUrlAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initReferrerStateAndShortUrl.d.ts.map