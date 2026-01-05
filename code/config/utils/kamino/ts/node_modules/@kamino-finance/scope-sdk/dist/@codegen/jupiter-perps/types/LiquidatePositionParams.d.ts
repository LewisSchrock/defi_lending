import * as types from "../types";
export interface LiquidatePositionParamsFields {
}
export interface LiquidatePositionParamsJSON {
}
export declare class LiquidatePositionParams {
    constructor(fields: LiquidatePositionParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.LiquidatePositionParams;
    static toEncodable(fields: LiquidatePositionParamsFields): {};
    toJSON(): LiquidatePositionParamsJSON;
    static fromJSON(obj: LiquidatePositionParamsJSON): LiquidatePositionParams;
    toEncodable(): {};
}
//# sourceMappingURL=LiquidatePositionParams.d.ts.map