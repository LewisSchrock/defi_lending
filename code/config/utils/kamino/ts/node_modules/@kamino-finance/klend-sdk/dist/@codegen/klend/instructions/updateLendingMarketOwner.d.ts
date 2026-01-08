import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface UpdateLendingMarketOwnerAccounts {
    lendingMarketOwnerCached: TransactionSigner;
    lendingMarket: Address;
}
export declare function updateLendingMarketOwner(accounts: UpdateLendingMarketOwnerAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=updateLendingMarketOwner.d.ts.map