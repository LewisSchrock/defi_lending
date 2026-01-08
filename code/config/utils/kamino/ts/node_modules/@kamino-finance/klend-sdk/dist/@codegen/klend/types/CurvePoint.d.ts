import * as types from "../types";
export interface CurvePointFields {
    utilizationRateBps: number;
    borrowRateBps: number;
}
export interface CurvePointJSON {
    utilizationRateBps: number;
    borrowRateBps: number;
}
export declare class CurvePoint {
    readonly utilizationRateBps: number;
    readonly borrowRateBps: number;
    constructor(fields: CurvePointFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.CurvePoint;
    static toEncodable(fields: CurvePointFields): {
        utilizationRateBps: number;
        borrowRateBps: number;
    };
    toJSON(): CurvePointJSON;
    static fromJSON(obj: CurvePointJSON): CurvePoint;
    toEncodable(): {
        utilizationRateBps: number;
        borrowRateBps: number;
    };
}
//# sourceMappingURL=CurvePoint.d.ts.map