import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetPoolConfigArgs {
    params: types.SetPoolConfigParamsFields;
}
export interface SetPoolConfigAccounts {
    admin: TransactionSigner;
    perpetuals: Address;
    pool: Address;
}
export declare const layout: import("buffer-layout").Layout<SetPoolConfigArgs>;
export declare function setPoolConfig(args: SetPoolConfigArgs, accounts: SetPoolConfigAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setPoolConfig.d.ts.map