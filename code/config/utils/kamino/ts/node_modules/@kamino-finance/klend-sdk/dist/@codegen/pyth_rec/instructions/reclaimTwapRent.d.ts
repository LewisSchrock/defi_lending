import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface ReclaimTwapRentAccounts {
    payer: TransactionSigner;
    twapUpdateAccount: Address;
}
export declare function reclaimTwapRent(accounts: ReclaimTwapRentAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=reclaimTwapRent.d.ts.map