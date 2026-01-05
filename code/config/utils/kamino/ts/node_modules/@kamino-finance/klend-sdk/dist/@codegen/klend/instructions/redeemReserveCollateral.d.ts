import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface RedeemReserveCollateralArgs {
    collateralAmount: BN;
}
export interface RedeemReserveCollateralAccounts {
    owner: TransactionSigner;
    lendingMarket: Address;
    reserve: Address;
    lendingMarketAuthority: Address;
    reserveLiquidityMint: Address;
    reserveCollateralMint: Address;
    reserveLiquiditySupply: Address;
    userSourceCollateral: Address;
    userDestinationLiquidity: Address;
    collateralTokenProgram: Address;
    liquidityTokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<RedeemReserveCollateralArgs>;
export declare function redeemReserveCollateral(args: RedeemReserveCollateralArgs, accounts: RedeemReserveCollateralAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=redeemReserveCollateral.d.ts.map