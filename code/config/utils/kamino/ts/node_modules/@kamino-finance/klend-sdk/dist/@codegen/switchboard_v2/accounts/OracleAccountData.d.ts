import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface OracleAccountDataFields {
    name: Array<number>;
    metadata: Array<number>;
    oracleAuthority: Address;
    lastHeartbeat: BN;
    numInUse: number;
    tokenAccount: Address;
    queuePubkey: Address;
    metrics: types.OracleMetricsFields;
    ebuf: Array<number>;
}
export interface OracleAccountDataJSON {
    name: Array<number>;
    metadata: Array<number>;
    oracleAuthority: string;
    lastHeartbeat: string;
    numInUse: number;
    tokenAccount: string;
    queuePubkey: string;
    metrics: types.OracleMetricsJSON;
    ebuf: Array<number>;
}
export declare class OracleAccountData {
    readonly name: Array<number>;
    readonly metadata: Array<number>;
    readonly oracleAuthority: Address;
    readonly lastHeartbeat: BN;
    readonly numInUse: number;
    readonly tokenAccount: Address;
    readonly queuePubkey: Address;
    readonly metrics: types.OracleMetrics;
    readonly ebuf: Array<number>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<OracleAccountData>;
    constructor(fields: OracleAccountDataFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<OracleAccountData | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<OracleAccountData | null>>;
    static decode(data: Buffer): OracleAccountData;
    toJSON(): OracleAccountDataJSON;
    static fromJSON(obj: OracleAccountDataJSON): OracleAccountData;
}
//# sourceMappingURL=OracleAccountData.d.ts.map