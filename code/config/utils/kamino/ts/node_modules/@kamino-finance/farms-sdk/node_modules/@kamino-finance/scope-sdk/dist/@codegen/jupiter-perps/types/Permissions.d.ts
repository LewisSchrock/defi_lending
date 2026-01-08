import * as types from "../types";
export interface PermissionsFields {
    allowSwap: boolean;
    allowAddLiquidity: boolean;
    allowRemoveLiquidity: boolean;
    allowIncreasePosition: boolean;
    allowDecreasePosition: boolean;
    allowCollateralWithdrawal: boolean;
    allowLiquidatePosition: boolean;
}
export interface PermissionsJSON {
    allowSwap: boolean;
    allowAddLiquidity: boolean;
    allowRemoveLiquidity: boolean;
    allowIncreasePosition: boolean;
    allowDecreasePosition: boolean;
    allowCollateralWithdrawal: boolean;
    allowLiquidatePosition: boolean;
}
export declare class Permissions {
    readonly allowSwap: boolean;
    readonly allowAddLiquidity: boolean;
    readonly allowRemoveLiquidity: boolean;
    readonly allowIncreasePosition: boolean;
    readonly allowDecreasePosition: boolean;
    readonly allowCollateralWithdrawal: boolean;
    readonly allowLiquidatePosition: boolean;
    constructor(fields: PermissionsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.Permissions;
    static toEncodable(fields: PermissionsFields): {
        allowSwap: boolean;
        allowAddLiquidity: boolean;
        allowRemoveLiquidity: boolean;
        allowIncreasePosition: boolean;
        allowDecreasePosition: boolean;
        allowCollateralWithdrawal: boolean;
        allowLiquidatePosition: boolean;
    };
    toJSON(): PermissionsJSON;
    static fromJSON(obj: PermissionsJSON): Permissions;
    toEncodable(): {
        allowSwap: boolean;
        allowAddLiquidity: boolean;
        allowRemoveLiquidity: boolean;
        allowIncreasePosition: boolean;
        allowDecreasePosition: boolean;
        allowCollateralWithdrawal: boolean;
        allowLiquidatePosition: boolean;
    };
}
//# sourceMappingURL=Permissions.d.ts.map