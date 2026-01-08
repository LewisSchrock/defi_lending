import * as types from "../types";
export interface TestInitParamsFields {
    allowSwap: boolean;
    allowAddLiquidity: boolean;
    allowRemoveLiquidity: boolean;
    allowIncreasePosition: boolean;
    allowDecreasePosition: boolean;
    allowCollateralWithdrawal: boolean;
    allowLiquidatePosition: boolean;
}
export interface TestInitParamsJSON {
    allowSwap: boolean;
    allowAddLiquidity: boolean;
    allowRemoveLiquidity: boolean;
    allowIncreasePosition: boolean;
    allowDecreasePosition: boolean;
    allowCollateralWithdrawal: boolean;
    allowLiquidatePosition: boolean;
}
export declare class TestInitParams {
    readonly allowSwap: boolean;
    readonly allowAddLiquidity: boolean;
    readonly allowRemoveLiquidity: boolean;
    readonly allowIncreasePosition: boolean;
    readonly allowDecreasePosition: boolean;
    readonly allowCollateralWithdrawal: boolean;
    readonly allowLiquidatePosition: boolean;
    constructor(fields: TestInitParamsFields);
    static layout(property?: string): import("buffer-layout").Layout<unknown>;
    static fromDecoded(obj: any): types.TestInitParams;
    static toEncodable(fields: TestInitParamsFields): {
        allowSwap: boolean;
        allowAddLiquidity: boolean;
        allowRemoveLiquidity: boolean;
        allowIncreasePosition: boolean;
        allowDecreasePosition: boolean;
        allowCollateralWithdrawal: boolean;
        allowLiquidatePosition: boolean;
    };
    toJSON(): TestInitParamsJSON;
    static fromJSON(obj: TestInitParamsJSON): TestInitParams;
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
//# sourceMappingURL=TestInitParams.d.ts.map