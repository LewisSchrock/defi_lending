import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface ElevationGroupFields {
    maxLiquidationBonusBps: number;
    id: number;
    ltvPct: number;
    liquidationThresholdPct: number;
    allowNewLoans: number;
    maxReservesAsCollateral: number;
    padding0: number;
    /** Mandatory debt reserve for this elevation group */
    debtReserve: Address;
    padding1: Array<BN>;
}
export interface ElevationGroupJSON {
    maxLiquidationBonusBps: number;
    id: number;
    ltvPct: number;
    liquidationThresholdPct: number;
    allowNewLoans: number;
    maxReservesAsCollateral: number;
    padding0: number;
    /** Mandatory debt reserve for this elevation group */
    debtReserve: string;
    padding1: Array<string>;
}
export declare class ElevationGroup {
    readonly maxLiquidationBonusBps: number;
    readonly id: number;
    readonly ltvPct: number;
    readonly liquidationThresholdPct: number;
    readonly allowNewLoans: number;
    readonly maxReservesAsCollateral: number;
    readonly padding0: number;
    /** Mandatory debt reserve for this elevation group */
    readonly debtReserve: Address;
    readonly padding1: Array<BN>;
    constructor(fields: ElevationGroupFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.ElevationGroup;
    static toEncodable(fields: ElevationGroupFields): {
        maxLiquidationBonusBps: number;
        id: number;
        ltvPct: number;
        liquidationThresholdPct: number;
        allowNewLoans: number;
        maxReservesAsCollateral: number;
        padding0: number;
        debtReserve: Address;
        padding1: BN[];
    };
    toJSON(): ElevationGroupJSON;
    static fromJSON(obj: ElevationGroupJSON): ElevationGroup;
    toEncodable(): {
        maxLiquidationBonusBps: number;
        id: number;
        ltvPct: number;
        liquidationThresholdPct: number;
        allowNewLoans: number;
        maxReservesAsCollateral: number;
        padding0: number;
        debtReserve: Address;
        padding1: BN[];
    };
}
//# sourceMappingURL=ElevationGroup.d.ts.map