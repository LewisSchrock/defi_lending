import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface CrankInitArgs {
    params: types.CrankInitParamsFields;
}
export interface CrankInitAccounts {
    crank: TransactionSigner;
    queue: Address;
    buffer: Address;
    payer: TransactionSigner;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function crankInit(args: CrankInitArgs, accounts: CrankInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=crankInit.d.ts.map