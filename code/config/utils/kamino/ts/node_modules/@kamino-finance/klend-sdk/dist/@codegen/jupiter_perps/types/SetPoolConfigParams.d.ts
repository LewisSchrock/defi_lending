import BN from "bn.js";
import * as types from "../types";
export interface SetPoolConfigParamsFields {
    fees: types.FeesFields;
    limit: types.LimitFields;
    maxRequestExecutionSec: BN;
}
export interface SetPoolConfigParamsJSON {
    fees: types.FeesJSON;
    limit: types.LimitJSON;
    maxRequestExecutionSec: string;
}
export declare class SetPoolConfigParams {
    readonly fees: types.Fees;
    readonly limit: types.Limit;
    readonly maxRequestExecutionSec: BN;
    constructor(fields: SetPoolConfigParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SetPoolConfigParams;
    static toEncodable(fields: SetPoolConfigParamsFields): {
        fees: {
            increasePositionBps: BN;
            decreasePositionBps: BN;
            addRemoveLiquidityBps: BN;
            swapBps: BN;
            taxBps: BN;
            stableSwapBps: BN;
            stableSwapTaxBps: BN;
            liquidationRewardBps: BN;
            protocolShareBps: BN;
        };
        limit: {
            maxAumUsd: BN;
            maxIndividualLpToken: BN;
            maxPositionUsd: BN;
        };
        maxRequestExecutionSec: BN;
    };
    toJSON(): SetPoolConfigParamsJSON;
    static fromJSON(obj: SetPoolConfigParamsJSON): SetPoolConfigParams;
    toEncodable(): {
        fees: {
            increasePositionBps: BN;
            decreasePositionBps: BN;
            addRemoveLiquidityBps: BN;
            swapBps: BN;
            taxBps: BN;
            stableSwapBps: BN;
            stableSwapTaxBps: BN;
            liquidationRewardBps: BN;
            protocolShareBps: BN;
        };
        limit: {
            maxAumUsd: BN;
            maxIndividualLpToken: BN;
            maxPositionUsd: BN;
        };
        maxRequestExecutionSec: BN;
    };
}
//# sourceMappingURL=SetPoolConfigParams.d.ts.map