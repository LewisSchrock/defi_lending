import * as types from "../types";
export interface BufferRelayerSaveResultParamsFields {
    stateBump: number;
    permissionBump: number;
    result: Uint8Array;
    success: boolean;
}
export interface BufferRelayerSaveResultParamsJSON {
    stateBump: number;
    permissionBump: number;
    result: Array<number>;
    success: boolean;
}
export declare class BufferRelayerSaveResultParams {
    readonly stateBump: number;
    readonly permissionBump: number;
    readonly result: Uint8Array;
    readonly success: boolean;
    constructor(fields: BufferRelayerSaveResultParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.BufferRelayerSaveResultParams;
    static toEncodable(fields: BufferRelayerSaveResultParamsFields): {
        stateBump: number;
        permissionBump: number;
        result: Buffer<ArrayBufferLike>;
        success: boolean;
    };
    toJSON(): BufferRelayerSaveResultParamsJSON;
    static fromJSON(obj: BufferRelayerSaveResultParamsJSON): BufferRelayerSaveResultParams;
    toEncodable(): {
        stateBump: number;
        permissionBump: number;
        result: Buffer<ArrayBufferLike>;
        success: boolean;
    };
}
//# sourceMappingURL=BufferRelayerSaveResultParams.d.ts.map