import BN from "bn.js";
import * as types from "../types";
export interface CreateIncreasePositionRequestParamsFields {
    sizeUsdDelta: BN;
    collateralTokenDelta: BN;
    side: types.SideKind;
    requestType: types.RequestTypeKind;
    priceSlippage: BN | null;
    jupiterMinimumOut: BN | null;
    triggerPrice: BN | null;
    triggerAboveThreshold: boolean | null;
    counter: BN;
}
export interface CreateIncreasePositionRequestParamsJSON {
    sizeUsdDelta: string;
    collateralTokenDelta: string;
    side: types.SideJSON;
    requestType: types.RequestTypeJSON;
    priceSlippage: string | null;
    jupiterMinimumOut: string | null;
    triggerPrice: string | null;
    triggerAboveThreshold: boolean | null;
    counter: string;
}
export declare class CreateIncreasePositionRequestParams {
    readonly sizeUsdDelta: BN;
    readonly collateralTokenDelta: BN;
    readonly side: types.SideKind;
    readonly requestType: types.RequestTypeKind;
    readonly priceSlippage: BN | null;
    readonly jupiterMinimumOut: BN | null;
    readonly triggerPrice: BN | null;
    readonly triggerAboveThreshold: boolean | null;
    readonly counter: BN;
    constructor(fields: CreateIncreasePositionRequestParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.CreateIncreasePositionRequestParams;
    static toEncodable(fields: CreateIncreasePositionRequestParamsFields): {
        sizeUsdDelta: BN;
        collateralTokenDelta: BN;
        side: {
            None: {};
        } | {
            Long: {};
        } | {
            Short: {};
        };
        requestType: {
            Market: {};
        } | {
            Trigger: {};
        };
        priceSlippage: BN | null;
        jupiterMinimumOut: BN | null;
        triggerPrice: BN | null;
        triggerAboveThreshold: boolean | null;
        counter: BN;
    };
    toJSON(): CreateIncreasePositionRequestParamsJSON;
    static fromJSON(obj: CreateIncreasePositionRequestParamsJSON): CreateIncreasePositionRequestParams;
    toEncodable(): {
        sizeUsdDelta: BN;
        collateralTokenDelta: BN;
        side: {
            None: {};
        } | {
            Long: {};
        } | {
            Short: {};
        };
        requestType: {
            Market: {};
        } | {
            Trigger: {};
        };
        priceSlippage: BN | null;
        jupiterMinimumOut: BN | null;
        triggerPrice: BN | null;
        triggerAboveThreshold: boolean | null;
        counter: BN;
    };
}
//# sourceMappingURL=CreateIncreasePositionRequestParams.d.ts.map