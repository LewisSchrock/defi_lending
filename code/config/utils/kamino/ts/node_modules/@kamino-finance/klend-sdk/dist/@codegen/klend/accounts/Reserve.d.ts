import { Address, GetAccountInfoApi, GetMultipleAccountsApi, Rpc } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface ReserveFields {
    /** Version of the reserve */
    version: BN;
    /** Last slot when supply and rates updated */
    lastUpdate: types.LastUpdateFields;
    /** Lending market address */
    lendingMarket: Address;
    farmCollateral: Address;
    farmDebt: Address;
    /** Reserve liquidity */
    liquidity: types.ReserveLiquidityFields;
    reserveLiquidityPadding: Array<BN>;
    /** Reserve collateral */
    collateral: types.ReserveCollateralFields;
    reserveCollateralPadding: Array<BN>;
    /** Reserve configuration values */
    config: types.ReserveConfigFields;
    configPadding: Array<BN>;
    borrowedAmountOutsideElevationGroup: BN;
    /**
     * Amount of token borrowed in lamport of debt asset in the given
     * elevation group when this reserve is part of the collaterals.
     */
    borrowedAmountsAgainstThisReserveInElevationGroups: Array<BN>;
    padding: Array<BN>;
}
export interface ReserveJSON {
    /** Version of the reserve */
    version: string;
    /** Last slot when supply and rates updated */
    lastUpdate: types.LastUpdateJSON;
    /** Lending market address */
    lendingMarket: string;
    farmCollateral: string;
    farmDebt: string;
    /** Reserve liquidity */
    liquidity: types.ReserveLiquidityJSON;
    reserveLiquidityPadding: Array<string>;
    /** Reserve collateral */
    collateral: types.ReserveCollateralJSON;
    reserveCollateralPadding: Array<string>;
    /** Reserve configuration values */
    config: types.ReserveConfigJSON;
    configPadding: Array<string>;
    borrowedAmountOutsideElevationGroup: string;
    /**
     * Amount of token borrowed in lamport of debt asset in the given
     * elevation group when this reserve is part of the collaterals.
     */
    borrowedAmountsAgainstThisReserveInElevationGroups: Array<string>;
    padding: Array<string>;
}
export declare class Reserve {
    /** Version of the reserve */
    readonly version: BN;
    /** Last slot when supply and rates updated */
    readonly lastUpdate: types.LastUpdate;
    /** Lending market address */
    readonly lendingMarket: Address;
    readonly farmCollateral: Address;
    readonly farmDebt: Address;
    /** Reserve liquidity */
    readonly liquidity: types.ReserveLiquidity;
    readonly reserveLiquidityPadding: Array<BN>;
    /** Reserve collateral */
    readonly collateral: types.ReserveCollateral;
    readonly reserveCollateralPadding: Array<BN>;
    /** Reserve configuration values */
    readonly config: types.ReserveConfig;
    readonly configPadding: Array<BN>;
    readonly borrowedAmountOutsideElevationGroup: BN;
    /**
     * Amount of token borrowed in lamport of debt asset in the given
     * elevation group when this reserve is part of the collaterals.
     */
    readonly borrowedAmountsAgainstThisReserveInElevationGroups: Array<BN>;
    readonly padding: Array<BN>;
    static readonly discriminator: Buffer<ArrayBuffer>;
    static readonly layout: import("buffer-layout").Layout<Reserve>;
    constructor(fields: ReserveFields);
    static fetch(rpc: Rpc<GetAccountInfoApi>, address: Address, programId?: Address): Promise<Reserve | null>;
    static fetchMultiple(rpc: Rpc<GetMultipleAccountsApi>, addresses: Address[], programId?: Address): Promise<Array<Reserve | null>>;
    static decode(data: Buffer): Reserve;
    toJSON(): ReserveJSON;
    static fromJSON(obj: ReserveJSON): Reserve;
}
//# sourceMappingURL=Reserve.d.ts.map