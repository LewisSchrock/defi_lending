import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfPoolRequestArgs {
    params: types.VrfPoolRequestParamsFields;
}
export interface VrfPoolRequestAccounts {
    authority: TransactionSigner;
    vrfPool: Address;
    escrow: Address;
    mint: Address;
    queue: Address;
    queueAuthority: Address;
    dataBuffer: Address;
    recentBlockhashes: Address;
    programState: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfPoolRequest(args: VrfPoolRequestArgs, accounts: VrfPoolRequestAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfPoolRequest.d.ts.map