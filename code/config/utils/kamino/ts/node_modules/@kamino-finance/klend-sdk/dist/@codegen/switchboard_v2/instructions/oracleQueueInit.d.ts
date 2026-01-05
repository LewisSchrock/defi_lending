import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface OracleQueueInitArgs {
    params: types.OracleQueueInitParamsFields;
}
export interface OracleQueueInitAccounts {
    oracleQueue: TransactionSigner;
    authority: Address;
    buffer: Address;
    payer: TransactionSigner;
    systemProgram: Address;
    mint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function oracleQueueInit(args: OracleQueueInitArgs, accounts: OracleQueueInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=oracleQueueInit.d.ts.map