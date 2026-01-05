import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface OracleQueueSetConfigArgs {
    params: types.OracleQueueSetConfigParamsFields;
}
export interface OracleQueueSetConfigAccounts {
    queue: Address;
    authority: TransactionSigner;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function oracleQueueSetConfig(args: OracleQueueSetConfigArgs, accounts: OracleQueueSetConfigAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=oracleQueueSetConfig.d.ts.map