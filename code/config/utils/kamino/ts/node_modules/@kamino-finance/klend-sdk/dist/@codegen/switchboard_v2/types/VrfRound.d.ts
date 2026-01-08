import BN from "bn.js";
import * as types from "../types";
export interface VrfRoundFields {
    alpha: Array<number>;
    alphaLen: number;
    requestSlot: BN;
    requestTimestamp: BN;
    result: Array<number>;
    numVerified: number;
    ebuf: Array<number>;
}
export interface VrfRoundJSON {
    alpha: Array<number>;
    alphaLen: number;
    requestSlot: string;
    requestTimestamp: string;
    result: Array<number>;
    numVerified: number;
    ebuf: Array<number>;
}
export declare class VrfRound {
    readonly alpha: Array<number>;
    readonly alphaLen: number;
    readonly requestSlot: BN;
    readonly requestTimestamp: BN;
    readonly result: Array<number>;
    readonly numVerified: number;
    readonly ebuf: Array<number>;
    constructor(fields: VrfRoundFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VrfRound;
    static toEncodable(fields: VrfRoundFields): {
        alpha: number[];
        alphaLen: number;
        requestSlot: BN;
        requestTimestamp: BN;
        result: number[];
        numVerified: number;
        ebuf: number[];
    };
    toJSON(): VrfRoundJSON;
    static fromJSON(obj: VrfRoundJSON): VrfRound;
    toEncodable(): {
        alpha: number[];
        alphaLen: number;
        requestSlot: BN;
        requestTimestamp: BN;
        result: number[];
        numVerified: number;
        ebuf: number[];
    };
}
//# sourceMappingURL=VrfRound.d.ts.map