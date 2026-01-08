import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface AggregatorAddJobArgs {
    params: types.AggregatorAddJobParamsFields;
}
export interface AggregatorAddJobAccounts {
    aggregator: Address;
    authority: TransactionSigner;
    job: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function aggregatorAddJob(args: AggregatorAddJobArgs, accounts: AggregatorAddJobAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=aggregatorAddJob.d.ts.map