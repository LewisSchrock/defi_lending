import BN from "bn.js";
import * as types from "../types";
export interface AggregatorHistoryRowFields {
    timestamp: BN;
    value: types.SwitchboardDecimalFields;
}
export interface AggregatorHistoryRowJSON {
    timestamp: string;
    value: types.SwitchboardDecimalJSON;
}
export declare class AggregatorHistoryRow {
    readonly timestamp: BN;
    readonly value: types.SwitchboardDecimal;
    constructor(fields: AggregatorHistoryRowFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AggregatorHistoryRow;
    static toEncodable(fields: AggregatorHistoryRowFields): {
        timestamp: BN;
        value: {
            mantissa: BN;
            scale: number;
        };
    };
    toJSON(): AggregatorHistoryRowJSON;
    static fromJSON(obj: AggregatorHistoryRowJSON): AggregatorHistoryRow;
    toEncodable(): {
        timestamp: BN;
        value: {
            mantissa: BN;
            scale: number;
        };
    };
}
//# sourceMappingURL=AggregatorHistoryRow.d.ts.map