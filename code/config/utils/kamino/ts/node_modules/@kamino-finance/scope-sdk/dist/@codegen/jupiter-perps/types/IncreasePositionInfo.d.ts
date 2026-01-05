import BN from "bn.js";
import * as types from "../types";
export interface IncreasePositionInfoFields {
    price: BN;
    liquidationPrice: BN;
    feeUsd: BN;
    collateralUsd: BN;
}
export interface IncreasePositionInfoJSON {
    price: string;
    liquidationPrice: string;
    feeUsd: string;
    collateralUsd: string;
}
export declare class IncreasePositionInfo {
    readonly price: BN;
    readonly liquidationPrice: BN;
    readonly feeUsd: BN;
    readonly collateralUsd: BN;
    constructor(fields: IncreasePositionInfoFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.IncreasePositionInfo;
    static toEncodable(fields: IncreasePositionInfoFields): {
        price: BN;
        liquidationPrice: BN;
        feeUsd: BN;
        collateralUsd: BN;
    };
    toJSON(): IncreasePositionInfoJSON;
    static fromJSON(obj: IncreasePositionInfoJSON): IncreasePositionInfo;
    toEncodable(): {
        price: BN;
        liquidationPrice: BN;
        feeUsd: BN;
        collateralUsd: BN;
    };
}
//# sourceMappingURL=IncreasePositionInfo.d.ts.map