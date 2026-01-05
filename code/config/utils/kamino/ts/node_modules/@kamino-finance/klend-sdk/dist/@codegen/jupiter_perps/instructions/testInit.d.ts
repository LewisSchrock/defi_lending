import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface TestInitArgs {
    params: types.TestInitParamsFields;
}
export interface TestInitAccounts {
    upgradeAuthority: TransactionSigner;
    admin: Address;
    transferAuthority: Address;
    perpetuals: Address;
    systemProgram: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<TestInitArgs>;
export declare function testInit(args: TestInitArgs, accounts: TestInitAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=testInit.d.ts.map