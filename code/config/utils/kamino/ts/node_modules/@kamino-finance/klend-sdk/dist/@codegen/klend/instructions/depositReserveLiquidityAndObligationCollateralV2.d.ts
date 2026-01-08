import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DepositReserveLiquidityAndObligationCollateralV2Args {
    liquidityAmount: BN;
}
export interface DepositReserveLiquidityAndObligationCollateralV2Accounts {
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
    farmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<DepositReserveLiquidityAndObligationCollateralV2Args>;
export declare function depositReserveLiquidityAndObligationCollateralV2(args: DepositReserveLiquidityAndObligationCollateralV2Args, accounts: DepositReserveLiquidityAndObligationCollateralV2Accounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=depositReserveLiquidityAndObligationCollateralV2.d.ts.map