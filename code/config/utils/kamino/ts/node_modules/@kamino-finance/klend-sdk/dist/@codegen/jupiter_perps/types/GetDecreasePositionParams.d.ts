import BN from "bn.js";
import * as types from "../types";
export interface GetDecreasePositionParamsFields {
    collateralUsdDelta: BN;
    sizeUsdDelta: BN;
}
export interface GetDecreasePositionParamsJSON {
    collateralUsdDelta: string;
    sizeUsdDelta: string;
}
export declare class GetDecreasePositionParams {
    readonly collateralUsdDelta: BN;
    readonly sizeUsdDelta: BN;
    constructor(fields: GetDecreasePositionParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.GetDecreasePositionParams;
    static toEncodable(fields: GetDecreasePositionParamsFields): {
        collateralUsdDelta: BN;
        sizeUsdDelta: BN;
    };
    toJSON(): GetDecreasePositionParamsJSON;
    static fromJSON(obj: GetDecreasePositionParamsJSON): GetDecreasePositionParams;
    toEncodable(): {
        collateralUsdDelta: BN;
        sizeUsdDelta: BN;
    };
}
//# sourceMappingURL=GetDecreasePositionParams.d.ts.map