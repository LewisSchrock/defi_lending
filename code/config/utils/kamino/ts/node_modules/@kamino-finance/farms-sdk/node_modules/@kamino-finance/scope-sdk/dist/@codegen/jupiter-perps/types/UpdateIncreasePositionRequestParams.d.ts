import BN from "bn.js";
import * as types from "../types";
export interface UpdateIncreasePositionRequestParamsFields {
    sizeUsdDelta: BN;
    triggerPrice: BN;
}
export interface UpdateIncreasePositionRequestParamsJSON {
    sizeUsdDelta: string;
    triggerPrice: string;
}
export declare class UpdateIncreasePositionRequestParams {
    readonly sizeUsdDelta: BN;
    readonly triggerPrice: BN;
    constructor(fields: UpdateIncreasePositionRequestParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.UpdateIncreasePositionRequestParams;
    static toEncodable(fields: UpdateIncreasePositionRequestParamsFields): {
        sizeUsdDelta: BN;
        triggerPrice: BN;
    };
    toJSON(): UpdateIncreasePositionRequestParamsJSON;
    static fromJSON(obj: UpdateIncreasePositionRequestParamsJSON): UpdateIncreasePositionRequestParams;
    toEncodable(): {
        sizeUsdDelta: BN;
        triggerPrice: BN;
    };
}
//# sourceMappingURL=UpdateIncreasePositionRequestParams.d.ts.map