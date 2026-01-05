import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfRequestRandomnessArgs {
    params: types.VrfRequestRandomnessParamsFields;
}
export interface VrfRequestRandomnessAccounts {
    authority: TransactionSigner;
    vrf: Address;
    oracleQueue: Address;
    queueAuthority: Address;
    dataBuffer: Address;
    permission: Address;
    escrow: Address;
    payerWallet: Address;
    payerAuthority: TransactionSigner;
    recentBlockhashes: Address;
    programState: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfRequestRandomness(args: VrfRequestRandomnessArgs, accounts: VrfRequestRandomnessAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfRequestRandomness.d.ts.map