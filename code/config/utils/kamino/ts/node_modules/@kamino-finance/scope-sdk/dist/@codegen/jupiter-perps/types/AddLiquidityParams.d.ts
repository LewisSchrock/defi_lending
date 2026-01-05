import BN from "bn.js";
import * as types from "../types";
export interface AddLiquidityParamsFields {
    tokenAmountIn: BN;
    minLpAmountOut: BN;
    tokenAmountPreSwap: BN | null;
}
export interface AddLiquidityParamsJSON {
    tokenAmountIn: string;
    minLpAmountOut: string;
    tokenAmountPreSwap: string | null;
}
export declare class AddLiquidityParams {
    readonly tokenAmountIn: BN;
    readonly minLpAmountOut: BN;
    readonly tokenAmountPreSwap: BN | null;
    constructor(fields: AddLiquidityParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AddLiquidityParams;
    static toEncodable(fields: AddLiquidityParamsFields): {
        tokenAmountIn: BN;
        minLpAmountOut: BN;
        tokenAmountPreSwap: BN | null;
    };
    toJSON(): AddLiquidityParamsJSON;
    static fromJSON(obj: AddLiquidityParamsJSON): AddLiquidityParams;
    toEncodable(): {
        tokenAmountIn: BN;
        minLpAmountOut: BN;
        tokenAmountPreSwap: BN | null;
    };
}
//# sourceMappingURL=AddLiquidityParams.d.ts.map