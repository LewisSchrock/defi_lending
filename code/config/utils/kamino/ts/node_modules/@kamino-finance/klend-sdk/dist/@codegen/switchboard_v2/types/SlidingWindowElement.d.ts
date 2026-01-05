import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface SlidingWindowElementFields {
    oracleKey: Address;
    value: types.SwitchboardDecimalFields;
    slot: BN;
    timestamp: BN;
}
export interface SlidingWindowElementJSON {
    oracleKey: string;
    value: types.SwitchboardDecimalJSON;
    slot: string;
    timestamp: string;
}
export declare class SlidingWindowElement {
    readonly oracleKey: Address;
    readonly value: types.SwitchboardDecimal;
    readonly slot: BN;
    readonly timestamp: BN;
    constructor(fields: SlidingWindowElementFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SlidingWindowElement;
    static toEncodable(fields: SlidingWindowElementFields): {
        oracleKey: Address;
        value: {
            mantissa: BN;
            scale: number;
        };
        slot: BN;
        timestamp: BN;
    };
    toJSON(): SlidingWindowElementJSON;
    static fromJSON(obj: SlidingWindowElementJSON): SlidingWindowElement;
    toEncodable(): {
        oracleKey: Address;
        value: {
            mantissa: BN;
            scale: number;
        };
        slot: BN;
        timestamp: BN;
    };
}
//# sourceMappingURL=SlidingWindowElement.d.ts.map