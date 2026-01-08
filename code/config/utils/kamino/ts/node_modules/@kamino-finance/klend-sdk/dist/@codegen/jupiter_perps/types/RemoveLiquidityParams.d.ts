import BN from "bn.js";
import * as types from "../types";
export interface RemoveLiquidityParamsFields {
    lpAmountIn: BN;
    minAmountOut: BN;
}
export interface RemoveLiquidityParamsJSON {
    lpAmountIn: string;
    minAmountOut: string;
}
export declare class RemoveLiquidityParams {
    readonly lpAmountIn: BN;
    readonly minAmountOut: BN;
    constructor(fields: RemoveLiquidityParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.RemoveLiquidityParams;
    static toEncodable(fields: RemoveLiquidityParamsFields): {
        lpAmountIn: BN;
        minAmountOut: BN;
    };
    toJSON(): RemoveLiquidityParamsJSON;
    static fromJSON(obj: RemoveLiquidityParamsJSON): RemoveLiquidityParams;
    toEncodable(): {
        lpAmountIn: BN;
        minAmountOut: BN;
    };
}
//# sourceMappingURL=RemoveLiquidityParams.d.ts.map