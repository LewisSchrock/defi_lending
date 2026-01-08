import * as types from "../types";
export interface DecreasePositionParamsFields {
}
export interface DecreasePositionParamsJSON {
}
export declare class DecreasePositionParams {
    constructor(fields: DecreasePositionParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.DecreasePositionParams;
    static toEncodable(fields: DecreasePositionParamsFields): {};
    toJSON(): DecreasePositionParamsJSON;
    static fromJSON(obj: DecreasePositionParamsJSON): DecreasePositionParams;
    toEncodable(): {};
}
//# sourceMappingURL=DecreasePositionParams.d.ts.map