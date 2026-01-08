import BN from "bn.js";
import * as types from "../types";
export interface AssetsFields {
    feesReserves: BN;
    owned: BN;
    locked: BN;
    guaranteedUsd: BN;
    globalShortSizes: BN;
    globalShortAveragePrices: BN;
}
export interface AssetsJSON {
    feesReserves: string;
    owned: string;
    locked: string;
    guaranteedUsd: string;
    globalShortSizes: string;
    globalShortAveragePrices: string;
}
export declare class Assets {
    readonly feesReserves: BN;
    readonly owned: BN;
    readonly locked: BN;
    readonly guaranteedUsd: BN;
    readonly globalShortSizes: BN;
    readonly globalShortAveragePrices: BN;
    constructor(fields: AssetsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.Assets;
    static toEncodable(fields: AssetsFields): {
        feesReserves: BN;
        owned: BN;
        locked: BN;
        guaranteedUsd: BN;
        globalShortSizes: BN;
        globalShortAveragePrices: BN;
    };
    toJSON(): AssetsJSON;
    static fromJSON(obj: AssetsJSON): Assets;
    toEncodable(): {
        feesReserves: BN;
        owned: BN;
        locked: BN;
        guaranteedUsd: BN;
        globalShortSizes: BN;
        globalShortAveragePrices: BN;
    };
}
//# sourceMappingURL=Assets.d.ts.map