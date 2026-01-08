import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface VrfLiteProveAndVerifyArgs {
    params: types.VrfLiteProveAndVerifyParamsFields;
}
export interface VrfLiteProveAndVerifyAccounts {
    vrfLite: Address;
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
export declare function vrfLiteProveAndVerify(args: VrfLiteProveAndVerifyArgs, accounts: VrfLiteProveAndVerifyAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=vrfLiteProveAndVerify.d.ts.map