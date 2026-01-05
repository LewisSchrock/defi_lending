import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface InitArgs {
    params: types.InitParamsFields;
}
export interface InitAccounts {
    upgradeAuthority: TransactionSigner;
    admin: Address;
    transferAuthority: Address;
    perpetuals: Address;
    perpetualsProgram: Address;
    perpetualsProgramData: Address;
    systemProgram: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<InitArgs>;
export declare function init(args: InitArgs, accounts: InitAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=init.d.ts.map