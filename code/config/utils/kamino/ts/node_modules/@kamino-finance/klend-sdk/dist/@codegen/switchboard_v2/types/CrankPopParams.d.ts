import * as types from "../types";
export interface CrankPopParamsFields {
    stateBump: number;
    leaseBumps: Uint8Array;
    permissionBumps: Uint8Array;
    nonce: number | null;
    failOpenOnAccountMismatch: boolean | null;
}
export interface CrankPopParamsJSON {
    stateBump: number;
    leaseBumps: Array<number>;
    permissionBumps: Array<number>;
    nonce: number | null;
    failOpenOnAccountMismatch: boolean | null;
}
export declare class CrankPopParams {
    readonly stateBump: number;
    readonly leaseBumps: Uint8Array;
    readonly permissionBumps: Uint8Array;
    readonly nonce: number | null;
    readonly failOpenOnAccountMismatch: boolean | null;
    constructor(fields: CrankPopParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.CrankPopParams;
    static toEncodable(fields: CrankPopParamsFields): {
        stateBump: number;
        leaseBumps: Buffer<ArrayBufferLike>;
        permissionBumps: Buffer<ArrayBufferLike>;
        nonce: number | null;
        failOpenOnAccountMismatch: boolean | null;
    };
    toJSON(): CrankPopParamsJSON;
    static fromJSON(obj: CrankPopParamsJSON): CrankPopParams;
    toEncodable(): {
        stateBump: number;
        leaseBumps: Buffer<ArrayBufferLike>;
        permissionBumps: Buffer<ArrayBufferLike>;
        nonce: number | null;
        failOpenOnAccountMismatch: boolean | null;
    };
}
//# sourceMappingURL=CrankPopParams.d.ts.map