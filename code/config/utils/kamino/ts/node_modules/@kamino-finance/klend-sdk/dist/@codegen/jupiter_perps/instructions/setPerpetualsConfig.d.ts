import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetPerpetualsConfigArgs {
    params: types.SetPerpetualsConfigParamsFields;
}
export interface SetPerpetualsConfigAccounts {
    admin: TransactionSigner;
    perpetuals: Address;
}
export declare const layout: import("buffer-layout").Layout<SetPerpetualsConfigArgs>;
export declare function setPerpetualsConfig(args: SetPerpetualsConfigArgs, accounts: SetPerpetualsConfigAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setPerpetualsConfig.d.ts.map