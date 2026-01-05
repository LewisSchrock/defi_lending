import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface AggregatorRoundFields {
    numSuccess: number;
    numError: number;
    isClosed: boolean;
    roundOpenSlot: BN;
    roundOpenTimestamp: BN;
    result: types.SwitchboardDecimalFields;
    stdDeviation: types.SwitchboardDecimalFields;
    minResponse: types.SwitchboardDecimalFields;
    maxResponse: types.SwitchboardDecimalFields;
    oraclePubkeysData: Array<Address>;
    mediansData: Array<types.SwitchboardDecimalFields>;
    currentPayout: Array<BN>;
    mediansFulfilled: Array<boolean>;
    errorsFulfilled: Array<boolean>;
}
export interface AggregatorRoundJSON {
    numSuccess: number;
    numError: number;
    isClosed: boolean;
    roundOpenSlot: string;
    roundOpenTimestamp: string;
    result: types.SwitchboardDecimalJSON;
    stdDeviation: types.SwitchboardDecimalJSON;
    minResponse: types.SwitchboardDecimalJSON;
    maxResponse: types.SwitchboardDecimalJSON;
    oraclePubkeysData: Array<string>;
    mediansData: Array<types.SwitchboardDecimalJSON>;
    currentPayout: Array<string>;
    mediansFulfilled: Array<boolean>;
    errorsFulfilled: Array<boolean>;
}
export declare class AggregatorRound {
    readonly numSuccess: number;
    readonly numError: number;
    readonly isClosed: boolean;
    readonly roundOpenSlot: BN;
    readonly roundOpenTimestamp: BN;
    readonly result: types.SwitchboardDecimal;
    readonly stdDeviation: types.SwitchboardDecimal;
    readonly minResponse: types.SwitchboardDecimal;
    readonly maxResponse: types.SwitchboardDecimal;
    readonly oraclePubkeysData: Array<Address>;
    readonly mediansData: Array<types.SwitchboardDecimal>;
    readonly currentPayout: Array<BN>;
    readonly mediansFulfilled: Array<boolean>;
    readonly errorsFulfilled: Array<boolean>;
    constructor(fields: AggregatorRoundFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AggregatorRound;
    static toEncodable(fields: AggregatorRoundFields): {
        numSuccess: number;
        numError: number;
        isClosed: boolean;
        roundOpenSlot: BN;
        roundOpenTimestamp: BN;
        result: {
            mantissa: BN;
            scale: number;
        };
        stdDeviation: {
            mantissa: BN;
            scale: number;
        };
        minResponse: {
            mantissa: BN;
            scale: number;
        };
        maxResponse: {
            mantissa: BN;
            scale: number;
        };
        oraclePubkeysData: Address[];
        mediansData: {
            mantissa: BN;
            scale: number;
        }[];
        currentPayout: BN[];
        mediansFulfilled: boolean[];
        errorsFulfilled: boolean[];
    };
    toJSON(): AggregatorRoundJSON;
    static fromJSON(obj: AggregatorRoundJSON): AggregatorRound;
    toEncodable(): {
        numSuccess: number;
        numError: number;
        isClosed: boolean;
        roundOpenSlot: BN;
        roundOpenTimestamp: BN;
        result: {
            mantissa: BN;
            scale: number;
        };
        stdDeviation: {
            mantissa: BN;
            scale: number;
        };
        minResponse: {
            mantissa: BN;
            scale: number;
        };
        maxResponse: {
            mantissa: BN;
            scale: number;
        };
        oraclePubkeysData: Address[];
        mediansData: {
            mantissa: BN;
            scale: number;
        }[];
        currentPayout: BN[];
        mediansFulfilled: boolean[];
        errorsFulfilled: boolean[];
    };
}
//# sourceMappingURL=AggregatorRound.d.ts.map