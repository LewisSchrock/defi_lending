import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface ConfigFields {
    governanceAuthority: Address;
    targetGovernanceAuthority: Address | null;
    wormhole: Address;
    validDataSources: Array<types.DataSourceFields>;
    singleUpdateFeeInLamports: BN;
    minimumSignatures: number;
}
export interface ConfigJSON {
    governanceAuthority: string;
    targetGovernanceAuthority: string | null;
    wormhole: string;
    validDataSources: Array<types.DataSourceJSON>;
    singleUpdateFeeInLamports: string;
    minimumSignatures: number;
}
export declare class Config {
    readonly governanceAuthority: Address;
    readonly targetGovernanceAuthority: Address | null;
    readonly wormhole: Address;
    readonly validDataSources: Array<types.DataSource>;
    readonly singleUpdateFeeInLamports: BN;
    readonly minimumSignatures: number;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<Config>;
    constructor(fields: ConfigFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<Config | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<Config | null>>;
    static decode(data: Buffer): Config;
    toJSON(): ConfigJSON;
    static fromJSON(obj: ConfigJSON): Config;
}
//# sourceMappingURL=Config.d.ts.map