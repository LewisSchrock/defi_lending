import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface JobInitArgs {
    params: types.JobInitParamsFields;
}
export interface JobInitAccounts {
    job: TransactionSigner;
    authority: TransactionSigner;
    programState: Address;
    payer: TransactionSigner;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function jobInit(args: JobInitArgs, accounts: JobInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=jobInit.d.ts.map