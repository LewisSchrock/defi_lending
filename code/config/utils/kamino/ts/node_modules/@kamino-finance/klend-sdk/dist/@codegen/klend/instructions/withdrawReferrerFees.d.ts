import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface WithdrawReferrerFeesAccounts {
    referrer: TransactionSigner;
    referrerTokenState: Address;
    reserve: Address;
    reserveLiquidityMint: Address;
    reserveSupplyLiquidity: Address;
    referrerTokenAccount: Address;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    tokenProgram: Address;
}
export declare function withdrawReferrerFees(accounts: WithdrawReferrerFeesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=withdrawReferrerFees.d.ts.map