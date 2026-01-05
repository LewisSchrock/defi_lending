import BN from "bn.js";
import * as types from "../types";
export interface GetExactOutSwapAmountAndFeesParamsFields {
    amountOut: BN;
}
export interface GetExactOutSwapAmountAndFeesParamsJSON {
    amountOut: string;
}
export declare class GetExactOutSwapAmountAndFeesParams {
    readonly amountOut: BN;
    constructor(fields: GetExactOutSwapAmountAndFeesParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.GetExactOutSwapAmountAndFeesParams;
    static toEncodable(fields: GetExactOutSwapAmountAndFeesParamsFields): {
        amountOut: BN;
    };
    toJSON(): GetExactOutSwapAmountAndFeesParamsJSON;
    static fromJSON(obj: GetExactOutSwapAmountAndFeesParamsJSON): GetExactOutSwapAmountAndFeesParams;
    toEncodable(): {
        amountOut: BN;
    };
}
//# sourceMappingURL=GetExactOutSwapAmountAndFeesParams.d.ts.map