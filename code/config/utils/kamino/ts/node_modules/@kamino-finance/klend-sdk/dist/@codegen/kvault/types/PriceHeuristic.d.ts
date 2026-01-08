import BN from "bn.js";
import * as types from "../types";
export interface PriceHeuristicFields {
    /** Lower value of acceptable price */
    lower: BN;
    /** Upper value of acceptable price */
    upper: BN;
    /** Number of decimals of the previously defined values */
    exp: BN;
}
export interface PriceHeuristicJSON {
    /** Lower value of acceptable price */
    lower: string;
    /** Upper value of acceptable price */
    upper: string;
    /** Number of decimals of the previously defined values */
    exp: string;
}
export declare class PriceHeuristic {
    /** Lower value of acceptable price */
    readonly lower: BN;
    /** Upper value of acceptable price */
    readonly upper: BN;
    /** Number of decimals of the previously defined values */
    readonly exp: BN;
    constructor(fields: PriceHeuristicFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PriceHeuristic;
    static toEncodable(fields: PriceHeuristicFields): {
        lower: BN;
        upper: BN;
        exp: BN;
    };
    toJSON(): PriceHeuristicJSON;
    static fromJSON(obj: PriceHeuristicJSON): PriceHeuristic;
    toEncodable(): {
        lower: BN;
        upper: BN;
        exp: BN;
    };
}
//# sourceMappingURL=PriceHeuristic.d.ts.map