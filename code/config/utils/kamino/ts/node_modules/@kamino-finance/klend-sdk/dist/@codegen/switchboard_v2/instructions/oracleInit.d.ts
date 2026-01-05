import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface OracleInitArgs {
    params: types.OracleInitParamsFields;
}
export interface OracleInitAccounts {
    oracle: Address;
    oracleAuthority: Address;
    wallet: Address;
    programState: Address;
    queue: Address;
    payer: TransactionSigner;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function oracleInit(args: OracleInitArgs, accounts: OracleInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=oracleInit.d.ts.map