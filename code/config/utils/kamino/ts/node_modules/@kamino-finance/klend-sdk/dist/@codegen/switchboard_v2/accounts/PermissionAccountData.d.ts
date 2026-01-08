import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
export interface PermissionAccountDataFields {
    authority: Address;
    permissions: number;
    granter: Address;
    grantee: Address;
    expiration: BN;
    ebuf: Array<number>;
}
export interface PermissionAccountDataJSON {
    authority: string;
    permissions: number;
    granter: string;
    grantee: string;
    expiration: string;
    ebuf: Array<number>;
}
export declare class PermissionAccountData {
    readonly authority: Address;
    readonly permissions: number;
    readonly granter: Address;
    readonly grantee: Address;
    readonly expiration: BN;
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<PermissionAccountData>;
    constructor(fields: PermissionAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<PermissionAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<PermissionAccountData | null>>;
    static decode(data: Buffer): PermissionAccountData;
    toJSON(): PermissionAccountDataJSON;
    static fromJSON(obj: PermissionAccountDataJSON): PermissionAccountData;
}
//# sourceMappingURL=PermissionAccountData.d.ts.map