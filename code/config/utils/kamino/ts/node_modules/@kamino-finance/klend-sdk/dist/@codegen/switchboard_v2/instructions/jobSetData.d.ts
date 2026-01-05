import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface JobSetDataArgs {
    params: types.JobSetDataParamsFields;
}
export interface JobSetDataAccounts {
    job: Address;
    authority: TransactionSigner;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function jobSetData(args: JobSetDataArgs, accounts: JobSetDataAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=jobSetData.d.ts.map