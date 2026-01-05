import BN from "bn.js";
import * as types from "../types";
export interface OracleQueueInitParamsFields {
    name: Array<number>;
    metadata: Array<number>;
    reward: BN;
    minStake: BN;
    feedProbationPeriod: number;
    oracleTimeout: number;
    slashingEnabled: boolean;
    varianceToleranceMultiplier: types.BorshDecimalFields;
    consecutiveFeedFailureLimit: BN;
    consecutiveOracleFailureLimit: BN;
    queueSize: number;
    unpermissionedFeeds: boolean;
    unpermissionedVrf: boolean;
    enableBufferRelayers: boolean;
}
export interface OracleQueueInitParamsJSON {
    name: Array<number>;
    metadata: Array<number>;
    reward: string;
    minStake: string;
    feedProbationPeriod: number;
    oracleTimeout: number;
    slashingEnabled: boolean;
    varianceToleranceMultiplier: types.BorshDecimalJSON;
    consecutiveFeedFailureLimit: string;
    consecutiveOracleFailureLimit: string;
    queueSize: number;
    unpermissionedFeeds: boolean;
    unpermissionedVrf: boolean;
    enableBufferRelayers: boolean;
}
export declare class OracleQueueInitParams {
    readonly name: Array<number>;
    readonly metadata: Array<number>;
    readonly reward: BN;
    readonly minStake: BN;
    readonly feedProbationPeriod: number;
    readonly oracleTimeout: number;
    readonly slashingEnabled: boolean;
    readonly varianceToleranceMultiplier: types.BorshDecimal;
    readonly consecutiveFeedFailureLimit: BN;
    readonly consecutiveOracleFailureLimit: BN;
    readonly queueSize: number;
    readonly unpermissionedFeeds: boolean;
    readonly unpermissionedVrf: boolean;
    readonly enableBufferRelayers: boolean;
    constructor(fields: OracleQueueInitParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.OracleQueueInitParams;
    static toEncodable(fields: OracleQueueInitParamsFields): {
        name: number[];
        metadata: number[];
        reward: BN;
        minStake: BN;
        feedProbationPeriod: number;
        oracleTimeout: number;
        slashingEnabled: boolean;
        varianceToleranceMultiplier: {
            mantissa: BN;
            scale: number;
        };
        consecutiveFeedFailureLimit: BN;
        consecutiveOracleFailureLimit: BN;
        queueSize: number;
        unpermissionedFeeds: boolean;
        unpermissionedVrf: boolean;
        enableBufferRelayers: boolean;
    };
    toJSON(): OracleQueueInitParamsJSON;
    static fromJSON(obj: OracleQueueInitParamsJSON): OracleQueueInitParams;
    toEncodable(): {
        name: number[];
        metadata: number[];
        reward: BN;
        minStake: BN;
        feedProbationPeriod: number;
        oracleTimeout: number;
        slashingEnabled: boolean;
        varianceToleranceMultiplier: {
            mantissa: BN;
            scale: number;
        };
        consecutiveFeedFailureLimit: BN;
        consecutiveOracleFailureLimit: BN;
        queueSize: number;
        unpermissionedFeeds: boolean;
        unpermissionedVrf: boolean;
        enableBufferRelayers: boolean;
    };
}
//# sourceMappingURL=OracleQueueInitParams.d.ts.map