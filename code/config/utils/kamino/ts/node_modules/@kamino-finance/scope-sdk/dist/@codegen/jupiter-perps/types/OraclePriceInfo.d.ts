import BN from "bn.js";
import * as types from "../types";
export interface OraclePriceInfoFields {
    increaseLong: BN;
    increaseShort: BN;
    decreaseLong: BN;
    decreaseShort: BN;
    buyLp: BN;
    sellLp: BN;
}
export interface OraclePriceInfoJSON {
    increaseLong: string;
    increaseShort: string;
    decreaseLong: string;
    decreaseShort: string;
    buyLp: string;
    sellLp: string;
}
export declare class OraclePriceInfo {
    readonly increaseLong: BN;
    readonly increaseShort: BN;
    readonly decreaseLong: BN;
    readonly decreaseShort: BN;
    readonly buyLp: BN;
    readonly sellLp: BN;
    constructor(fields: OraclePriceInfoFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.OraclePriceInfo;
    static toEncodable(fields: OraclePriceInfoFields): {
        increaseLong: BN;
        increaseShort: BN;
        decreaseLong: BN;
        decreaseShort: BN;
        buyLp: BN;
        sellLp: BN;
    };
    toJSON(): OraclePriceInfoJSON;
    static fromJSON(obj: OraclePriceInfoJSON): OraclePriceInfo;
    toEncodable(): {
        increaseLong: BN;
        increaseShort: BN;
        decreaseLong: BN;
        decreaseShort: BN;
        buyLp: BN;
        sellLp: BN;
    };
}
//# sourceMappingURL=OraclePriceInfo.d.ts.map