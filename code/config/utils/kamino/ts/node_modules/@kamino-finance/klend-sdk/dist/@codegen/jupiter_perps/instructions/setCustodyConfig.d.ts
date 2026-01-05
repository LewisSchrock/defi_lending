import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetCustodyConfigArgs {
    params: types.SetCustodyConfigParamsFields;
}
export interface SetCustodyConfigAccounts {
    admin: TransactionSigner;
    perpetuals: Address;
    custody: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function setCustodyConfig(args: SetCustodyConfigArgs, accounts: SetCustodyConfigAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setCustodyConfig.d.ts.map