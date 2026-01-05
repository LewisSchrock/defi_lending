import * as types from "../types";
export interface IncreasePositionParamsFields {
}
export interface IncreasePositionParamsJSON {
}
export declare class IncreasePositionParams {
    constructor(fields: IncreasePositionParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.IncreasePositionParams;
    static toEncodable(fields: IncreasePositionParamsFields): {};
    toJSON(): IncreasePositionParamsJSON;
    static fromJSON(obj: IncreasePositionParamsJSON): IncreasePositionParams;
    toEncodable(): {};
}
//# sourceMappingURL=IncreasePositionParams.d.ts.map