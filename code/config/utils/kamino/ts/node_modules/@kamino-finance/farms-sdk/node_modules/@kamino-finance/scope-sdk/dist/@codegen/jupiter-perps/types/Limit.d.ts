import BN from "bn.js";
import * as types from "../types";
export interface LimitFields {
    maxAumUsd: BN;
    maxIndividualLpToken: BN;
    maxPositionUsd: BN;
}
export interface LimitJSON {
    maxAumUsd: string;
    maxIndividualLpToken: string;
    maxPositionUsd: string;
}
export declare class Limit {
    readonly maxAumUsd: BN;
    readonly maxIndividualLpToken: BN;
    readonly maxPositionUsd: BN;
    constructor(fields: LimitFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.Limit;
    static toEncodable(fields: LimitFields): {
        maxAumUsd: BN;
        maxIndividualLpToken: BN;
        maxPositionUsd: BN;
    };
    toJSON(): LimitJSON;
    static fromJSON(obj: LimitJSON): Limit;
    toEncodable(): {
        maxAumUsd: BN;
        maxIndividualLpToken: BN;
        maxPositionUsd: BN;
    };
}
//# sourceMappingURL=Limit.d.ts.map