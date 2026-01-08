import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface WithdrawObligationCollateralAndRedeemReserveCollateralV2Args {
    collateralAmount: BN;
}
export interface WithdrawObligationCollateralAndRedeemReserveCollateralV2Accounts {
    withdrawAccounts: {
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
    };
    farmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<WithdrawObligationCollateralAndRedeemReserveCollateralV2Args>;
export declare function withdrawObligationCollateralAndRedeemReserveCollateralV2(args: WithdrawObligationCollateralAndRedeemReserveCollateralV2Args, accounts: WithdrawObligationCollateralAndRedeemReserveCollateralV2Accounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=withdrawObligationCollateralAndRedeemReserveCollateralV2.d.ts.map