import BN from "bn.js";
import * as types from "../types";
export interface GetSwapAmountAndFeesParamsFields {
    amountIn: BN;
}
export interface GetSwapAmountAndFeesParamsJSON {
    amountIn: string;
}
export declare class GetSwapAmountAndFeesParams {
    readonly amountIn: BN;
    constructor(fields: GetSwapAmountAndFeesParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.GetSwapAmountAndFeesParams;
    static toEncodable(fields: GetSwapAmountAndFeesParamsFields): {
        amountIn: BN;
    };
    toJSON(): GetSwapAmountAndFeesParamsJSON;
    static fromJSON(obj: GetSwapAmountAndFeesParamsJSON): GetSwapAmountAndFeesParams;
    toEncodable(): {
        amountIn: BN;
    };
}
//# sourceMappingURL=GetSwapAmountAndFeesParams.d.ts.map