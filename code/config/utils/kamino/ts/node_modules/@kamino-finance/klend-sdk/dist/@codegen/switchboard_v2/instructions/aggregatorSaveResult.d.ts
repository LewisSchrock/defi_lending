import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorSaveResultArgs {
    params: types.AggregatorSaveResultParamsFields;
}
export interface AggregatorSaveResultAccounts {
    aggregator: Address;
    oracle: Address;
    oracleAuthority: TransactionSigner;
    oracleQueue: Address;
    queueAuthority: Address;
    feedPermission: Address;
    oraclePermission: Address;
    lease: Address;
    escrow: Address;
    tokenProgram: Address;
    programState: Address;
    historyBuffer: Address;
    mint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorSaveResult(args: AggregatorSaveResultArgs, accounts: AggregatorSaveResultAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorSaveResult.d.ts.map