import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetSwapAmountAndFeesArgs {
    params: types.GetSwapAmountAndFeesParamsFields;
}
export interface GetSwapAmountAndFeesAccounts {
    perpetuals: Address;
    pool: Address;
    receivingCustody: Address;
    receivingCustodyOracleAccount: Address;
    dispensingCustody: Address;
    dispensingCustodyOracleAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<GetSwapAmountAndFeesArgs>;
export declare function getSwapAmountAndFees(args: GetSwapAmountAndFeesArgs, accounts: GetSwapAmountAndFeesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getSwapAmountAndFees.d.ts.map