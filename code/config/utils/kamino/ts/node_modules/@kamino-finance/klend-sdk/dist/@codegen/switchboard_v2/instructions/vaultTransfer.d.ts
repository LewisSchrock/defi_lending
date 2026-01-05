import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VaultTransferArgs {
    params: types.VaultTransferParamsFields;
}
export interface VaultTransferAccounts {
    state: Address;
    authority: TransactionSigner;
    to: Address;
    vault: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vaultTransfer(args: VaultTransferArgs, accounts: VaultTransferAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vaultTransfer.d.ts.map