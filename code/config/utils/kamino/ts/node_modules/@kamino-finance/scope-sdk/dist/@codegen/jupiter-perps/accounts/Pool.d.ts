import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface PoolFields {
    name: string;
    custodies: Array<Address>;
    aumUsd: BN;
    limit: types.LimitFields;
    fees: types.FeesFields;
    poolApr: types.PoolAprFields;
    maxRequestExecutionSec: BN;
    bump: number;
    lpTokenBump: number;
    inceptionTime: BN;
}
export interface PoolJSON {
    name: string;
    custodies: Array<string>;
    aumUsd: string;
    limit: types.LimitJSON;
    fees: types.FeesJSON;
    poolApr: types.PoolAprJSON;
    maxRequestExecutionSec: string;
    bump: number;
    lpTokenBump: number;
    inceptionTime: string;
}
export declare class Pool {
    readonly name: string;
    readonly custodies: Array<Address>;
    readonly aumUsd: BN;
    readonly limit: types.Limit;
    readonly fees: types.Fees;
    readonly poolApr: types.PoolApr;
    readonly maxRequestExecutionSec: BN;
    readonly bump: number;
    readonly lpTokenBump: number;
    readonly inceptionTime: BN;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<Pool>;
    constructor(fields: PoolFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<Pool | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<Pool | null>>;
    static decode(data: Buffer): Pool;
    toJSON(): PoolJSON;
    static fromJSON(obj: PoolJSON): Pool;
}
//# sourceMappingURL=Pool.d.ts.map