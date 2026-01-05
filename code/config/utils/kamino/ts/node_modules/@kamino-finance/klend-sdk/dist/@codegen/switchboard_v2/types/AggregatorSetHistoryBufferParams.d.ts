import * as types from "../types";
export interface AggregatorSetHistoryBufferParamsFields {
}
export interface AggregatorSetHistoryBufferParamsJSON {
}
export declare class AggregatorSetHistoryBufferParams {
    constructor(fields: AggregatorSetHistoryBufferParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AggregatorSetHistoryBufferParams;
    static toEncodable(fields: AggregatorSetHistoryBufferParamsFields): {};
    toJSON(): AggregatorSetHistoryBufferParamsJSON;
    static fromJSON(obj: AggregatorSetHistoryBufferParamsJSON): AggregatorSetHistoryBufferParams;
    toEncodable(): {};
}
//# sourceMappingURL=AggregatorSetHistoryBufferParams.d.ts.map