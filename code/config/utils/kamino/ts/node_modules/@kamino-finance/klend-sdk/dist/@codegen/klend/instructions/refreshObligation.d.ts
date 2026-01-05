import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RefreshObligationAccounts {
    lendingMarket: Address;
    obligation: Address;
}
export declare function refreshObligation(accounts: RefreshObligationAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=refreshObligation.d.ts.map