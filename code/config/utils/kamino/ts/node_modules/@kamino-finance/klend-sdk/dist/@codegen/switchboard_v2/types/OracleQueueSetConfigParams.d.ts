import BN from "bn.js";
import * as types from "../types";
export interface OracleQueueSetConfigParamsFields {
    name: Array<number> | null;
    metadata: Array<number> | null;
    unpermissionedFeedsEnabled: boolean | null;
    unpermissionedVrfEnabled: boolean | null;
    enableBufferRelayers: boolean | null;
    varianceToleranceMultiplier: types.BorshDecimalFields | null;
    slashingEnabled: boolean | null;
    reward: BN | null;
    minStake: BN | null;
    oracleTimeout: number | null;
    consecutiveFeedFailureLimit: BN | null;
    consecutiveOracleFailureLimit: BN | null;
}
export interface OracleQueueSetConfigParamsJSON {
    name: Array<number> | null;
    metadata: Array<number> | null;
    unpermissionedFeedsEnabled: boolean | null;
    unpermissionedVrfEnabled: boolean | null;
    enableBufferRelayers: boolean | null;
    varianceToleranceMultiplier: types.BorshDecimalJSON | null;
    slashingEnabled: boolean | null;
    reward: string | null;
    minStake: string | null;
    oracleTimeout: number | null;
    consecutiveFeedFailureLimit: string | null;
    consecutiveOracleFailureLimit: string | null;
}
export declare class OracleQueueSetConfigParams {
    readonly name: Array<number> | null;
    readonly metadata: Array<number> | null;
    readonly unpermissionedFeedsEnabled: boolean | null;
    readonly unpermissionedVrfEnabled: boolean | null;
    readonly enableBufferRelayers: boolean | null;
    readonly varianceToleranceMultiplier: types.BorshDecimal | null;
    readonly slashingEnabled: boolean | null;
    readonly reward: BN | null;
    readonly minStake: BN | null;
    readonly oracleTimeout: number | null;
    readonly consecutiveFeedFailureLimit: BN | null;
    readonly consecutiveOracleFailureLimit: BN | null;
    constructor(fields: OracleQueueSetConfigParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.OracleQueueSetConfigParams;
    static toEncodable(fields: OracleQueueSetConfigParamsFields): {
        name: number[] | null;
        metadata: number[] | null;
        unpermissionedFeedsEnabled: boolean | null;
        unpermissionedVrfEnabled: boolean | null;
        enableBufferRelayers: boolean | null;
        varianceToleranceMultiplier: {
            mantissa: BN;
            scale: number;
        } | null;
        slashingEnabled: boolean | null;
        reward: BN | null;
        minStake: BN | null;
        oracleTimeout: number | null;
        consecutiveFeedFailureLimit: BN | null;
        consecutiveOracleFailureLimit: BN | null;
    };
    toJSON(): OracleQueueSetConfigParamsJSON;
    static fromJSON(obj: OracleQueueSetConfigParamsJSON): OracleQueueSetConfigParams;
    toEncodable(): {
        name: number[] | null;
        metadata: number[] | null;
        unpermissionedFeedsEnabled: boolean | null;
        unpermissionedVrfEnabled: boolean | null;
        enableBufferRelayers: boolean | null;
        varianceToleranceMultiplier: {
            mantissa: BN;
            scale: number;
        } | null;
        slashingEnabled: boolean | null;
        reward: BN | null;
        minStake: BN | null;
        oracleTimeout: number | null;
        consecutiveFeedFailureLimit: BN | null;
        consecutiveOracleFailureLimit: BN | null;
    };
}
//# sourceMappingURL=OracleQueueSetConfigParams.d.ts.map