import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface PerpetualsFields {
    permissions: types.PermissionsFields;
    pools: Array<Address>;
    admin: Address;
    transferAuthorityBump: number;
    perpetualsBump: number;
    inceptionTime: BN;
}
export interface PerpetualsJSON {
    permissions: types.PermissionsJSON;
    pools: Array<string>;
    admin: string;
    transferAuthorityBump: number;
    perpetualsBump: number;
    inceptionTime: string;
}
export declare class Perpetuals {
    readonly permissions: types.Permissions;
    readonly pools: Array<Address>;
    readonly admin: Address;
    readonly transferAuthorityBump: number;
    readonly perpetualsBump: number;
    readonly inceptionTime: BN;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<Perpetuals>;
    constructor(fields: PerpetualsFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<Perpetuals | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<Perpetuals | null>>;
    static decode(data: Buffer): Perpetuals;
    toJSON(): PerpetualsJSON;
    static fromJSON(obj: PerpetualsJSON): Perpetuals;
}
//# sourceMappingURL=Perpetuals.d.ts.map