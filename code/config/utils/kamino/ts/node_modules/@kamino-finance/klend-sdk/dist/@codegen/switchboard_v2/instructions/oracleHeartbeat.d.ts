import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface OracleHeartbeatArgs {
    params: types.OracleHeartbeatParamsFields;
}
export interface OracleHeartbeatAccounts {
    oracle: Address;
    oracleAuthority: TransactionSigner;
    tokenAccount: Address;
    gcOracle: Address;
    oracleQueue: Address;
    permission: Address;
    dataBuffer: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function oracleHeartbeat(args: OracleHeartbeatArgs, accounts: OracleHeartbeatAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=oracleHeartbeat.d.ts.map