import * as types from "../types";
export interface DecreasePositionPostSwapParamsFields {
}
export interface DecreasePositionPostSwapParamsJSON {
}
export declare class DecreasePositionPostSwapParams {
    constructor(fields: DecreasePositionPostSwapParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.DecreasePositionPostSwapParams;
    static toEncodable(fields: DecreasePositionPostSwapParamsFields): {};
    toJSON(): DecreasePositionPostSwapParamsJSON;
    static fromJSON(obj: DecreasePositionPostSwapParamsJSON): DecreasePositionPostSwapParams;
    toEncodable(): {};
}
//# sourceMappingURL=DecreasePositionPostSwapParams.d.ts.map