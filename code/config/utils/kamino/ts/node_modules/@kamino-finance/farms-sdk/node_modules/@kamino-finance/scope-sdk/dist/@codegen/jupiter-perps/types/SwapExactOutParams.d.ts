import BN from "bn.js";
import * as types from "../types";
export interface SwapExactOutParamsFields {
    amountOut: BN;
    maxAmountIn: BN;
}
export interface SwapExactOutParamsJSON {
    amountOut: string;
    maxAmountIn: string;
}
export declare class SwapExactOutParams {
    readonly amountOut: BN;
    readonly maxAmountIn: BN;
    constructor(fields: SwapExactOutParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SwapExactOutParams;
    static toEncodable(fields: SwapExactOutParamsFields): {
        amountOut: BN;
        maxAmountIn: BN;
    };
    toJSON(): SwapExactOutParamsJSON;
    static fromJSON(obj: SwapExactOutParamsJSON): SwapExactOutParams;
    toEncodable(): {
        amountOut: BN;
        maxAmountIn: BN;
    };
}
//# sourceMappingURL=SwapExactOutParams.d.ts.map