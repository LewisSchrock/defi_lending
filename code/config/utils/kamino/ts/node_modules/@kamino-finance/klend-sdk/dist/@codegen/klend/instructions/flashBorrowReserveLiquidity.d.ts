import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface FlashBorrowReserveLiquidityArgs {
    liquidityAmount: BN;
}
export interface FlashBorrowReserveLiquidityAccounts {
    userTransferAuthority: TransactionSigner;
    lendingMarketAuthority: Address;
    lendingMarket: Address;
    reserve: Address;
    reserveLiquidityMint: Address;
    reserveSourceLiquidity: Address;
    userDestinationLiquidity: Address;
    reserveLiquidityFeeReceiver: Address;
    referrerTokenState: Option<Address>;
    referrerAccount: Option<Address>;
    sysvarInfo: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<FlashBorrowReserveLiquidityArgs>;
export declare function flashBorrowReserveLiquidity(args: FlashBorrowReserveLiquidityArgs, accounts: FlashBorrowReserveLiquidityAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=flashBorrowReserveLiquidity.d.ts.map