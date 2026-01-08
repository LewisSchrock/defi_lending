import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface LiquidateObligationAndRedeemReserveCollateralArgs {
    liquidityAmount: BN;
    minAcceptableReceivedLiquidityAmount: BN;
    maxAllowedLtvOverridePercent: BN;
}
export interface LiquidateObligationAndRedeemReserveCollateralAccounts {
    liquidator: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    repayReserve: Address;
    repayReserveLiquidityMint: Address;
    repayReserveLiquiditySupply: Address;
    withdrawReserve: Address;
    withdrawReserveLiquidityMint: Address;
    withdrawReserveCollateralMint: Address;
    withdrawReserveCollateralSupply: Address;
    withdrawReserveLiquiditySupply: Address;
    withdrawReserveLiquidityFeeReceiver: Address;
    userSourceLiquidity: Address;
    userDestinationCollateral: Address;
    userDestinationLiquidity: Address;
    collateralTokenProgram: Address;
    repayLiquidityTokenProgram: Address;
    withdrawLiquidityTokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<LiquidateObligationAndRedeemReserveCollateralArgs>;
export declare function liquidateObligationAndRedeemReserveCollateral(args: LiquidateObligationAndRedeemReserveCollateralArgs, accounts: LiquidateObligationAndRedeemReserveCollateralAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=liquidateObligationAndRedeemReserveCollateral.d.ts.map