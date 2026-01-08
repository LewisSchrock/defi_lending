import { Address, IInstruction } from "@solana/kit";
import * as types from "../types";
export interface VrfInitArgs {
    params: types.VrfInitParamsFields;
}
export interface VrfInitAccounts {
    vrf: Address;
    authority: Address;
    oracleQueue: Address;
    escrow: Address;
    programState: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfInit(args: VrfInitArgs, accounts: VrfInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfInit.d.ts.map