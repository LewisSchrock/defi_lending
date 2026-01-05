import * as types from "../types";
export interface InitParamsFields {
    allowSwap: boolean;
    allowAddLiquidity: boolean;
    allowRemoveLiquidity: boolean;
    allowIncreasePosition: boolean;
    allowDecreasePosition: boolean;
    allowCollateralWithdrawal: boolean;
    allowLiquidatePosition: boolean;
}
export interface InitParamsJSON {
    allowSwap: boolean;
    allowAddLiquidity: boolean;
    allowRemoveLiquidity: boolean;
    allowIncreasePosition: boolean;
    allowDecreasePosition: boolean;
    allowCollateralWithdrawal: boolean;
    allowLiquidatePosition: boolean;
}
export declare class InitParams {
    readonly allowSwap: boolean;
    readonly allowAddLiquidity: boolean;
    readonly allowRemoveLiquidity: boolean;
    readonly allowIncreasePosition: boolean;
    readonly allowDecreasePosition: boolean;
    readonly allowCollateralWithdrawal: boolean;
    readonly allowLiquidatePosition: boolean;
    constructor(fields: InitParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.InitParams;
    static toEncodable(fields: InitParamsFields): {
        allowSwap: boolean;
        allowAddLiquidity: boolean;
        allowRemoveLiquidity: boolean;
        allowIncreasePosition: boolean;
        allowDecreasePosition: boolean;
        allowCollateralWithdrawal: boolean;
        allowLiquidatePosition: boolean;
    };
    toJSON(): InitParamsJSON;
    static fromJSON(obj: InitParamsJSON): InitParams;
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
//# sourceMappingURL=InitParams.d.ts.map