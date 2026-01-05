import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorLockArgs {
    params: types.AggregatorLockParamsFields;
}
export interface AggregatorLockAccounts {
    aggregator: Address;
    authority: TransactionSigner;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorLock(args: AggregatorLockArgs, accounts: AggregatorLockAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorLock.d.ts.map