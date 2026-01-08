import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfSetCallbackArgs {
    params: types.VrfSetCallbackParamsFields;
}
export interface VrfSetCallbackAccounts {
    vrf: Address;
    authority: TransactionSigner;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfSetCallback(args: VrfSetCallbackArgs, accounts: VrfSetCallbackAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfSetCallback.d.ts.map