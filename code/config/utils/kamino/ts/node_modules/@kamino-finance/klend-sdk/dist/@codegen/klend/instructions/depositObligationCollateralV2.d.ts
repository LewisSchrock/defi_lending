import { Address, AccountMeta, AccountSignerMeta, Instruction, Option, TransactionSigner } from "@solana/kit";
import BN from "bn.js";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface DepositObligationCollateralV2Args {
    collateralAmount: BN;
}
export interface DepositObligationCollateralV2Accounts {
    depositAccounts: {
        owner: TransactionSigner;
        obligation: Address;
        lendingMarket: Address;
        depositReserve: Address;
        reserveDestinationCollateral: Address;
        userSourceCollateral: Address;
        tokenProgram: Address;
        instructionSysvarAccount: Address;
    };
    lendingMarketAuthority: Address;
    farmsAccounts: {
        obligationFarmUserState: Option<Address>;
        reserveFarmState: Option<Address>;
    };
    farmsProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<DepositObligationCollateralV2Args>;
export declare function depositObligationCollateralV2(args: DepositObligationCollateralV2Args, accounts: DepositObligationCollateralV2Accounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=depositObligationCollateralV2.d.ts.map