import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface LeaseExtendArgs {
    params: types.LeaseExtendParamsFields;
}
export interface LeaseExtendAccounts {
    lease: Address;
    aggregator: Address;
    queue: Address;
    funder: Address;
    owner: TransactionSigner;
    escrow: Address;
    tokenProgram: Address;
    programState: Address;
    mint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function leaseExtend(args: LeaseExtendArgs, accounts: LeaseExtendAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=leaseExtend.d.ts.map