import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
export interface RealmSpawnRecordAccountDataFields {
    ebuf: Array<number>;
}
export interface RealmSpawnRecordAccountDataJSON {
    ebuf: Array<number>;
}
export declare class RealmSpawnRecordAccountData {
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<RealmSpawnRecordAccountData>;
    constructor(fields: RealmSpawnRecordAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<RealmSpawnRecordAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<RealmSpawnRecordAccountData | null>>;
    static decode(data: Buffer): RealmSpawnRecordAccountData;
    toJSON(): RealmSpawnRecordAccountDataJSON;
    static fromJSON(obj: RealmSpawnRecordAccountDataJSON): RealmSpawnRecordAccountData;
}
//# sourceMappingURL=RealmSpawnRecordAccountData.d.ts.map