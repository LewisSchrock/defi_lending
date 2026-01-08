import BN from "bn.js";
import * as types from "../types";
export interface SetCustodyGlobalLimitParamsFields {
    maxGlobalLongSizes: BN;
    maxGlobalShortSizes: BN;
}
export interface SetCustodyGlobalLimitParamsJSON {
    maxGlobalLongSizes: string;
    maxGlobalShortSizes: string;
}
export declare class SetCustodyGlobalLimitParams {
    readonly maxGlobalLongSizes: BN;
    readonly maxGlobalShortSizes: BN;
    constructor(fields: SetCustodyGlobalLimitParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SetCustodyGlobalLimitParams;
    static toEncodable(fields: SetCustodyGlobalLimitParamsFields): {
        maxGlobalLongSizes: BN;
        maxGlobalShortSizes: BN;
    };
    toJSON(): SetCustodyGlobalLimitParamsJSON;
    static fromJSON(obj: SetCustodyGlobalLimitParamsJSON): SetCustodyGlobalLimitParams;
    toEncodable(): {
        maxGlobalLongSizes: BN;
        maxGlobalShortSizes: BN;
    };
}
//# sourceMappingURL=SetCustodyGlobalLimitParams.d.ts.map