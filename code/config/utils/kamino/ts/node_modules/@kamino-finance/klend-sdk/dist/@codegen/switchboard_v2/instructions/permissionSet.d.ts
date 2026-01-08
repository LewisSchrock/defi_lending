import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface PermissionSetArgs {
    params: types.PermissionSetParamsFields;
}
export interface PermissionSetAccounts {
    permission: Address;
    authority: TransactionSigner;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function permissionSet(args: PermissionSetArgs, accounts: PermissionSetAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=permissionSet.d.ts.map