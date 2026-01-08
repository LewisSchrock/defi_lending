import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RepayAndWithdrawAndRedeemArgs {
    repayAmount: BN;
    withdrawCollateralAmount: BN;
}
export interface RepayAndWithdrawAndRedeemAccounts {
    repayAccounts: {
        owner: TransactionSigner;
        obligation: Address;
        lendingMarket: Address;
        repayReserve: Address;
        reserveLiquidityMint: Address;
        reserveDestinationLiquidity: Address;
        userSourceLiquidity: Address;
        tokenProgram: Address;
        instructionSysvarAccount: Address;
    };
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
export declare const layout: import("buffer-layout").Layout<RepayAndWithdrawAndRedeemArgs>;
export declare function repayAndWithdrawAndRedeem(args: RepayAndWithdrawAndRedeemArgs, accounts: RepayAndWithdrawAndRedeemAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=repayAndWithdrawAndRedeem.d.ts.map