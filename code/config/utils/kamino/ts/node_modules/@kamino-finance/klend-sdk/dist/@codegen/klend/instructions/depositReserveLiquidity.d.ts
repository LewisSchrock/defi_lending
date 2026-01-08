import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DepositReserveLiquidityArgs {
    liquidityAmount: BN;
}
export interface DepositReserveLiquidityAccounts {
    owner: TransactionSigner;
    reserve: Address;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    reserveLiquidityMint: Address;
    reserveLiquiditySupply: Address;
    reserveCollateralMint: Address;
    userSourceLiquidity: Address;
    userDestinationCollateral: Address;
    collateralTokenProgram: Address;
    liquidityTokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<DepositReserveLiquidityArgs>;
export declare function depositReserveLiquidity(args: DepositReserveLiquidityArgs, accounts: DepositReserveLiquidityAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=depositReserveLiquidity.d.ts.map