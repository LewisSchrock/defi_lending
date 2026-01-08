import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
export interface JobAccountDataFields {
    name: Array<number>;
    metadata: Array<number>;
    authority: Address;
    expiration: BN;
    hash: Array<number>;
    data: Uint8Array;
    referenceCount: number;
    totalSpent: BN;
    createdAt: BN;
    isInitializing: number;
}
export interface JobAccountDataJSON {
    name: Array<number>;
    metadata: Array<number>;
    authority: string;
    expiration: string;
    hash: Array<number>;
    data: Array<number>;
    referenceCount: number;
    totalSpent: string;
    createdAt: string;
    isInitializing: number;
}
export declare class JobAccountData {
    readonly name: Array<number>;
    readonly metadata: Array<number>;
    readonly authority: Address;
    readonly expiration: BN;
    readonly hash: Array<number>;
    readonly data: Uint8Array;
    readonly referenceCount: number;
    readonly totalSpent: BN;
    readonly createdAt: BN;
    readonly isInitializing: number;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<JobAccountData>;
    constructor(fields: JobAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<JobAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<JobAccountData | null>>;
    static decode(data: Buffer): JobAccountData;
    toJSON(): JobAccountDataJSON;
    static fromJSON(obj: JobAccountDataJSON): JobAccountData;
}
//# sourceMappingURL=JobAccountData.d.ts.map