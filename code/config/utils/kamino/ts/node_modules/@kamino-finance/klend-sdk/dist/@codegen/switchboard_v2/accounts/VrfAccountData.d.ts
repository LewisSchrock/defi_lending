import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface VrfAccountDataFields {
    status: types.VrfStatusKind;
    counter: BN;
    authority: Address;
    oracleQueue: Address;
    escrow: Address;
    callback: types.CallbackZCFields;
    batchSize: number;
    builders: Array<types.VrfBuilderFields>;
    buildersLen: number;
    testMode: boolean;
    currentRound: types.VrfRoundFields;
    ebuf: Array<number>;
}
export interface VrfAccountDataJSON {
    status: types.VrfStatusJSON;
    counter: string;
    authority: string;
    oracleQueue: string;
    escrow: string;
    callback: types.CallbackZCJSON;
    batchSize: number;
    builders: Array<types.VrfBuilderJSON>;
    buildersLen: number;
    testMode: boolean;
    currentRound: types.VrfRoundJSON;
    ebuf: Array<number>;
}
export declare class VrfAccountData {
    readonly status: types.VrfStatusKind;
    readonly counter: BN;
    readonly authority: Address;
    readonly oracleQueue: Address;
    readonly escrow: Address;
    readonly callback: types.CallbackZC;
    readonly batchSize: number;
    readonly builders: Array<types.VrfBuilder>;
    readonly buildersLen: number;
    readonly testMode: boolean;
    readonly currentRound: types.VrfRound;
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<VrfAccountData>;
    constructor(fields: VrfAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<VrfAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<VrfAccountData | null>>;
    static decode(data: Buffer): VrfAccountData;
    toJSON(): VrfAccountDataJSON;
    static fromJSON(obj: VrfAccountDataJSON): VrfAccountData;
}
//# sourceMappingURL=VrfAccountData.d.ts.map