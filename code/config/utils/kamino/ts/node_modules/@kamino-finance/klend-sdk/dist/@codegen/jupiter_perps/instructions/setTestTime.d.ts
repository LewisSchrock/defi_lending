import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetTestTimeArgs {
    params: types.SetTestTimeParamsFields;
}
export interface SetTestTimeAccounts {
    admin: TransactionSigner;
    perpetuals: Address;
}
export declare const layout: import("buffer-layout").Layout<SetTestTimeArgs>;
export declare function setTestTime(args: SetTestTimeArgs, accounts: SetTestTimeAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setTestTime.d.ts.map