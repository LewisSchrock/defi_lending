import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface WithdrawObligationCollateralArgs {
    collateralAmount: BN;
}
export interface WithdrawObligationCollateralAccounts {
    owner: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
    lendingMarketAuthority: Address;
    withdrawReserve: Address;
    reserveSourceCollateral: Address;
    userDestinationCollateral: Address;
    tokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<WithdrawObligationCollateralArgs>;
export declare function withdrawObligationCollateral(args: WithdrawObligationCollateralArgs, accounts: WithdrawObligationCollateralAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=withdrawObligationCollateral.d.ts.map