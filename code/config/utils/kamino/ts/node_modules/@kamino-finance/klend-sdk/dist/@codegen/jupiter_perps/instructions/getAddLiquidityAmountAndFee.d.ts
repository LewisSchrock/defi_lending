import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetAddLiquidityAmountAndFeeArgs {
    params: types.GetAddLiquidityAmountAndFeeParamsFields;
}
export interface GetAddLiquidityAmountAndFeeAccounts {
    perpetuals: Address;
    pool: Address;
    custody: Address;
    custodyOracleAccount: Address;
    lpTokenMint: Address;
}
export declare const layout: import("buffer-layout").Layout<GetAddLiquidityAmountAndFeeArgs>;
export declare function getAddLiquidityAmountAndFee(args: GetAddLiquidityAmountAndFeeArgs, accounts: GetAddLiquidityAmountAndFeeAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getAddLiquidityAmountAndFee.d.ts.map