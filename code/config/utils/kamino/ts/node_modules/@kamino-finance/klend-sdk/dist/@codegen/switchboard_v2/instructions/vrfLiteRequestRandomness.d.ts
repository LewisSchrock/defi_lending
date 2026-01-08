import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfLiteRequestRandomnessArgs {
    params: types.VrfLiteRequestRandomnessParamsFields;
}
export interface VrfLiteRequestRandomnessAccounts {
    authority: TransactionSigner;
    vrfLite: Address;
    queue: Address;
    queueAuthority: Address;
    dataBuffer: Address;
    permission: Address;
    escrow: Address;
    recentBlockhashes: Address;
    programState: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfLiteRequestRandomness(args: VrfLiteRequestRandomnessArgs, accounts: VrfLiteRequestRandomnessAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfLiteRequestRandomness.d.ts.map