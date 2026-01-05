import { Address, AccountMeta, AccountSignerMeta, Instruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export declare const DISCRIMINATOR: Buffer<ArrayBuffer>;
export interface SetDataSourcesArgs {
    validDataSources: Array<types.DataSourceFields>;
}
export interface SetDataSourcesAccounts {
    payer: TransactionSigner;
    config: Address;
}
export declare const layout: import("buffer-layout").Layout<SetDataSourcesArgs>;
export declare function setDataSources(args: SetDataSourcesArgs, accounts: SetDataSourcesAccounts, remainingAccounts?: Array<AccountMeta | AccountSignerMeta>, programAddress?: Address): Instruction<string, readonly (AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>;
//# sourceMappingURL=setDataSources.d.ts.map