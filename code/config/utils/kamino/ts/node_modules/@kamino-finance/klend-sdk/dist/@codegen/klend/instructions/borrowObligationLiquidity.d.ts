import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface BorrowObligationLiquidityArgs {
    liquidityAmount: BN;
}
export interface BorrowObligationLiquidityAccounts {
    owner: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    borrowReserve: Address;
    borrowReserveLiquidityMint: Address;
    reserveSourceLiquidity: Address;
    borrowReserveLiquidityFeeReceiver: Address;
    userDestinationLiquidity: Address;
    referrerTokenState: Option<Address>;
    tokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<BorrowObligationLiquidityArgs>;
export declare function borrowObligationLiquidity(args: BorrowObligationLiquidityArgs, accounts: BorrowObligationLiquidityAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=borrowObligationLiquidity.d.ts.map