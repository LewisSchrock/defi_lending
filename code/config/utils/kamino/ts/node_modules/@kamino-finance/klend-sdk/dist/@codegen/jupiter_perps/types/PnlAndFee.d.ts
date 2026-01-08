import BN from "bn.js";
import * as types from "../types";
export interface PnlAndFeeFields {
    hasProfit: boolean;
    pnlDelta: BN;
    openPositionFeeUsd: BN;
    closePositionFeeUsd: BN;
    fundingFeeUsd: BN;
    liquidationPrice: BN;
}
export interface PnlAndFeeJSON {
    hasProfit: boolean;
    pnlDelta: string;
    openPositionFeeUsd: string;
    closePositionFeeUsd: string;
    fundingFeeUsd: string;
    liquidationPrice: string;
}
export declare class PnlAndFee {
    readonly hasProfit: boolean;
    readonly pnlDelta: BN;
    readonly openPositionFeeUsd: BN;
    readonly closePositionFeeUsd: BN;
    readonly fundingFeeUsd: BN;
    readonly liquidationPrice: BN;
    constructor(fields: PnlAndFeeFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PnlAndFee;
    static toEncodable(fields: PnlAndFeeFields): {
        hasProfit: boolean;
        pnlDelta: BN;
        openPositionFeeUsd: BN;
        closePositionFeeUsd: BN;
        fundingFeeUsd: BN;
        liquidationPrice: BN;
    };
    toJSON(): PnlAndFeeJSON;
    static fromJSON(obj: PnlAndFeeJSON): PnlAndFee;
    toEncodable(): {
        hasProfit: boolean;
        pnlDelta: BN;
        openPositionFeeUsd: BN;
        closePositionFeeUsd: BN;
        fundingFeeUsd: BN;
        liquidationPrice: BN;
    };
}
//# sourceMappingURL=PnlAndFee.d.ts.map