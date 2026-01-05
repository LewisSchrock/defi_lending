import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetRemoveLiquidityAmountAndFeeArgs {
    params: types.GetRemoveLiquidityAmountAndFeeParamsFields;
}
export interface GetRemoveLiquidityAmountAndFeeAccounts {
    perpetuals: Address;
    pool: Address;
    custody: Address;
    custodyOracleAccount: Address;
    lpTokenMint: Address;
}
export declare const layout: import("buffer-layout").Layout<GetRemoveLiquidityAmountAndFeeArgs>;
export declare function getRemoveLiquidityAmountAndFee(args: GetRemoveLiquidityAmountAndFeeArgs, accounts: GetRemoveLiquidityAmountAndFeeAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getRemoveLiquidityAmountAndFee.d.ts.map