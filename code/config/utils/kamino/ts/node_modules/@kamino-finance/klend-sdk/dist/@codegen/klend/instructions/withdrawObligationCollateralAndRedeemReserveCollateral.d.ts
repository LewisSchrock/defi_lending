import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface WithdrawObligationCollateralAndRedeemReserveCollateralArgs {
    collateralAmount: BN;
}
export interface WithdrawObligationCollateralAndRedeemReserveCollateralAccounts {
    owner: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    withdrawReserve: Address;
    reserveLiquidityMint: Address;
    reserveSourceCollateral: Address;
    reserveCollateralMint: Address;
    reserveLiquiditySupply: Address;
    userDestinationLiquidity: Address;
    placeholderUserDestinationCollateral: Option<Address>;
    collateralTokenProgram: Address;
    liquidityTokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<WithdrawObligationCollateralAndRedeemReserveCollateralArgs>;
export declare function withdrawObligationCollateralAndRedeemReserveCollateral(args: WithdrawObligationCollateralAndRedeemReserveCollateralArgs, accounts: WithdrawObligationCollateralAndRedeemReserveCollateralAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=withdrawObligationCollateralAndRedeemReserveCollateral.d.ts.map