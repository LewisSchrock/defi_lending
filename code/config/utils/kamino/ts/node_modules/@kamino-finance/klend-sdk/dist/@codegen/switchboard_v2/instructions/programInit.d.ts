import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface ProgramInitArgs {
    params: types.ProgramInitParamsFields;
}
export interface ProgramInitAccounts {
    state: Address;
    authority: Address;
    tokenMint: Address;
    vault: Address;
    payer: TransactionSigner;
    systemProgram: Address;
    tokenProgram: Address;
    daoMint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function programInit(args: ProgramInitArgs, accounts: ProgramInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=programInit.d.ts.map