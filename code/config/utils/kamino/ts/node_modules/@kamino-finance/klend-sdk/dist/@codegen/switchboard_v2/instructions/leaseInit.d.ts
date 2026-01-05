import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface LeaseInitArgs {
    params: types.LeaseInitParamsFields;
}
export interface LeaseInitAccounts {
    lease: Address;
    queue: Address;
    aggregator: Address;
    funder: Address;
    payer: TransactionSigner;
    systemProgram: Address;
    tokenProgram: Address;
    owner: TransactionSigner;
    escrow: Address;
    programState: Address;
    mint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function leaseInit(args: LeaseInitArgs, accounts: LeaseInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=leaseInit.d.ts.map