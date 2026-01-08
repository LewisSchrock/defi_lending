import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DepositAndWithdrawArgs {
    liquidityAmount: BN;
    withdrawCollateralAmount: BN;
}
export interface DepositAndWithdrawAccounts {
    depositAccounts: {
        owner: TransactionSigner;
        obligation: Address;
        lendingMarket: Address;
        lendingMarketAuthority: Address;
        reserve: Address;
        reserveLiquidityMint: Address;
        reserveLiquiditySupply: Address;
        reserveCollateralMint: Address;
        reserveDestinationDepositCollateral: Address;
        userSourceLiquidity: Address;
        placeholderUserDestinationCollateral: Option<Address>;
        collateralTokenProgram: Address;
        liquidityTokenProgram: Address;
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
    depositFarmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    withdrawFarmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<DepositAndWithdrawArgs>;
export declare function depositAndWithdraw(args: DepositAndWithdrawArgs, accounts: DepositAndWithdrawAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=depositAndWithdraw.d.ts.map