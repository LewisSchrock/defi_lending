import BN from "bn.js";
import * as types from "../types";
export interface FeesFields {
    increasePositionBps: BN;
    decreasePositionBps: BN;
    addRemoveLiquidityBps: BN;
    swapBps: BN;
    taxBps: BN;
    stableSwapBps: BN;
    stableSwapTaxBps: BN;
    liquidationRewardBps: BN;
    protocolShareBps: BN;
}
export interface FeesJSON {
    increasePositionBps: string;
    decreasePositionBps: string;
    addRemoveLiquidityBps: string;
    swapBps: string;
    taxBps: string;
    stableSwapBps: string;
    stableSwapTaxBps: string;
    liquidationRewardBps: string;
    protocolShareBps: string;
}
export declare class Fees {
    readonly increasePositionBps: BN;
    readonly decreasePositionBps: BN;
    readonly addRemoveLiquidityBps: BN;
    readonly swapBps: BN;
    readonly taxBps: BN;
    readonly stableSwapBps: BN;
    readonly stableSwapTaxBps: BN;
    readonly liquidationRewardBps: BN;
    readonly protocolShareBps: BN;
    constructor(fields: FeesFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.Fees;
    static toEncodable(fields: FeesFields): {
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
    toJSON(): FeesJSON;
    static fromJSON(obj: FeesJSON): Fees;
    toEncodable(): {
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
}
//# sourceMappingURL=Fees.d.ts.map