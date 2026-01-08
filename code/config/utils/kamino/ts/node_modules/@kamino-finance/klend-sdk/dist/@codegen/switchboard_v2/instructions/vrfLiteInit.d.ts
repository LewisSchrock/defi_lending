import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfLiteInitArgs {
    params: types.VrfLiteInitParamsFields;
}
export interface VrfLiteInitAccounts {
    authority: Address;
    vrf: TransactionSigner;
    mint: Address;
    escrow: Address;
    queueAuthority: Address;
    queue: Address;
    permission: Address;
    programState: Address;
    payer: TransactionSigner;
    tokenProgram: Address;
    associatedTokenProgram: Address;
    systemProgram: Address;
    rent: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfLiteInit(args: VrfLiteInitArgs, accounts: VrfLiteInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfLiteInit.d.ts.map