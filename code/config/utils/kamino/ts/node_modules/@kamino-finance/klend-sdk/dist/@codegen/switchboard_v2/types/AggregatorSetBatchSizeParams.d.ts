import * as types from "../types";
export interface AggregatorSetBatchSizeParamsFields {
    batchSize: number;
}
export interface AggregatorSetBatchSizeParamsJSON {
    batchSize: number;
}
export declare class AggregatorSetBatchSizeParams {
    readonly batchSize: number;
    constructor(fields: AggregatorSetBatchSizeParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AggregatorSetBatchSizeParams;
    static toEncodable(fields: AggregatorSetBatchSizeParamsFields): {
        batchSize: number;
    };
    toJSON(): AggregatorSetBatchSizeParamsJSON;
    static fromJSON(obj: AggregatorSetBatchSizeParamsJSON): AggregatorSetBatchSizeParams;
    toEncodable(): {
        batchSize: number;
    };
}
//# sourceMappingURL=AggregatorSetBatchSizeParams.d.ts.map