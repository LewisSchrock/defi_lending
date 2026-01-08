import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface BufferRelayerRoundFields {
    numSuccess: number;
    numError: number;
    roundOpenSlot: BN;
    roundOpenTimestamp: BN;
    oraclePubkey: Address;
}
export interface BufferRelayerRoundJSON {
    numSuccess: number;
    numError: number;
    roundOpenSlot: string;
    roundOpenTimestamp: string;
    oraclePubkey: string;
}
export declare class BufferRelayerRound {
    readonly numSuccess: number;
    readonly numError: number;
    readonly roundOpenSlot: BN;
    readonly roundOpenTimestamp: BN;
    readonly oraclePubkey: Address;
    constructor(fields: BufferRelayerRoundFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.BufferRelayerRound;
    static toEncodable(fields: BufferRelayerRoundFields): {
        numSuccess: number;
        numError: number;
        roundOpenSlot: BN;
        roundOpenTimestamp: BN;
        oraclePubkey: Address;
    };
    toJSON(): BufferRelayerRoundJSON;
    static fromJSON(obj: BufferRelayerRoundJSON): BufferRelayerRound;
    toEncodable(): {
        numSuccess: number;
        numError: number;
        roundOpenSlot: BN;
        roundOpenTimestamp: BN;
        oraclePubkey: Address;
    };
}
//# sourceMappingURL=BufferRelayerRound.d.ts.map