import BN from "bn.js";
import * as types from "../types";
export interface GetRemoveLiquidityAmountAndFeeParamsFields {
    lpAmountIn: BN;
}
export interface GetRemoveLiquidityAmountAndFeeParamsJSON {
    lpAmountIn: string;
}
export declare class GetRemoveLiquidityAmountAndFeeParams {
    readonly lpAmountIn: BN;
    constructor(fields: GetRemoveLiquidityAmountAndFeeParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.GetRemoveLiquidityAmountAndFeeParams;
    static toEncodable(fields: GetRemoveLiquidityAmountAndFeeParamsFields): {
        lpAmountIn: BN;
    };
    toJSON(): GetRemoveLiquidityAmountAndFeeParamsJSON;
    static fromJSON(obj: GetRemoveLiquidityAmountAndFeeParamsJSON): GetRemoveLiquidityAmountAndFeeParams;
    toEncodable(): {
        lpAmountIn: BN;
    };
}
//# sourceMappingURL=GetRemoveLiquidityAmountAndFeeParams.d.ts.map