import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface CrankRowFields {
    pubkey: Address;
    nextTimestamp: BN;
}
export interface CrankRowJSON {
    pubkey: string;
    nextTimestamp: string;
}
export declare class CrankRow {
    readonly pubkey: Address;
    readonly nextTimestamp: BN;
    constructor(fields: CrankRowFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.CrankRow;
    static toEncodable(fields: CrankRowFields): {
        pubkey: Address;
        nextTimestamp: BN;
    };
    toJSON(): CrankRowJSON;
    static fromJSON(obj: CrankRowJSON): CrankRow;
    toEncodable(): {
        pubkey: Address;
        nextTimestamp: BN;
    };
}
//# sourceMappingURL=CrankRow.d.ts.map