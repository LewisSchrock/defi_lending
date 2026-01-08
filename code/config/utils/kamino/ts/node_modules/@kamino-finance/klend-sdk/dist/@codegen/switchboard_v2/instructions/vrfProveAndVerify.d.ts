import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfProveAndVerifyArgs {
    params: types.VrfProveAndVerifyParamsFields;
}
export interface VrfProveAndVerifyAccounts {
    vrf: Address;
    callbackPid: Address;
    tokenProgram: Address;
    escrow: Address;
    programState: Address;
    oracle: Address;
    oracleAuthority: TransactionSigner;
    oracleWallet: Address;
    instructionsSysvar: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function vrfProveAndVerify(args: VrfProveAndVerifyArgs, accounts: VrfProveAndVerifyAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfProveAndVerify.d.ts.map