import BN from "bn.js";
import * as types from "../types";
export interface SetTestTimeParamsFields {
    time: BN;
}
export interface SetTestTimeParamsJSON {
    time: string;
}
export declare class SetTestTimeParams {
    readonly time: BN;
    constructor(fields: SetTestTimeParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SetTestTimeParams;
    static toEncodable(fields: SetTestTimeParamsFields): {
        time: BN;
    };
    toJSON(): SetTestTimeParamsJSON;
    static fromJSON(obj: SetTestTimeParamsJSON): SetTestTimeParams;
    toEncodable(): {
        time: BN;
    };
}
//# sourceMappingURL=SetTestTimeParams.d.ts.map