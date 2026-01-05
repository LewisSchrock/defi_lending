import { Address, IInstruction, TransactionSigner } from "@solana/kit";
import * as types from "../types";
export interface BufferRelayerInitArgs {
    params: types.BufferRelayerInitParamsFields;
}
export interface BufferRelayerInitAccounts {
    bufferRelayer: Address;
    escrow: Address;
    authority: Address;
    queue: Address;
    job: Address;
    programState: Address;
    mint: Address;
    payer: TransactionSigner;
    tokenProgram: Address;
    associatedTokenProgram: Address;
    systemProgram: Address;
    rent: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function bufferRelayerInit(args: BufferRelayerInitArgs, accounts: BufferRelayerInitAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=bufferRelayerInit.d.ts.map