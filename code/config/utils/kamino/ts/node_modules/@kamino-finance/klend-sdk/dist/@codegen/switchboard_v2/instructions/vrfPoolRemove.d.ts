import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfPoolRemoveArgs {
    params: types.VrfPoolRemoveParamsFields;
}
export interface VrfPoolRemoveAccounts {
    authority: TransactionSigner;
    vrfPool: Address;
    queue: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfPoolRemove(args: VrfPoolRemoveArgs, accounts: VrfPoolRemoveAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfPoolRemove.d.ts.map