import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface WithdrawObligationCollateralV2Args {
    collateralAmount: BN;
}
export interface WithdrawObligationCollateralV2Accounts {
    withdrawAccounts: {
        owner: TransactionSigner;
        obligation: Address;
        lendingMarket: Address;
        lendingMarketAuthority: Address;
        withdrawReserve: Address;
        reserveSourceCollateral: Address;
        userDestinationCollateral: Address;
        tokenProgram: Address;
        instructionSysvarAccount: Address;
    };
    farmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<WithdrawObligationCollateralV2Args>;
export declare function withdrawObligationCollateralV2(args: WithdrawObligationCollateralV2Args, accounts: WithdrawObligationCollateralV2Accounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=withdrawObligationCollateralV2.d.ts.map