import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface BufferRelayerSaveResultArgs {
    params: types.BufferRelayerSaveResultParamsFields;
}
export interface BufferRelayerSaveResultAccounts {
    bufferRelayer: Address;
    oracleAuthority: TransactionSigner;
    oracle: Address;
    oracleQueue: Address;
    dataBuffer: Address;
    queueAuthority: Address;
    permission: Address;
    escrow: Address;
    oracleWallet: Address;
    programState: Address;
    tokenProgram: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function bufferRelayerSaveResult(args: BufferRelayerSaveResultArgs, accounts: BufferRelayerSaveResultAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=bufferRelayerSaveResult.d.ts.map