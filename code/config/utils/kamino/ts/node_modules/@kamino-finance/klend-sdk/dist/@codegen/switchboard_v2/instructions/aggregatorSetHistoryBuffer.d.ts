import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorSetHistoryBufferArgs {
    params: types.AggregatorSetHistoryBufferParamsFields;
}
export interface AggregatorSetHistoryBufferAccounts {
    aggregator: Address;
    authority: TransactionSigner;
    buffer: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorSetHistoryBuffer(args: AggregatorSetHistoryBufferArgs, accounts: AggregatorSetHistoryBufferAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorSetHistoryBuffer.d.ts.map