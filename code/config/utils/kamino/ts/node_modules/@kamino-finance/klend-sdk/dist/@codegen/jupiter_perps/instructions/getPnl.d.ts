import { Address, AccountMeta, AccountSignerMeta, Instruction } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface GetPnlArgs {
    params: types.GetPnlAndFeeParamsFields;
}
export interface GetPnlAccounts {
    perpetuals: Address;
    pool: Address;
    position: Address;
    custody: Address;
    custodyOracleAccount: Address;
    collateralCustody: Address;
}
export declare const layout: import("buffer-layout").Layout<GetPnlArgs>;
export declare function getPnl(args: GetPnlArgs, accounts: GetPnlAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=getPnl.d.ts.map