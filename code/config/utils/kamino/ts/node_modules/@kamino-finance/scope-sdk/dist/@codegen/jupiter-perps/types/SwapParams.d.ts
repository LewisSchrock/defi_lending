import BN from "bn.js";
import * as types from "../types";
export interface SwapParamsFields {
    amountIn: BN;
    minAmountOut: BN;
}
export interface SwapParamsJSON {
    amountIn: string;
    minAmountOut: string;
}
export declare class SwapParams {
    readonly amountIn: BN;
    readonly minAmountOut: BN;
    constructor(fields: SwapParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SwapParams;
    static toEncodable(fields: SwapParamsFields): {
        amountIn: BN;
        minAmountOut: BN;
    };
    toJSON(): SwapParamsJSON;
    static fromJSON(obj: SwapParamsJSON): SwapParams;
    toEncodable(): {
        amountIn: BN;
        minAmountOut: BN;
    };
}
//# sourceMappingURL=SwapParams.d.ts.map