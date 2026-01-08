import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorSetResolutionModeArgs {
    params: types.AggregatorSetResolutionModeParamsFields;
}
export interface AggregatorSetResolutionModeAccounts {
    aggregator: Address;
    authority: TransactionSigner;
    slidingWindow: Address;
    payer: TransactionSigner;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorSetResolutionMode(args: AggregatorSetResolutionModeArgs, accounts: AggregatorSetResolutionModeAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorSetResolutionMode.d.ts.map