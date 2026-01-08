import BN from "bn.js";
import * as types from "../types";
export interface AddPoolParamsFields {
    name: string;
    limit: types.LimitFields;
    fees: types.FeesFields;
    maxRequestExecutionSec: BN;
}
export interface AddPoolParamsJSON {
    name: string;
    limit: types.LimitJSON;
    fees: types.FeesJSON;
    maxRequestExecutionSec: string;
}
export declare class AddPoolParams {
    readonly name: string;
    readonly limit: types.Limit;
    readonly fees: types.Fees;
    readonly maxRequestExecutionSec: BN;
    constructor(fields: AddPoolParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AddPoolParams;
    static toEncodable(fields: AddPoolParamsFields): {
        name: string;
        limit: {
            maxAumUsd: BN;
            maxIndividualLpToken: BN;
            maxPositionUsd: BN;
        };
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
        maxRequestExecutionSec: BN;
    };
    toJSON(): AddPoolParamsJSON;
    static fromJSON(obj: AddPoolParamsJSON): AddPoolParams;
    toEncodable(): {
        name: string;
        limit: {
            maxAumUsd: BN;
            maxIndividualLpToken: BN;
            maxPositionUsd: BN;
        };
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
        maxRequestExecutionSec: BN;
    };
}
//# sourceMappingURL=AddPoolParams.d.ts.map