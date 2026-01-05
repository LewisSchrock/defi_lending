import * as types from "../types";
export interface AggregatorSetUpdateIntervalParamsFields {
    newInterval: number;
}
export interface AggregatorSetUpdateIntervalParamsJSON {
    newInterval: number;
}
export declare class AggregatorSetUpdateIntervalParams {
    readonly newInterval: number;
    constructor(fields: AggregatorSetUpdateIntervalParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AggregatorSetUpdateIntervalParams;
    static toEncodable(fields: AggregatorSetUpdateIntervalParamsFields): {
        newInterval: number;
    };
    toJSON(): AggregatorSetUpdateIntervalParamsJSON;
    static fromJSON(obj: AggregatorSetUpdateIntervalParamsJSON): AggregatorSetUpdateIntervalParams;
    toEncodable(): {
        newInterval: number;
    };
}
//# sourceMappingURL=AggregatorSetUpdateIntervalParams.d.ts.map