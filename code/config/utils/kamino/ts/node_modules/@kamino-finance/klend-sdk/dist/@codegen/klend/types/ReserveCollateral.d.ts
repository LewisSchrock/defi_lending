import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface ReserveCollateralFields {
    /** Reserve collateral mint address */
    mintPubkey: Address;
    /** Reserve collateral mint supply, used for exchange rate */
    mintTotalSupply: BN;
    /** Reserve collateral supply address */
    supplyVault: Address;
    padding1: Array<BN>;
    padding2: Array<BN>;
}
export interface ReserveCollateralJSON {
    /** Reserve collateral mint address */
    mintPubkey: string;
    /** Reserve collateral mint supply, used for exchange rate */
    mintTotalSupply: string;
    /** Reserve collateral supply address */
    supplyVault: string;
    padding1: Array<string>;
    padding2: Array<string>;
}
/** Reserve collateral */
export declare class ReserveCollateral {
    /** Reserve collateral mint address */
    readonly mintPubkey: Address;
    /** Reserve collateral mint supply, used for exchange rate */
    readonly mintTotalSupply: BN;
    /** Reserve collateral supply address */
    readonly supplyVault: Address;
    readonly padding1: Array<BN>;
    readonly padding2: Array<BN>;
    constructor(fields: ReserveCollateralFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.ReserveCollateral;
    static toEncodable(fields: ReserveCollateralFields): {
        mintPubkey: Address;
        mintTotalSupply: BN;
        supplyVault: Address;
        padding1: BN[];
        padding2: BN[];
    };
    toJSON(): ReserveCollateralJSON;
    static fromJSON(obj: ReserveCollateralJSON): ReserveCollateral;
    toEncodable(): {
        mintPubkey: Address;
        mintTotalSupply: BN;
        supplyVault: Address;
        padding1: BN[];
        padding2: BN[];
    };
}
//# sourceMappingURL=ReserveCollateral.d.ts.map