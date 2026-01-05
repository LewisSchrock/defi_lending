import BN from "bn.js";
import * as types from "../types";
export interface LeaseExtendParamsFields {
    loadAmount: BN;
    leaseBump: number;
    stateBump: number;
    walletBumps: Uint8Array;
}
export interface LeaseExtendParamsJSON {
    loadAmount: string;
    leaseBump: number;
    stateBump: number;
    walletBumps: Array<number>;
}
export declare class LeaseExtendParams {
    readonly loadAmount: BN;
    readonly leaseBump: number;
    readonly stateBump: number;
    readonly walletBumps: Uint8Array;
    constructor(fields: LeaseExtendParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.LeaseExtendParams;
    static toEncodable(fields: LeaseExtendParamsFields): {
        loadAmount: BN;
        leaseBump: number;
        stateBump: number;
        walletBumps: Buffer<ArrayBufferLike>;
    };
    toJSON(): LeaseExtendParamsJSON;
    static fromJSON(obj: LeaseExtendParamsJSON): LeaseExtendParams;
    toEncodable(): {
        loadAmount: BN;
        leaseBump: number;
        stateBump: number;
        walletBumps: Buffer<ArrayBufferLike>;
    };
}
//# sourceMappingURL=LeaseExtendParams.d.ts.map