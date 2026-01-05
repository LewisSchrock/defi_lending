import BN from "bn.js";
import * as types from "../types";
export interface UpdateDecreasePositionRequestParamsFields {
    sizeUsdDelta: BN;
    triggerPrice: BN;
}
export interface UpdateDecreasePositionRequestParamsJSON {
    sizeUsdDelta: string;
    triggerPrice: string;
}
export declare class UpdateDecreasePositionRequestParams {
    readonly sizeUsdDelta: BN;
    readonly triggerPrice: BN;
    constructor(fields: UpdateDecreasePositionRequestParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.UpdateDecreasePositionRequestParams;
    static toEncodable(fields: UpdateDecreasePositionRequestParamsFields): {
        sizeUsdDelta: BN;
        triggerPrice: BN;
    };
    toJSON(): UpdateDecreasePositionRequestParamsJSON;
    static fromJSON(obj: UpdateDecreasePositionRequestParamsJSON): UpdateDecreasePositionRequestParams;
    toEncodable(): {
        sizeUsdDelta: BN;
        triggerPrice: BN;
    };
}
//# sourceMappingURL=UpdateDecreasePositionRequestParams.d.ts.map