import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetLiquidationStateArgs {
    params: types.GetLiquidationStateParamsFields;
}
export interface GetLiquidationStateAccounts {
    perpetuals: Address;
    pool: Address;
    position: Address;
    custody: Address;
    custodyOracleAccount: Address;
    collateralCustody: Address;
}
export declare const layout: import("buffer-layout").Layout<GetLiquidationStateArgs>;
export declare function getLiquidationState(args: GetLiquidationStateArgs, accounts: GetLiquidationStateAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getLiquidationState.d.ts.map