import BN from "bn.js";
import * as types from "../types";
export interface FundingRateStateFields {
    cumulativeInterestRate: BN;
    lastUpdate: BN;
    hourlyFundingBps: BN;
}
export interface FundingRateStateJSON {
    cumulativeInterestRate: string;
    lastUpdate: string;
    hourlyFundingBps: string;
}
export declare class FundingRateState {
    readonly cumulativeInterestRate: BN;
    readonly lastUpdate: BN;
    readonly hourlyFundingBps: BN;
    constructor(fields: FundingRateStateFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.FundingRateState;
    static toEncodable(fields: FundingRateStateFields): {
        cumulativeInterestRate: BN;
        lastUpdate: BN;
        hourlyFundingBps: BN;
    };
    toJSON(): FundingRateStateJSON;
    static fromJSON(obj: FundingRateStateJSON): FundingRateState;
    toEncodable(): {
        cumulativeInterestRate: BN;
        lastUpdate: BN;
        hourlyFundingBps: BN;
    };
}
//# sourceMappingURL=FundingRateState.d.ts.map