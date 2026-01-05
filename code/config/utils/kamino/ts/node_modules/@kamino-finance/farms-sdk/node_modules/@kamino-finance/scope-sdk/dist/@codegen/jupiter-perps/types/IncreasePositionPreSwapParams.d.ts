import * as types from "../types";
export interface IncreasePositionPreSwapParamsFields {
}
export interface IncreasePositionPreSwapParamsJSON {
}
export declare class IncreasePositionPreSwapParams {
    constructor(fields: IncreasePositionPreSwapParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.IncreasePositionPreSwapParams;
    static toEncodable(fields: IncreasePositionPreSwapParamsFields): {};
    toJSON(): IncreasePositionPreSwapParamsJSON;
    static fromJSON(obj: IncreasePositionPreSwapParamsJSON): IncreasePositionPreSwapParams;
    toEncodable(): {};
}
//# sourceMappingURL=IncreasePositionPreSwapParams.d.ts.map