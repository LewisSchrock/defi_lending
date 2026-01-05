"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.TestInitParams = void 0;
const borsh = __importStar(require("@coral-xyz/borsh"));
class TestInitParams {
    allowSwap;
    allowAddLiquidity;
    allowRemoveLiquidity;
    allowIncreasePosition;
    allowDecreasePosition;
    allowCollateralWithdrawal;
    allowLiquidatePosition;
    constructor(fields) {
        this.allowSwap = fields.allowSwap;
        this.allowAddLiquidity = fields.allowAddLiquidity;
        this.allowRemoveLiquidity = fields.allowRemoveLiquidity;
        this.allowIncreasePosition = fields.allowIncreasePosition;
        this.allowDecreasePosition = fields.allowDecreasePosition;
        this.allowCollateralWithdrawal = fields.allowCollateralWithdrawal;
        this.allowLiquidatePosition = fields.allowLiquidatePosition;
    }
    static layout(property) {
        return borsh.struct([
            borsh.bool("allowSwap"),
            borsh.bool("allowAddLiquidity"),
            borsh.bool("allowRemoveLiquidity"),
            borsh.bool("allowIncreasePosition"),
            borsh.bool("allowDecreasePosition"),
            borsh.bool("allowCollateralWithdrawal"),
            borsh.bool("allowLiquidatePosition"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new TestInitParams({
            allowSwap: obj.allowSwap,
            allowAddLiquidity: obj.allowAddLiquidity,
            allowRemoveLiquidity: obj.allowRemoveLiquidity,
            allowIncreasePosition: obj.allowIncreasePosition,
            allowDecreasePosition: obj.allowDecreasePosition,
            allowCollateralWithdrawal: obj.allowCollateralWithdrawal,
            allowLiquidatePosition: obj.allowLiquidatePosition,
        });
    }
    static toEncodable(fields) {
        return {
            allowSwap: fields.allowSwap,
            allowAddLiquidity: fields.allowAddLiquidity,
            allowRemoveLiquidity: fields.allowRemoveLiquidity,
            allowIncreasePosition: fields.allowIncreasePosition,
            allowDecreasePosition: fields.allowDecreasePosition,
            allowCollateralWithdrawal: fields.allowCollateralWithdrawal,
            allowLiquidatePosition: fields.allowLiquidatePosition,
        };
    }
    toJSON() {
        return {
            allowSwap: this.allowSwap,
            allowAddLiquidity: this.allowAddLiquidity,
            allowRemoveLiquidity: this.allowRemoveLiquidity,
            allowIncreasePosition: this.allowIncreasePosition,
            allowDecreasePosition: this.allowDecreasePosition,
            allowCollateralWithdrawal: this.allowCollateralWithdrawal,
            allowLiquidatePosition: this.allowLiquidatePosition,
        };
    }
    static fromJSON(obj) {
        return new TestInitParams({
            allowSwap: obj.allowSwap,
            allowAddLiquidity: obj.allowAddLiquidity,
            allowRemoveLiquidity: obj.allowRemoveLiquidity,
            allowIncreasePosition: obj.allowIncreasePosition,
            allowDecreasePosition: obj.allowDecreasePosition,
            allowCollateralWithdrawal: obj.allowCollateralWithdrawal,
            allowLiquidatePosition: obj.allowLiquidatePosition,
        });
    }
    toEncodable() {
        return TestInitParams.toEncodable(this);
    }
}
exports.TestInitParams = TestInitParams;
//# sourceMappingURL=TestInitParams.js.map