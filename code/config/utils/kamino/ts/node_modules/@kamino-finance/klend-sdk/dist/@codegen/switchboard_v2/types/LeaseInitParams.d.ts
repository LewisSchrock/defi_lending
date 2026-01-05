import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface LeaseInitParamsFields {
    loadAmount: BN;
    withdrawAuthority: Address;
    leaseBump: number;
    stateBump: number;
    walletBumps: Uint8Array;
}
export interface LeaseInitParamsJSON {
    loadAmount: string;
    withdrawAuthority: string;
    leaseBump: number;
    stateBump: number;
    walletBumps: Array<number>;
}
export declare class LeaseInitParams {
    readonly loadAmount: BN;
    readonly withdrawAuthority: Address;
    readonly leaseBump: number;
    readonly stateBump: number;
    readonly walletBumps: Uint8Array;
    constructor(fields: LeaseInitParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.LeaseInitParams;
    static toEncodable(fields: LeaseInitParamsFields): {
        loadAmount: BN;
        withdrawAuthority: Address;
        leaseBump: number;
        stateBump: number;
        walletBumps: Buffer<ArrayBufferLike>;
    };
    toJSON(): LeaseInitParamsJSON;
    static fromJSON(obj: LeaseInitParamsJSON): LeaseInitParams;
    toEncodable(): {
        loadAmount: BN;
        withdrawAuthority: Address;
        leaseBump: number;
        stateBump: number;
        walletBumps: Buffer<ArrayBufferLike>;
    };
}
//# sourceMappingURL=LeaseInitParams.d.ts.map