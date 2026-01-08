import BN from "bn.js";
import * as types from "../types";
export interface LeaseWithdrawParamsFields {
    stateBump: number;
    leaseBump: number;
    amount: BN;
}
export interface LeaseWithdrawParamsJSON {
    stateBump: number;
    leaseBump: number;
    amount: string;
}
export declare class LeaseWithdrawParams {
    readonly stateBump: number;
    readonly leaseBump: number;
    readonly amount: BN;
    constructor(fields: LeaseWithdrawParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.LeaseWithdrawParams;
    static toEncodable(fields: LeaseWithdrawParamsFields): {
        stateBump: number;
        leaseBump: number;
        amount: BN;
    };
    toJSON(): LeaseWithdrawParamsJSON;
    static fromJSON(obj: LeaseWithdrawParamsJSON): LeaseWithdrawParams;
    toEncodable(): {
        stateBump: number;
        leaseBump: number;
        amount: BN;
    };
}
//# sourceMappingURL=LeaseWithdrawParams.d.ts.map