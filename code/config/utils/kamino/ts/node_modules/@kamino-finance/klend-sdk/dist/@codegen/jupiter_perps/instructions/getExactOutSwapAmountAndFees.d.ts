import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetExactOutSwapAmountAndFeesArgs {
    params: types.GetExactOutSwapAmountAndFeesParamsFields;
}
export interface GetExactOutSwapAmountAndFeesAccounts {
    perpetuals: Address;
    pool: Address;
    receivingCustody: Address;
    receivingCustodyOracleAccount: Address;
    dispensingCustody: Address;
    dispensingCustodyOracleAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<GetExactOutSwapAmountAndFeesArgs>;
export declare function getExactOutSwapAmountAndFees(args: GetExactOutSwapAmountAndFeesArgs, accounts: GetExactOutSwapAmountAndFeesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getExactOutSwapAmountAndFees.d.ts.map