import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface MarkObligationForDeleveragingArgs {
    autodeleverageTargetLtvPct: number;
}
export interface MarkObligationForDeleveragingAccounts {
    riskCouncil: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
}
export declare const layout: import("buffer-layout").Layout<MarkObligationForDeleveragingArgs>;
export declare function markObligationForDeleveraging(args: MarkObligationForDeleveragingArgs, accounts: MarkObligationForDeleveragingAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=markObligationForDeleveraging.d.ts.map