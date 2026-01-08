import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import * as types from "../types";
export interface BufferRelayerAccountDataFields {
    name: Array<number>;
    queuePubkey: Address;
    escrow: Address;
    authority: Address;
    jobPubkey: Address;
    jobHash: Array<number>;
    minUpdateDelaySeconds: number;
    isLocked: boolean;
    currentRound: types.BufferRelayerRoundFields;
    latestConfirmedRound: types.BufferRelayerRoundFields;
    result: Uint8Array;
}
export interface BufferRelayerAccountDataJSON {
    name: Array<number>;
    queuePubkey: string;
    escrow: string;
    authority: string;
    jobPubkey: string;
    jobHash: Array<number>;
    minUpdateDelaySeconds: number;
    isLocked: boolean;
    currentRound: types.BufferRelayerRoundJSON;
    latestConfirmedRound: types.BufferRelayerRoundJSON;
    result: Array<number>;
}
export declare class BufferRelayerAccountData {
    readonly name: Array<number>;
    readonly queuePubkey: Address;
    readonly escrow: Address;
    readonly authority: Address;
    readonly jobPubkey: Address;
    readonly jobHash: Array<number>;
    readonly minUpdateDelaySeconds: number;
    readonly isLocked: boolean;
    readonly currentRound: types.BufferRelayerRound;
    readonly latestConfirmedRound: types.BufferRelayerRound;
    readonly result: Uint8Array;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<BufferRelayerAccountData>;
    constructor(fields: BufferRelayerAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<BufferRelayerAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<BufferRelayerAccountData | null>>;
    static decode(data: Buffer): BufferRelayerAccountData;
    toJSON(): BufferRelayerAccountDataJSON;
    static fromJSON(obj: BufferRelayerAccountDataJSON): BufferRelayerAccountData;
}
//# sourceMappingURL=BufferRelayerAccountData.d.ts.map