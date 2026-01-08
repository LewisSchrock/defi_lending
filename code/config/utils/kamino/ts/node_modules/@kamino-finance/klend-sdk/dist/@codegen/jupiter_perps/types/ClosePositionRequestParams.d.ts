import * as types from "../types";
export interface ClosePositionRequestParamsFields {
}
export interface ClosePositionRequestParamsJSON {
}
export declare class ClosePositionRequestParams {
    constructor(fields: ClosePositionRequestParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.ClosePositionRequestParams;
    static toEncodable(fields: ClosePositionRequestParamsFields): {};
    toJSON(): ClosePositionRequestParamsJSON;
    static fromJSON(obj: ClosePositionRequestParamsJSON): ClosePositionRequestParams;
    toEncodable(): {};
}
//# sourceMappingURL=ClosePositionRequestParams.d.ts.map