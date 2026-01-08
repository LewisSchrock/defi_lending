import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface LiquidateObligationAndRedeemReserveCollateralV2Args {
    liquidityAmount: BN;
    minAcceptableReceivedLiquidityAmount: BN;
    maxAllowedLtvOverridePercent: BN;
}
export interface LiquidateObligationAndRedeemReserveCollateralV2Accounts {
    liquidationAccounts: {
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
    };
    collateralFarmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    debtFarmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<LiquidateObligationAndRedeemReserveCollateralV2Args>;
export declare function liquidateObligationAndRedeemReserveCollateralV2(args: LiquidateObligationAndRedeemReserveCollateralV2Args, accounts: LiquidateObligationAndRedeemReserveCollateralV2Accounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=liquidateObligationAndRedeemReserveCollateralV2.d.ts.map