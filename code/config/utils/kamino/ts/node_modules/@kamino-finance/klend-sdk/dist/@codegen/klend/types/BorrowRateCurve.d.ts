import * as types from "../types";
export interface BorrowRateCurveFields {
    points: Array<types.CurvePointFields>;
}
export interface BorrowRateCurveJSON {
    points: Array<types.CurvePointJSON>;
}
export declare class BorrowRateCurve {
    readonly points: Array<types.CurvePoint>;
    constructor(fields: BorrowRateCurveFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.BorrowRateCurve;
    static toEncodable(fields: BorrowRateCurveFields): {
        points: {
            utilizationRateBps: number;
            borrowRateBps: number;
        }[];
    };
    toJSON(): BorrowRateCurveJSON;
    static fromJSON(obj: BorrowRateCurveJSON): BorrowRateCurve;
    toEncodable(): {
        points: {
            utilizationRateBps: number;
            borrowRateBps: number;
        }[];
    };
}
//# sourceMappingURL=BorrowRateCurve.d.ts.map