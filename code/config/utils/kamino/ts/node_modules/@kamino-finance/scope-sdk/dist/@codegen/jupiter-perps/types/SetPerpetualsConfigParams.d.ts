import * as types from "../types";
export interface SetPerpetualsConfigParamsFields {
    permissions: types.PermissionsFields;
}
export interface SetPerpetualsConfigParamsJSON {
    permissions: types.PermissionsJSON;
}
export declare class SetPerpetualsConfigParams {
    readonly permissions: types.Permissions;
    constructor(fields: SetPerpetualsConfigParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.SetPerpetualsConfigParams;
    static toEncodable(fields: SetPerpetualsConfigParamsFields): {
        permissions: {
            allowSwap: boolean;
            allowAddLiquidity: boolean;
            allowRemoveLiquidity: boolean;
            allowIncreasePosition: boolean;
            allowDecreasePosition: boolean;
            allowCollateralWithdrawal: boolean;
            allowLiquidatePosition: boolean;
        };
    };
    toJSON(): SetPerpetualsConfigParamsJSON;
    static fromJSON(obj: SetPerpetualsConfigParamsJSON): SetPerpetualsConfigParams;
    toEncodable(): {
        permissions: {
            allowSwap: boolean;
            allowAddLiquidity: boolean;
            allowRemoveLiquidity: boolean;
            allowIncreasePosition: boolean;
            allowDecreasePosition: boolean;
            allowCollateralWithdrawal: boolean;
            allowLiquidatePosition: boolean;
        };
    };
}
//# sourceMappingURL=SetPerpetualsConfigParams.d.ts.map