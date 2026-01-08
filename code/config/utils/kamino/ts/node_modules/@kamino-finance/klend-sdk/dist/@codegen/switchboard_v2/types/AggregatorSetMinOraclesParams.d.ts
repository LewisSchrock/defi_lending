import * as types from "../types";
export interface AggregatorSetMinOraclesParamsFields {
    minOracleResults: number;
}
export interface AggregatorSetMinOraclesParamsJSON {
    minOracleResults: number;
}
export declare class AggregatorSetMinOraclesParams {
    readonly minOracleResults: number;
    constructor(fields: AggregatorSetMinOraclesParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AggregatorSetMinOraclesParams;
    static toEncodable(fields: AggregatorSetMinOraclesParamsFields): {
        minOracleResults: number;
    };
    toJSON(): AggregatorSetMinOraclesParamsJSON;
    static fromJSON(obj: AggregatorSetMinOraclesParamsJSON): AggregatorSetMinOraclesParams;
    toEncodable(): {
        minOracleResults: number;
    };
}
//# sourceMappingURL=AggregatorSetMinOraclesParams.d.ts.map