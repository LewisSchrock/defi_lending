import * as types from "../types";
export interface GetLiquidationStateParamsFields {
}
export interface GetLiquidationStateParamsJSON {
}
export declare class GetLiquidationStateParams {
    constructor(fields: GetLiquidationStateParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.GetLiquidationStateParams;
    static toEncodable(fields: GetLiquidationStateParamsFields): {};
    toJSON(): GetLiquidationStateParamsJSON;
    static fromJSON(obj: GetLiquidationStateParamsJSON): GetLiquidationStateParams;
    toEncodable(): {};
}
//# sourceMappingURL=GetLiquidationStateParams.d.ts.map