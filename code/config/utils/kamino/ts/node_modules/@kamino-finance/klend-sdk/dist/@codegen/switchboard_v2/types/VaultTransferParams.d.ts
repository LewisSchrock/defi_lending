import BN from "bn.js";
import * as types from "../types";
export interface VaultTransferParamsFields {
    stateBump: number;
    amount: BN;
}
export interface VaultTransferParamsJSON {
    stateBump: number;
    amount: string;
}
export declare class VaultTransferParams {
    readonly stateBump: number;
    readonly amount: BN;
    constructor(fields: VaultTransferParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.VaultTransferParams;
    static toEncodable(fields: VaultTransferParamsFields): {
        stateBump: number;
        amount: BN;
    };
    toJSON(): VaultTransferParamsJSON;
    static fromJSON(obj: VaultTransferParamsJSON): VaultTransferParams;
    toEncodable(): {
        stateBump: number;
        amount: BN;
    };
}
//# sourceMappingURL=VaultTransferParams.d.ts.map