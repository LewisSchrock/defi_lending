import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DepositObligationCollateralArgs {
    collateralAmount: BN;
}
export interface DepositObligationCollateralAccounts {
    owner: TransactionSigner;
    obligation: Address;
    lendingMarket: Address;
    depositReserve: Address;
    reserveDestinationCollateral: Address;
    userSourceCollateral: Address;
    tokenProgram: Address;
    instructionSysvarAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<DepositObligationCollateralArgs>;
export declare function depositObligationCollateral(args: DepositObligationCollateralArgs, accounts: DepositObligationCollateralAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=depositObligationCollateral.d.ts.map