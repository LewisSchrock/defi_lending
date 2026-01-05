import * as types from "../types";
export interface GetPnlAndFeeParamsFields {
}
export interface GetPnlAndFeeParamsJSON {
}
export declare class GetPnlAndFeeParams {
    constructor(fields: GetPnlAndFeeParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.GetPnlAndFeeParams;
    static toEncodable(fields: GetPnlAndFeeParamsFields): {};
    toJSON(): GetPnlAndFeeParamsJSON;
    static fromJSON(obj: GetPnlAndFeeParamsJSON): GetPnlAndFeeParams;
    toEncodable(): {};
}
//# sourceMappingURL=GetPnlAndFeeParams.d.ts.map