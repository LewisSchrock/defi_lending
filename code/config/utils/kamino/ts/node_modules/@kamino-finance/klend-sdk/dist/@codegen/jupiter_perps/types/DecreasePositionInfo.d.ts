import BN from "bn.js";
import * as types from "../types";
export interface DecreasePositionInfoFields {
    price: BN;
    liquidationPrice: BN;
    feeUsd: BN;
    collateralUsd: BN;
    hasProfit: boolean;
    pnlDelta: BN;
    transferAmountUsd: BN;
    transferToken: BN;
}
export interface DecreasePositionInfoJSON {
    price: string;
    liquidationPrice: string;
    feeUsd: string;
    collateralUsd: string;
    hasProfit: boolean;
    pnlDelta: string;
    transferAmountUsd: string;
    transferToken: string;
}
export declare class DecreasePositionInfo {
    readonly price: BN;
    readonly liquidationPrice: BN;
    readonly feeUsd: BN;
    readonly collateralUsd: BN;
    readonly hasProfit: boolean;
    readonly pnlDelta: BN;
    readonly transferAmountUsd: BN;
    readonly transferToken: BN;
    constructor(fields: DecreasePositionInfoFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.DecreasePositionInfo;
    static toEncodable(fields: DecreasePositionInfoFields): {
        price: BN;
        liquidationPrice: BN;
        feeUsd: BN;
        collateralUsd: BN;
        hasProfit: boolean;
        pnlDelta: BN;
        transferAmountUsd: BN;
        transferToken: BN;
    };
    toJSON(): DecreasePositionInfoJSON;
    static fromJSON(obj: DecreasePositionInfoJSON): DecreasePositionInfo;
    toEncodable(): {
        price: BN;
        liquidationPrice: BN;
        feeUsd: BN;
        collateralUsd: BN;
        hasProfit: boolean;
        pnlDelta: BN;
        transferAmountUsd: BN;
        transferToken: BN;
    };
}
//# sourceMappingURL=DecreasePositionInfo.d.ts.map