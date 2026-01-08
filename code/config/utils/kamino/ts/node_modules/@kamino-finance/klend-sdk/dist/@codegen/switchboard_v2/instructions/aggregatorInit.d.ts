import { Address, IInstruction } from "@solana/kit";
import * as types from "../types";
export interface AggregatorInitArgs {
    params: types.AggregatorInitParamsFields;
}
export interface AggregatorInitAccounts {
    aggregator: Address;
    authority: Address;
    queue: Address;
    programState: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorInit(args: AggregatorInitArgs, accounts: AggregatorInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorInit.d.ts.map