import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitReferrerTokenStateAccounts {
    payer: TransactionSigner;
    lendingMarket: Address;
    reserve: Address;
    referrer: Address;
    referrerTokenState: Address;
    rent: Address;
    systemProgram: Address;
}
export declare function initReferrerTokenState(accounts: InitReferrerTokenStateAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=initReferrerTokenState.d.ts.map