import BN from "bn.js";
import * as types from "../types";
export interface SwapAmountAndFeesFields {
    amountIn: BN;
    amountOut: BN;
    feeBps: BN;
    feeToken: BN;
}
export interface SwapAmountAndFeesJSON {
    amountIn: string;
    amountOut: string;
    feeBps: string;
    feeToken: string;
}
export declare class SwapAmountAndFees {
    readonly amountIn: BN;
    readonly amountOut: BN;
    readonly feeBps: BN;
    readonly feeToken: BN;
    constructor(fields: SwapAmountAndFeesFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SwapAmountAndFees;
    static toEncodable(fields: SwapAmountAndFeesFields): {
        amountIn: BN;
        amountOut: BN;
        feeBps: BN;
        feeToken: BN;
    };
    toJSON(): SwapAmountAndFeesJSON;
    static fromJSON(obj: SwapAmountAndFeesJSON): SwapAmountAndFees;
    toEncodable(): {
        amountIn: BN;
        amountOut: BN;
        feeBps: BN;
        feeToken: BN;
    };
}
//# sourceMappingURL=SwapAmountAndFees.d.ts.map