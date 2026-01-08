import BN from "bn.js";
import * as types from "../types";
export interface PriceFeedMessageFields {
    feedId: Array<number>;
    price: BN;
    conf: BN;
    exponent: number;
    publishTime: BN;
    prevPublishTime: BN;
    emaPrice: BN;
    emaConf: BN;
}
export interface PriceFeedMessageJSON {
    feedId: Array<number>;
    price: string;
    conf: string;
    exponent: number;
    publishTime: string;
    prevPublishTime: string;
    emaPrice: string;
    emaConf: string;
}
export declare class PriceFeedMessage {
    readonly feedId: Array<number>;
    readonly price: BN;
    readonly conf: BN;
    readonly exponent: number;
    readonly publishTime: BN;
    readonly prevPublishTime: BN;
    readonly emaPrice: BN;
    readonly emaConf: BN;
    constructor(fields: PriceFeedMessageFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.PriceFeedMessage;
    static toEncodable(fields: PriceFeedMessageFields): {
        feedId: number[];
        price: BN;
        conf: BN;
        exponent: number;
        publishTime: BN;
        prevPublishTime: BN;
        emaPrice: BN;
        emaConf: BN;
    };
    toJSON(): PriceFeedMessageJSON;
    static fromJSON(obj: PriceFeedMessageJSON): PriceFeedMessage;
    toEncodable(): {
        feedId: number[];
        price: BN;
        conf: BN;
        exponent: number;
        publishTime: BN;
        prevPublishTime: BN;
        emaPrice: BN;
        emaConf: BN;
    };
}
//# sourceMappingURL=PriceFeedMessage.d.ts.map