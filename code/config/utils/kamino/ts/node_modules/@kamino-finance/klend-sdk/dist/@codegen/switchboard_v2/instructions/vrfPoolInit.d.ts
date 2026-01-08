import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfPoolInitArgs {
    params: types.VrfPoolInitParamsFields;
}
export interface VrfPoolInitAccounts {
    authority: Address;
    vrfPool: Address;
    queue: Address;
    mint: Address;
    escrow: Address;
    programState: Address;
    payer: TransactionSigner;
    tokenProgram: Address;
    associatedTokenProgram: Address;
    systemProgram: Address;
    rent: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfPoolInit(args: VrfPoolInitArgs, accounts: VrfPoolInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfPoolInit.d.ts.map