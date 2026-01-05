import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface PermissionInitArgs {
    params: types.PermissionInitParamsFields;
}
export interface PermissionInitAccounts {
    permission: Address;
    authority: Address;
    granter: Address;
    grantee: Address;
    payer: TransactionSigner;
    systemProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function permissionInit(args: PermissionInitArgs, accounts: PermissionInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=permissionInit.d.ts.map