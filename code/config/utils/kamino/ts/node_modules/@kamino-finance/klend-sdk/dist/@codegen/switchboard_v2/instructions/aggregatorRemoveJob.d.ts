import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorRemoveJobArgs {
    params: types.AggregatorRemoveJobParamsFields;
}
export interface AggregatorRemoveJobAccounts {
    aggregator: Address;
    authority: TransactionSigner;
    job: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorRemoveJob(args: AggregatorRemoveJobArgs, accounts: AggregatorRemoveJobAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorRemoveJob.d.ts.map