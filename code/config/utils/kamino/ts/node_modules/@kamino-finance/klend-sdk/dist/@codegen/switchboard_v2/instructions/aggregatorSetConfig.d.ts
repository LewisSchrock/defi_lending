import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorSetConfigArgs {
    params: types.AggregatorSetConfigParamsFields;
}
export interface AggregatorSetConfigAccounts {
    aggregator: Address;
    authority: TransactionSigner;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorSetConfig(args: AggregatorSetConfigArgs, accounts: AggregatorSetConfigAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorSetConfig.d.ts.map