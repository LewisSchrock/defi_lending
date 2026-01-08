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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ElevationGroup = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class ElevationGroup {
    maxLiquidationBonusBps;
    id;
    ltvPct;
    liquidationThresholdPct;
    allowNewLoans;
    maxReservesAsCollateral;
    padding0;
    /** Mandatory debt reserve for this elevation group */
    debtReserve;
    padding1;
    constructor(fields) {
        this.maxLiquidationBonusBps = fields.maxLiquidationBonusBps;
        this.id = fields.id;
        this.ltvPct = fields.ltvPct;
        this.liquidationThresholdPct = fields.liquidationThresholdPct;
        this.allowNewLoans = fields.allowNewLoans;
        this.maxReservesAsCollateral = fields.maxReservesAsCollateral;
        this.padding0 = fields.padding0;
        this.debtReserve = fields.debtReserve;
        this.padding1 = fields.padding1;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u16("maxLiquidationBonusBps"),
            borsh.u8("id"),
            borsh.u8("ltvPct"),
            borsh.u8("liquidationThresholdPct"),
            borsh.u8("allowNewLoans"),
            borsh.u8("maxReservesAsCollateral"),
            borsh.u8("padding0"),
            (0, utils_1.borshAddress)("debtReserve"),
            borsh.array(borsh.u64(), 4, "padding1"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new ElevationGroup({
            maxLiquidationBonusBps: obj.maxLiquidationBonusBps,
            id: obj.id,
            ltvPct: obj.ltvPct,
            liquidationThresholdPct: obj.liquidationThresholdPct,
            allowNewLoans: obj.allowNewLoans,
            maxReservesAsCollateral: obj.maxReservesAsCollateral,
            padding0: obj.padding0,
            debtReserve: obj.debtReserve,
            padding1: obj.padding1,
        });
    }
    static toEncodable(fields) {
        return {
            maxLiquidationBonusBps: fields.maxLiquidationBonusBps,
            id: fields.id,
            ltvPct: fields.ltvPct,
            liquidationThresholdPct: fields.liquidationThresholdPct,
            allowNewLoans: fields.allowNewLoans,
            maxReservesAsCollateral: fields.maxReservesAsCollateral,
            padding0: fields.padding0,
            debtReserve: fields.debtReserve,
            padding1: fields.padding1,
        };
    }
    toJSON() {
        return {
            maxLiquidationBonusBps: this.maxLiquidationBonusBps,
            id: this.id,
            ltvPct: this.ltvPct,
            liquidationThresholdPct: this.liquidationThresholdPct,
            allowNewLoans: this.allowNewLoans,
            maxReservesAsCollateral: this.maxReservesAsCollateral,
            padding0: this.padding0,
            debtReserve: this.debtReserve,
            padding1: this.padding1.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new ElevationGroup({
            maxLiquidationBonusBps: obj.maxLiquidationBonusBps,
            id: obj.id,
            ltvPct: obj.ltvPct,
            liquidationThresholdPct: obj.liquidationThresholdPct,
            allowNewLoans: obj.allowNewLoans,
            maxReservesAsCollateral: obj.maxReservesAsCollateral,
            padding0: obj.padding0,
            debtReserve: (0, kit_1.address)(obj.debtReserve),
            padding1: obj.padding1.map((item) => new bn_js_1.default(item)),
        });
    }
    toEncodable() {
        return ElevationGroup.toEncodable(this);
    }
}
exports.ElevationGroup = ElevationGroup;
//# sourceMappingURL=ElevationGroup.js.map