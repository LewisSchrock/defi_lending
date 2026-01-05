import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface LeaseSetAuthorityArgs {
    params: types.LeaseSetAuthorityParamsFields;
}
export interface LeaseSetAuthorityAccounts {
    lease: Address;
    withdrawAuthority: TransactionSigner;
    newAuthority: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function leaseSetAuthority(args: LeaseSetAuthorityArgs, accounts: LeaseSetAuthorityAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=leaseSetAuthority.d.ts.map