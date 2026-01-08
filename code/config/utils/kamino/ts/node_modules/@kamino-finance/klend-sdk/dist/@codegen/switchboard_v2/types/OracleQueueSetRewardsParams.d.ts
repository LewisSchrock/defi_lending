import BN from "bn.js";
import * as types from "../types";
export interface OracleQueueSetRewardsParamsFields {
    rewards: BN;
}
export interface OracleQueueSetRewardsParamsJSON {
    rewards: string;
}
export declare class OracleQueueSetRewardsParams {
    readonly rewards: BN;
    constructor(fields: OracleQueueSetRewardsParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.OracleQueueSetRewardsParams;
    static toEncodable(fields: OracleQueueSetRewardsParamsFields): {
        rewards: BN;
    };
    toJSON(): OracleQueueSetRewardsParamsJSON;
    static fromJSON(obj: OracleQueueSetRewardsParamsJSON): OracleQueueSetRewardsParams;
    toEncodable(): {
        rewards: BN;
    };
}
//# sourceMappingURL=OracleQueueSetRewardsParams.d.ts.map