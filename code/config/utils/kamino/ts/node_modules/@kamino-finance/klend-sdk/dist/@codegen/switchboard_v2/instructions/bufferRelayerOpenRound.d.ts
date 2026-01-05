import { Address, IInstruction } from "@solana/kit";
import * as types from "../types";
export interface BufferRelayerOpenRoundArgs {
    params: types.BufferRelayerOpenRoundParamsFields;
}
export interface BufferRelayerOpenRoundAccounts {
    bufferRelayer: Address;
    oracleQueue: Address;
    dataBuffer: Address;
    permission: Address;
    escrow: Address;
    programState: Address;
}
export declare const layout: import("buffer-layout").Layout<unknown>;
export declare function bufferRelayerOpenRound(args: BufferRelayerOpenRoundArgs, accounts: BufferRelayerOpenRoundAccounts, programAddress?: Address): IInstruction;
//# sourceMappingURL=bufferRelayerOpenRound.d.ts.map