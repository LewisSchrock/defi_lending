import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
export interface LeaseAccountDataFields {
    escrow: Address;
    queue: Address;
    aggregator: Address;
    tokenProgram: Address;
    isActive: boolean;
    crankRowCount: number;
    createdAt: BN;
    updateCount: BN;
    withdrawAuthority: Address;
    ebuf: Array<number>;
}
export interface LeaseAccountDataJSON {
    escrow: string;
    queue: string;
    aggregator: string;
    tokenProgram: string;
    isActive: boolean;
    crankRowCount: number;
    createdAt: string;
    updateCount: string;
    withdrawAuthority: string;
    ebuf: Array<number>;
}
export declare class LeaseAccountData {
    readonly escrow: Address;
    readonly queue: Address;
    readonly aggregator: Address;
    readonly tokenProgram: Address;
    readonly isActive: boolean;
    readonly crankRowCount: number;
    readonly createdAt: BN;
    readonly updateCount: BN;
    readonly withdrawAuthority: Address;
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<LeaseAccountData>;
    constructor(fields: LeaseAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<LeaseAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<LeaseAccountData | null>>;
    static decode(data: Buffer): LeaseAccountData;
    toJSON(): LeaseAccountDataJSON;
    static fromJSON(obj: LeaseAccountDataJSON): LeaseAccountData;
}
//# sourceMappingURL=LeaseAccountData.d.ts.map