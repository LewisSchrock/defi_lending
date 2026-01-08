import BN from "bn.js";
import * as types from "../types";
export interface LastUpdateFields {
    /** Last slot when updated */
    slot: BN;
    /** True when marked stale, false when slot updated */
    stale: number;
    /** Status of the prices used to calculate the last update */
    priceStatus: number;
    placeholder: Array<number>;
}
export interface LastUpdateJSON {
    /** Last slot when updated */
    slot: string;
    /** True when marked stale, false when slot updated */
    stale: number;
    /** Status of the prices used to calculate the last update */
    priceStatus: number;
    placeholder: Array<number>;
}
/** Last update state */
export declare class LastUpdate {
    /** Last slot when updated */
    readonly slot: BN;
    /** True when marked stale, false when slot updated */
    readonly stale: number;
    /** Status of the prices used to calculate the last update */
    readonly priceStatus: number;
    readonly placeholder: Array<number>;
    constructor(fields: LastUpdateFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.LastUpdate;
    static toEncodable(fields: LastUpdateFields): {
        slot: BN;
        stale: number;
        priceStatus: number;
        placeholder: number[];
    };
    toJSON(): LastUpdateJSON;
    static fromJSON(obj: LastUpdateJSON): LastUpdate;
    toEncodable(): {
        slot: BN;
        stale: number;
        priceStatus: number;
        placeholder: number[];
    };
}
//# sourceMappingURL=LastUpdate.d.ts.map