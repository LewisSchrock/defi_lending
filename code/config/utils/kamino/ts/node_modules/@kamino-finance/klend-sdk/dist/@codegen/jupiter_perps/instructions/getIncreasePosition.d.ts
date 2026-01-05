import { Address, AccountMeta, AccountSignerMeta, Instruction, Option } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetIncreasePositionArgs {
    params: types.GetIncreasePositionParamsFields;
}
export interface GetIncreasePositionAccounts {
    perpetuals: Address;
    pool: Address;
    position: Option<Address>;
    custody: Address;
    custodyOracleAccount: Address;
    collateralCustody: Address;
    collateralCustodyOracleAccount: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function getIncreasePosition(args: GetIncreasePositionArgs, accounts: GetIncreasePositionAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getIncreasePosition.d.ts.map