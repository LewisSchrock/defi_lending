import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface VrfLiteAccountDataFields {
    stateBump: number;
    permissionBump: number;
    vrfPool: Address;
    status: types.VrfStatusKind;
    result: Array<number>;
    counter: BN;
    alpha: Array<number>;
    alphaLen: number;
    requestSlot: BN;
    requestTimestamp: BN;
    authority: Address;
    queue: Address;
    escrow: Address;
    callback: types.CallbackZCFields;
    builder: types.VrfBuilderFields;
    expiration: BN;
    ebuf: Array<number>;
}
export interface VrfLiteAccountDataJSON {
    stateBump: number;
    permissionBump: number;
    vrfPool: string;
    status: types.VrfStatusJSON;
    result: Array<number>;
    counter: string;
    alpha: Array<number>;
    alphaLen: number;
    requestSlot: string;
    requestTimestamp: string;
    authority: string;
    queue: string;
    escrow: string;
    callback: types.CallbackZCJSON;
    builder: types.VrfBuilderJSON;
    expiration: string;
    ebuf: Array<number>;
}
export declare class VrfLiteAccountData {
    readonly stateBump: number;
    readonly permissionBump: number;
    readonly vrfPool: Address;
    readonly status: types.VrfStatusKind;
    readonly result: Array<number>;
    readonly counter: BN;
    readonly alpha: Array<number>;
    readonly alphaLen: number;
    readonly requestSlot: BN;
    readonly requestTimestamp: BN;
    readonly authority: Address;
    readonly queue: Address;
    readonly escrow: Address;
    readonly callback: types.CallbackZC;
    readonly builder: types.VrfBuilder;
    readonly expiration: BN;
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<VrfLiteAccountData>;
    constructor(fields: VrfLiteAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<VrfLiteAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<VrfLiteAccountData | null>>;
    static decode(data: Buffer): VrfLiteAccountData;
    toJSON(): VrfLiteAccountDataJSON;
    static fromJSON(obj: VrfLiteAccountDataJSON): VrfLiteAccountData;
}
//# sourceMappingURL=VrfLiteAccountData.d.ts.map