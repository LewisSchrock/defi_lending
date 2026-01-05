import BN from "bn.js";
import * as types from "../types";
export interface AmountAndFeeFields {
    amount: BN;
    fee: BN;
    feeBps: BN;
}
export interface AmountAndFeeJSON {
    amount: string;
    fee: string;
    feeBps: string;
}
export declare class AmountAndFee {
    readonly amount: BN;
    readonly fee: BN;
    readonly feeBps: BN;
    constructor(fields: AmountAndFeeFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AmountAndFee;
    static toEncodable(fields: AmountAndFeeFields): {
        amount: BN;
        fee: BN;
        feeBps: BN;
    };
    toJSON(): AmountAndFeeJSON;
    static fromJSON(obj: AmountAndFeeJSON): AmountAndFee;
    toEncodable(): {
        amount: BN;
        fee: BN;
        feeBps: BN;
    };
}
//# sourceMappingURL=AmountAndFee.d.ts.map