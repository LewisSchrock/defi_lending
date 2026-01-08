import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface WithdrawProtocolFeeArgs {
    amount: BN;
}
export interface WithdrawProtocolFeeAccounts {
    globalConfig: Address;
    lendingMarket: Address;
    reserve: Address;
    reserveLiquidityMint: Address;
    lendingMarketAuthority: Address;
    feeVault: Address;
    feeCollectorAta: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<WithdrawProtocolFeeArgs>;
export declare function withdrawProtocolFee(args: WithdrawProtocolFeeArgs, accounts: WithdrawProtocolFeeAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=withdrawProtocolFee.d.ts.map