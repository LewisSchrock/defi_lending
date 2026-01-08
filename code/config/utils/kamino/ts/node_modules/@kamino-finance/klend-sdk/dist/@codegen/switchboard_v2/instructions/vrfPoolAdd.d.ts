import { Address, IInstruction } from "@solana/kit";
import * as types from "../types";
export interface VrfPoolAddArgs {
    params: types.VrfPoolAddParamsFields;
}
export interface VrfPoolAddAccounts {
    authority: Address;
    vrfPool: Address;
    vrfLite: Address;
    queue: Address;
    permission: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfPoolAdd(args: VrfPoolAddArgs, accounts: VrfPoolAddAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfPoolAdd.d.ts.map