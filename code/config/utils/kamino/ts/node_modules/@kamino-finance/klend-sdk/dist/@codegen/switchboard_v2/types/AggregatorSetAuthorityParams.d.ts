import * as types from "../types";
export interface AggregatorSetAuthorityParamsFields {
}
export interface AggregatorSetAuthorityParamsJSON {
}
export declare class AggregatorSetAuthorityParams {
    constructor(fields: AggregatorSetAuthorityParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AggregatorSetAuthorityParams;
    static toEncodable(fields: AggregatorSetAuthorityParamsFields): {};
    toJSON(): AggregatorSetAuthorityParamsJSON;
    static fromJSON(obj: AggregatorSetAuthorityParamsJSON): AggregatorSetAuthorityParams;
    toEncodable(): {};
}
//# sourceMappingURL=AggregatorSetAuthorityParams.d.ts.map