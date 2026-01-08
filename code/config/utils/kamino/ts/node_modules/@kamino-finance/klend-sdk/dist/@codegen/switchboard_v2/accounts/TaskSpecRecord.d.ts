import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import * as types from "../types";
export interface TaskSpecRecordFields {
    hash: types.HashFields;
}
export interface TaskSpecRecordJSON {
    hash: types.HashJSON;
}
export declare class TaskSpecRecord {
    readonly hash: types.Hash;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<TaskSpecRecord>;
    constructor(fields: TaskSpecRecordFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<TaskSpecRecord | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<TaskSpecRecord | null>>;
    static decode(data: Buffer): TaskSpecRecord;
    toJSON(): TaskSpecRecordJSON;
    static fromJSON(obj: TaskSpecRecordJSON): TaskSpecRecord;
}
//# sourceMappingURL=TaskSpecRecord.d.ts.map