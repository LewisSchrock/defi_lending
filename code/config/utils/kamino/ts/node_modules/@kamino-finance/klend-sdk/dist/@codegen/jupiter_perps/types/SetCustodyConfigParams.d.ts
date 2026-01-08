import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface SetCustodyConfigParamsFields {
    oracle: types.OracleParamsFields;
    pricing: types.PricingParamsFields;
    permissions: types.PermissionsFields;
    hourlyFundingBps: BN;
    targetRatioBps: BN;
}
export interface SetCustodyConfigParamsJSON {
    oracle: types.OracleParamsJSON;
    pricing: types.PricingParamsJSON;
    permissions: types.PermissionsJSON;
    hourlyFundingBps: string;
    targetRatioBps: string;
}
export declare class SetCustodyConfigParams {
    readonly oracle: types.OracleParams;
    readonly pricing: types.PricingParams;
    readonly permissions: types.Permissions;
    readonly hourlyFundingBps: BN;
    readonly targetRatioBps: BN;
    constructor(fields: SetCustodyConfigParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SetCustodyConfigParams;
    static toEncodable(fields: SetCustodyConfigParamsFields): {
        oracle: {
            oracleAccount: Address;
            oracleType: {
                None: {};
            } | {
                Test: {};
            } | {
                Pyth: {};
            };
            maxPriceError: BN;
            maxPriceAgeSec: number;
        };
        pricing: {
            tradeSpreadLong: BN;
            tradeSpreadShort: BN;
            swapSpread: BN;
            maxLeverage: BN;
            maxGlobalLongSizes: BN;
            maxGlobalShortSizes: BN;
        };
        permissions: {
            allowSwap: boolean;
            allowAddLiquidity: boolean;
            allowRemoveLiquidity: boolean;
            allowIncreasePosition: boolean;
            allowDecreasePosition: boolean;
            allowCollateralWithdrawal: boolean;
            allowLiquidatePosition: boolean;
        };
        hourlyFundingBps: BN;
        targetRatioBps: BN;
    };
    toJSON(): SetCustodyConfigParamsJSON;
    static fromJSON(obj: SetCustodyConfigParamsJSON): SetCustodyConfigParams;
    toEncodable(): {
        oracle: {
            oracleAccount: Address;
            oracleType: {
                None: {};
            } | {
                Test: {};
            } | {
                Pyth: {};
            };
            maxPriceError: BN;
            maxPriceAgeSec: number;
        };
        pricing: {
            tradeSpreadLong: BN;
            tradeSpreadShort: BN;
            swapSpread: BN;
            maxLeverage: BN;
            maxGlobalLongSizes: BN;
            maxGlobalShortSizes: BN;
        };
        permissions: {
            allowSwap: boolean;
            allowAddLiquidity: boolean;
            allowRemoveLiquidity: boolean;
            allowIncreasePosition: boolean;
            allowDecreasePosition: boolean;
            allowCollateralWithdrawal: boolean;
            allowLiquidatePosition: boolean;
        };
        hourlyFundingBps: BN;
        targetRatioBps: BN;
    };
}
//# sourceMappingURL=SetCustodyConfigParams.d.ts.map