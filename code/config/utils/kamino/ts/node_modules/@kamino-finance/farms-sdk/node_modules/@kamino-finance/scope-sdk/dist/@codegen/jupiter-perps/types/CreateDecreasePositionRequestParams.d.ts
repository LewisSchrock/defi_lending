import BN from "bn.js";
import * as types from "../types";
export interface CreateDecreasePositionRequestParamsFields {
    collateralUsdDelta: BN;
    sizeUsdDelta: BN;
    requestType: types.RequestTypeKind;
    priceSlippage: BN | null;
    jupiterMinimumOut: BN | null;
    triggerPrice: BN | null;
    triggerAboveThreshold: boolean | null;
    entirePosition: boolean | null;
    counter: BN;
}
export interface CreateDecreasePositionRequestParamsJSON {
    collateralUsdDelta: string;
    sizeUsdDelta: string;
    requestType: types.RequestTypeJSON;
    priceSlippage: string | null;
    jupiterMinimumOut: string | null;
    triggerPrice: string | null;
    triggerAboveThreshold: boolean | null;
    entirePosition: boolean | null;
    counter: string;
}
export declare class CreateDecreasePositionRequestParams {
    readonly collateralUsdDelta: BN;
    readonly sizeUsdDelta: BN;
    readonly requestType: types.RequestTypeKind;
    readonly priceSlippage: BN | null;
    readonly jupiterMinimumOut: BN | null;
    readonly triggerPrice: BN | null;
    readonly triggerAboveThreshold: boolean | null;
    readonly entirePosition: boolean | null;
    readonly counter: BN;
    constructor(fields: CreateDecreasePositionRequestParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.CreateDecreasePositionRequestParams;
    static toEncodable(fields: CreateDecreasePositionRequestParamsFields): {
        collateralUsdDelta: BN;
        sizeUsdDelta: BN;
        requestType: {
            Market: {};
        } | {
            Trigger: {};
        };
        priceSlippage: BN | null;
        jupiterMinimumOut: BN | null;
        triggerPrice: BN | null;
        triggerAboveThreshold: boolean | null;
        entirePosition: boolean | null;
        counter: BN;
    };
    toJSON(): CreateDecreasePositionRequestParamsJSON;
    static fromJSON(obj: CreateDecreasePositionRequestParamsJSON): CreateDecreasePositionRequestParams;
    toEncodable(): {
        collateralUsdDelta: BN;
        sizeUsdDelta: BN;
        requestType: {
            Market: {};
        } | {
            Trigger: {};
        };
        priceSlippage: BN | null;
        jupiterMinimumOut: BN | null;
        triggerPrice: BN | null;
        triggerAboveThreshold: boolean | null;
        entirePosition: boolean | null;
        counter: BN;
    };
}
//# sourceMappingURL=CreateDecreasePositionRequestParams.d.ts.map