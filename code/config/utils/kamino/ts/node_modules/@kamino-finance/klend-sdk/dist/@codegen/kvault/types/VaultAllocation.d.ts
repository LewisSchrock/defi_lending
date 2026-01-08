import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface VaultAllocationFields {
    reserve: Address;
    ctokenVault: Address;
    targetAllocationWeight: BN;
    /** Maximum token invested in this reserve */
    tokenAllocationCap: BN;
    ctokenVaultBump: BN;
    configPadding: Array<BN>;
    ctokenAllocation: BN;
    lastInvestSlot: BN;
    tokenTargetAllocationSf: BN;
    statePadding: Array<BN>;
}
export interface VaultAllocationJSON {
    reserve: string;
    ctokenVault: string;
    targetAllocationWeight: string;
    /** Maximum token invested in this reserve */
    tokenAllocationCap: string;
    ctokenVaultBump: string;
    configPadding: Array<string>;
    ctokenAllocation: string;
    lastInvestSlot: string;
    tokenTargetAllocationSf: string;
    statePadding: Array<string>;
}
export declare class VaultAllocation {
    readonly reserve: Address;
    readonly ctokenVault: Address;
    readonly targetAllocationWeight: BN;
    /** Maximum token invested in this reserve */
    readonly tokenAllocationCap: BN;
    readonly ctokenVaultBump: BN;
    readonly configPadding: Array<BN>;
    readonly ctokenAllocation: BN;
    readonly lastInvestSlot: BN;
    readonly tokenTargetAllocationSf: BN;
    readonly statePadding: Array<BN>;
    constructor(fields: VaultAllocationFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VaultAllocation;
    static toEncodable(fields: VaultAllocationFields): {
        reserve: Address;
        ctokenVault: Address;
        targetAllocationWeight: BN;
        tokenAllocationCap: BN;
        ctokenVaultBump: BN;
        configPadding: BN[];
        ctokenAllocation: BN;
        lastInvestSlot: BN;
        tokenTargetAllocationSf: BN;
        statePadding: BN[];
    };
    toJSON(): VaultAllocationJSON;
    static fromJSON(obj: VaultAllocationJSON): VaultAllocation;
    toEncodable(): {
        reserve: Address;
        ctokenVault: Address;
        targetAllocationWeight: BN;
        tokenAllocationCap: BN;
        ctokenVaultBump: BN;
        configPadding: BN[];
        ctokenAllocation: BN;
        lastInvestSlot: BN;
        tokenTargetAllocationSf: BN;
        statePadding: BN[];
    };
}
//# sourceMappingURL=VaultAllocation.d.ts.map