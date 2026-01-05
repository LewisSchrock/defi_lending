import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetCustodyGlobalLimitArgs {
    params: types.SetCustodyGlobalLimitParamsFields;
}
export interface SetCustodyGlobalLimitAccounts {
    keeper: TransactionSigner;
    custody: Address;
}
export declare const layout: import("buffer-layout").Layout<SetCustodyGlobalLimitArgs>;
export declare function setCustodyGlobalLimit(args: SetCustodyGlobalLimitArgs, accounts: SetCustodyGlobalLimitAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setCustodyGlobalLimit.d.ts.map