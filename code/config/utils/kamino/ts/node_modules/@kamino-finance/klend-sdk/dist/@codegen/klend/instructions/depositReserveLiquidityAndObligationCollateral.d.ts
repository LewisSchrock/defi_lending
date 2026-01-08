import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DepositReserveLiquidityAndObligationCollateralArgs {
    liquidityAmount: BN;
}
export interface DepositReserveLiquidityAndObligationCollateralAccounts {
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
}
export declare const layout: import("buffer-layout").Layout<DepositReserveLiquidityAndObligationCollateralArgs>;
export declare function depositReserveLiquidityAndObligationCollateral(args: DepositReserveLiquidityAndObligationCollateralArgs, accounts: DepositReserveLiquidityAndObligationCollateralAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=depositReserveLiquidityAndObligationCollateral.d.ts.map