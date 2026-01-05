import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetTestOraclePriceArgs {
    params: types.SetTestOraclePriceParamsFields;
}
export interface SetTestOraclePriceAccounts {
    admin: TransactionSigner;
    perpetuals: Address;
    pool: Address;
    custody: Address;
    oracleAccount: Address;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<SetTestOraclePriceArgs>;
export declare function setTestOraclePrice(args: SetTestOraclePriceArgs, accounts: SetTestOraclePriceAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setTestOraclePrice.d.ts.map