import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorSaveResultV2Args {
    params: types.AggregatorSaveResultParamsFields;
}
export interface AggregatorSaveResultV2Accounts {
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
export declare function aggregatorSaveResultV2(args: AggregatorSaveResultV2Args, accounts: AggregatorSaveResultV2Accounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorSaveResultV2.d.ts.map