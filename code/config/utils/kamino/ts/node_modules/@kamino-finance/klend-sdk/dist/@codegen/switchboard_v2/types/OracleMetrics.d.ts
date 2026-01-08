import BN from "bn.js";
import * as types from "../types";
export interface OracleMetricsFields {
    consecutiveSuccess: BN;
    consecutiveError: BN;
    consecutiveDisagreement: BN;
    consecutiveLateResponse: BN;
    consecutiveFailure: BN;
    totalSuccess: BN;
    totalError: BN;
    totalDisagreement: BN;
    totalLateResponse: BN;
}
export interface OracleMetricsJSON {
    consecutiveSuccess: string;
    consecutiveError: string;
    consecutiveDisagreement: string;
    consecutiveLateResponse: string;
    consecutiveFailure: string;
    totalSuccess: string;
    totalError: string;
    totalDisagreement: string;
    totalLateResponse: string;
}
export declare class OracleMetrics {
    readonly consecutiveSuccess: BN;
    readonly consecutiveError: BN;
    readonly consecutiveDisagreement: BN;
    readonly consecutiveLateResponse: BN;
    readonly consecutiveFailure: BN;
    readonly totalSuccess: BN;
    readonly totalError: BN;
    readonly totalDisagreement: BN;
    readonly totalLateResponse: BN;
    constructor(fields: OracleMetricsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.OracleMetrics;
    static toEncodable(fields: OracleMetricsFields): {
        consecutiveSuccess: BN;
        consecutiveError: BN;
        consecutiveDisagreement: BN;
        consecutiveLateResponse: BN;
        consecutiveFailure: BN;
        totalSuccess: BN;
        totalError: BN;
        totalDisagreement: BN;
        totalLateResponse: BN;
    };
    toJSON(): OracleMetricsJSON;
    static fromJSON(obj: OracleMetricsJSON): OracleMetrics;
    toEncodable(): {
        consecutiveSuccess: BN;
        consecutiveError: BN;
        consecutiveDisagreement: BN;
        consecutiveLateResponse: BN;
        consecutiveFailure: BN;
        totalSuccess: BN;
        totalError: BN;
        totalDisagreement: BN;
        totalLateResponse: BN;
    };
}
//# sourceMappingURL=OracleMetrics.d.ts.map