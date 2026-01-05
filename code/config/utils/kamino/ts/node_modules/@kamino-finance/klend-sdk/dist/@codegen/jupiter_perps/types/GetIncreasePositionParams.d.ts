import BN from "bn.js";
import * as types from "../types";
export interface GetIncreasePositionParamsFields {
    collateralTokenDelta: BN;
    sizeUsdDelta: BN;
    side: types.SideKind;
}
export interface GetIncreasePositionParamsJSON {
    collateralTokenDelta: string;
    sizeUsdDelta: string;
    side: types.SideJSON;
}
export declare class GetIncreasePositionParams {
    readonly collateralTokenDelta: BN;
    readonly sizeUsdDelta: BN;
    readonly side: types.SideKind;
    constructor(fields: GetIncreasePositionParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.GetIncreasePositionParams;
    static toEncodable(fields: GetIncreasePositionParamsFields): {
        collateralTokenDelta: BN;
        sizeUsdDelta: BN;
        side: {
            None: {};
        } | {
            Long: {};
        } | {
            Short: {};
        };
    };
    toJSON(): GetIncreasePositionParamsJSON;
    static fromJSON(obj: GetIncreasePositionParamsJSON): GetIncreasePositionParams;
    toEncodable(): {
        collateralTokenDelta: BN;
        sizeUsdDelta: BN;
        side: {
            None: {};
        } | {
            Long: {};
        } | {
            Short: {};
        };
    };
}
//# sourceMappingURL=GetIncreasePositionParams.d.ts.map