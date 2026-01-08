import BN from "bn.js";
import * as types from "../types";
export interface GetAddLiquidityAmountAndFeeParamsFields {
    tokenAmountIn: BN;
}
export interface GetAddLiquidityAmountAndFeeParamsJSON {
    tokenAmountIn: string;
}
export declare class GetAddLiquidityAmountAndFeeParams {
    readonly tokenAmountIn: BN;
    constructor(fields: GetAddLiquidityAmountAndFeeParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.GetAddLiquidityAmountAndFeeParams;
    static toEncodable(fields: GetAddLiquidityAmountAndFeeParamsFields): {
        tokenAmountIn: BN;
    };
    toJSON(): GetAddLiquidityAmountAndFeeParamsJSON;
    static fromJSON(obj: GetAddLiquidityAmountAndFeeParamsJSON): GetAddLiquidityAmountAndFeeParams;
    toEncodable(): {
        tokenAmountIn: BN;
    };
}
//# sourceMappingURL=GetAddLiquidityAmountAndFeeParams.d.ts.map