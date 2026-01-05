import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface VrfPoolRowFields {
    timestamp: BN;
    pubkey: Address;
}
export interface VrfPoolRowJSON {
    timestamp: string;
    pubkey: string;
}
export declare class VrfPoolRow {
    readonly timestamp: BN;
    readonly pubkey: Address;
    constructor(fields: VrfPoolRowFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfPoolRow;
    static toEncodable(fields: VrfPoolRowFields): {
        timestamp: BN;
        pubkey: Address;
    };
    toJSON(): VrfPoolRowJSON;
    static fromJSON(obj: VrfPoolRowJSON): VrfPoolRow;
    toEncodable(): {
        timestamp: BN;
        pubkey: Address;
    };
}
//# sourceMappingURL=VrfPoolRow.d.ts.map