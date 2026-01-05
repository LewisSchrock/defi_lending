import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetDecreasePositionArgs {
    params: types.GetDecreasePositionParamsFields;
}
export interface GetDecreasePositionAccounts {
    perpetuals: Address;
    pool: Address;
    position: Address;
    custody: Address;
    custodyOracleAccount: Address;
    collateralCustody: Address;
    collateralCustodyOracleAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<GetDecreasePositionArgs>;
export declare function getDecreasePosition(args: GetDecreasePositionArgs, accounts: GetDecreasePositionAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getDecreasePosition.d.ts.map