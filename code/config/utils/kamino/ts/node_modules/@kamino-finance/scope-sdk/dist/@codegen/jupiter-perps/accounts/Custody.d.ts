import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface CustodyFields {
    pool: Address;
    mint: Address;
    tokenAccount: Address;
    decimals: number;
    isStable: boolean;
    oracle: types.OracleParamsFields;
    pricing: types.PricingParamsFields;
    permissions: types.PermissionsFields;
    targetRatioBps: BN;
    assets: types.AssetsFields;
    fundingRateState: types.FundingRateStateFields;
    bump: number;
    tokenAccountBump: number;
}
export interface CustodyJSON {
    pool: string;
    mint: string;
    tokenAccount: string;
    decimals: number;
    isStable: boolean;
    oracle: types.OracleParamsJSON;
    pricing: types.PricingParamsJSON;
    permissions: types.PermissionsJSON;
    targetRatioBps: string;
    assets: types.AssetsJSON;
    fundingRateState: types.FundingRateStateJSON;
    bump: number;
    tokenAccountBump: number;
}
export declare class Custody {
    readonly pool: Address;
    readonly mint: Address;
    readonly tokenAccount: Address;
    readonly decimals: number;
    readonly isStable: boolean;
    readonly oracle: types.OracleParams;
    readonly pricing: types.PricingParams;
    readonly permissions: types.Permissions;
    readonly targetRatioBps: BN;
    readonly assets: types.Assets;
    readonly fundingRateState: types.FundingRateState;
    readonly bump: number;
    readonly tokenAccountBump: number;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<Custody>;
    constructor(fields: CustodyFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<Custody | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<Custody | null>>;
    static decode(data: Buffer): Custody;
    toJSON(): CustodyJSON;
    static fromJSON(obj: CustodyJSON): Custody;
}
//# sourceMappingURL=Custody.d.ts.map