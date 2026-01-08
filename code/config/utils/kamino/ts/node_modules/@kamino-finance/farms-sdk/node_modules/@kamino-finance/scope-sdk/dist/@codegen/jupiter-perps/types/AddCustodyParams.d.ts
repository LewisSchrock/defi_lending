import { Address } from "@solana/kit";
import BN from "bn.js";
import * as types from "../types";
export interface AddCustodyParamsFields {
    isStable: boolean;
    oracle: types.OracleParamsFields;
    pricing: types.PricingParamsFields;
    permissions: types.PermissionsFields;
    hourlyFundingBps: BN;
    targetRatioBps: BN;
}
export interface AddCustodyParamsJSON {
    isStable: boolean;
    oracle: types.OracleParamsJSON;
    pricing: types.PricingParamsJSON;
    permissions: types.PermissionsJSON;
    hourlyFundingBps: string;
    targetRatioBps: string;
}
export declare class AddCustodyParams {
    readonly isStable: boolean;
    readonly oracle: types.OracleParams;
    readonly pricing: types.PricingParams;
    readonly permissions: types.Permissions;
    readonly hourlyFundingBps: BN;
    readonly targetRatioBps: BN;
    constructor(fields: AddCustodyParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.AddCustodyParams;
    static toEncodable(fields: AddCustodyParamsFields): {
        isStable: boolean;
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
    toJSON(): AddCustodyParamsJSON;
    static fromJSON(obj: AddCustodyParamsJSON): AddCustodyParams;
    toEncodable(): {
        isStable: boolean;
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
//# sourceMappingURL=AddCustodyParams.d.ts.map