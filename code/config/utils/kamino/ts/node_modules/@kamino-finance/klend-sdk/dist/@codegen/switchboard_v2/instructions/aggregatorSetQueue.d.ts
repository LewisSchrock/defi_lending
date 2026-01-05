import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorSetQueueArgs {
    params: types.AggregatorSetQueueParamsFields;
}
export interface AggregatorSetQueueAccounts {
    aggregator: Address;
    authority: TransactionSigner;
    queue: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorSetQueue(args: AggregatorSetQueueArgs, accounts: AggregatorSetQueueAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorSetQueue.d.ts.map