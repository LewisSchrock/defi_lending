import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RedeemFeesAccounts {
    reserve: Address;
    reserveLiquidityMint: Address;
    reserveLiquidityFeeReceiver: Address;
    reserveSupplyLiquidity: Address;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    tokenProgram: Address;
}
export declare function redeemFees(accounts: RedeemFeesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=redeemFees.d.ts.map