import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface FlashRepayReserveLiquidityArgs {
    liquidityAmount: BN;
    borrowInstructionIndex: number;
}
export interface FlashRepayReserveLiquidityAccounts {
    userTransferAuthority: TransactionSigner;
    lendingMarketAuthority: Address;
    lendingMarket: Address;
    reserve: Address;
    reserveLiquidityMint: Address;
    reserveDestinationLiquidity: Address;
    userSourceLiquidity: Address;
    reserveLiquidityFeeReceiver: Address;
    referrerTokenState: Option<Address>;
    referrerAccount: Option<Address>;
    sysvarInfo: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<FlashRepayReserveLiquidityArgs>;
export declare function flashRepayReserveLiquidity(args: FlashRepayReserveLiquidityArgs, accounts: FlashRepayReserveLiquidityAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=flashRepayReserveLiquidity.d.ts.map