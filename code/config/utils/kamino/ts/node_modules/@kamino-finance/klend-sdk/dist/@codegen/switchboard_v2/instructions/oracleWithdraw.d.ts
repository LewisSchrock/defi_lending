import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface OracleWithdrawArgs {
    params: types.OracleWithdrawParamsFields;
}
export interface OracleWithdrawAccounts {
    oracle: Address;
    oracleAuthority: TransactionSigner;
    tokenAccount: Address;
    withdrawAccount: Address;
    oracleQueue: Address;
    permission: Address;
    tokenProgram: Address;
    programState: Address;
    payer: TransactionSigner;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function oracleWithdraw(args: OracleWithdrawArgs, accounts: OracleWithdrawAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=oracleWithdraw.d.ts.map