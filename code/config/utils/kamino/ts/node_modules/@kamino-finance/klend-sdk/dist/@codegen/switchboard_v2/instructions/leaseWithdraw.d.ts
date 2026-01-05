import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface LeaseWithdrawArgs {
    params: types.LeaseWithdrawParamsFields;
}
export interface LeaseWithdrawAccounts {
    lease: Address;
    escrow: Address;
    aggregator: Address;
    queue: Address;
    withdrawAuthority: TransactionSigner;
    withdrawAccount: Address;
    tokenProgram: Address;
    programState: Address;
    mint: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function leaseWithdraw(args: LeaseWithdrawArgs, accounts: LeaseWithdrawAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=leaseWithdraw.d.ts.map