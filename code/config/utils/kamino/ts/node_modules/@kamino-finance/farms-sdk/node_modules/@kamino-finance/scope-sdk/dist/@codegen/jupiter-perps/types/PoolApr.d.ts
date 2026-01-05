import BN from "bn.js";
import * as types from "../types";
export interface PoolAprFields {
    lastUpdated: BN;
    feeAprBps: BN;
    realizedFeeUsd: BN;
}
export interface PoolAprJSON {
    lastUpdated: string;
    feeAprBps: string;
    realizedFeeUsd: string;
}
export declare class PoolApr {
    readonly lastUpdated: BN;
    readonly feeAprBps: BN;
    readonly realizedFeeUsd: BN;
    constructor(fields: PoolAprFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PoolApr;
    static toEncodable(fields: PoolAprFields): {
        lastUpdated: BN;
        feeAprBps: BN;
        realizedFeeUsd: BN;
    };
    toJSON(): PoolAprJSON;
    static fromJSON(obj: PoolAprJSON): PoolApr;
    toEncodable(): {
        lastUpdated: BN;
        feeAprBps: BN;
        realizedFeeUsd: BN;
    };
}
//# sourceMappingURL=PoolApr.d.ts.map