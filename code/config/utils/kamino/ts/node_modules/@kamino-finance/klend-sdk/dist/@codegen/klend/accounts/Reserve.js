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
exports.Reserve = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class Reserve {
    /** Version of the reserve */
    version;
    /** Last slot when supply and rates updated */
    lastUpdate;
    /** Lending market address */
    lendingMarket;
    farmCollateral;
    farmDebt;
    /** Reserve liquidity */
    liquidity;
    reserveLiquidityPadding;
    /** Reserve collateral */
    collateral;
    reserveCollateralPadding;
    /** Reserve configuration values */
    config;
    configPadding;
    borrowedAmountOutsideElevationGroup;
    /**
     * Amount of token borrowed in lamport of debt asset in the given
     * elevation group when this reserve is part of the collaterals.
     */
    borrowedAmountsAgainstThisReserveInElevationGroups;
    padding;
    static discriminator = Buffer.from([
        43, 242, 204, 202, 26, 247, 59, 127,
    ]);
    static layout = borsh.struct([
        borsh.u64("version"),
        types.LastUpdate.layout("lastUpdate"),
        (0, utils_1.borshAddress)("lendingMarket"),
        (0, utils_1.borshAddress)("farmCollateral"),
        (0, utils_1.borshAddress)("farmDebt"),
        types.ReserveLiquidity.layout("liquidity"),
        borsh.array(borsh.u64(), 150, "reserveLiquidityPadding"),
        types.ReserveCollateral.layout("collateral"),
        borsh.array(borsh.u64(), 150, "reserveCollateralPadding"),
        types.ReserveConfig.layout("config"),
        borsh.array(borsh.u64(), 116, "configPadding"),
        borsh.u64("borrowedAmountOutsideElevationGroup"),
        borsh.array(borsh.u64(), 32, "borrowedAmountsAgainstThisReserveInElevationGroups"),
        borsh.array(borsh.u64(), 207, "padding"),
    ]);
    constructor(fields) {
        this.version = fields.version;
        this.lastUpdate = new types.LastUpdate({ ...fields.lastUpdate });
        this.lendingMarket = fields.lendingMarket;
        this.farmCollateral = fields.farmCollateral;
        this.farmDebt = fields.farmDebt;
        this.liquidity = new types.ReserveLiquidity({ ...fields.liquidity });
        this.reserveLiquidityPadding = fields.reserveLiquidityPadding;
        this.collateral = new types.ReserveCollateral({ ...fields.collateral });
        this.reserveCollateralPadding = fields.reserveCollateralPadding;
        this.config = new types.ReserveConfig({ ...fields.config });
        this.configPadding = fields.configPadding;
        this.borrowedAmountOutsideElevationGroup =
            fields.borrowedAmountOutsideElevationGroup;
        this.borrowedAmountsAgainstThisReserveInElevationGroups =
            fields.borrowedAmountsAgainstThisReserveInElevationGroups;
        this.padding = fields.padding;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`ReserveFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
        }
        return this.decode(Buffer.from(info.data));
    }
    static async fetchMultiple(rpc, addresses, programId = programId_1.PROGRAM_ID) {
        const infos = await (0, kit_1.fetchEncodedAccounts)(rpc, addresses);
        return infos.map((info) => {
            if (!info.exists) {
                return null;
            }
            if (info.programAddress !== programId) {
                throw new Error(`ReserveFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(Reserve.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = Reserve.layout.decode(data.slice(8));
        return new Reserve({
            version: dec.version,
            lastUpdate: types.LastUpdate.fromDecoded(dec.lastUpdate),
            lendingMarket: dec.lendingMarket,
            farmCollateral: dec.farmCollateral,
            farmDebt: dec.farmDebt,
            liquidity: types.ReserveLiquidity.fromDecoded(dec.liquidity),
            reserveLiquidityPadding: dec.reserveLiquidityPadding,
            collateral: types.ReserveCollateral.fromDecoded(dec.collateral),
            reserveCollateralPadding: dec.reserveCollateralPadding,
            config: types.ReserveConfig.fromDecoded(dec.config),
            configPadding: dec.configPadding,
            borrowedAmountOutsideElevationGroup: dec.borrowedAmountOutsideElevationGroup,
            borrowedAmountsAgainstThisReserveInElevationGroups: dec.borrowedAmountsAgainstThisReserveInElevationGroups,
            padding: dec.padding,
        });
    }
    toJSON() {
        return {
            version: this.version.toString(),
            lastUpdate: this.lastUpdate.toJSON(),
            lendingMarket: this.lendingMarket,
            farmCollateral: this.farmCollateral,
            farmDebt: this.farmDebt,
            liquidity: this.liquidity.toJSON(),
            reserveLiquidityPadding: this.reserveLiquidityPadding.map((item) => item.toString()),
            collateral: this.collateral.toJSON(),
            reserveCollateralPadding: this.reserveCollateralPadding.map((item) => item.toString()),
            config: this.config.toJSON(),
            configPadding: this.configPadding.map((item) => item.toString()),
            borrowedAmountOutsideElevationGroup: this.borrowedAmountOutsideElevationGroup.toString(),
            borrowedAmountsAgainstThisReserveInElevationGroups: this.borrowedAmountsAgainstThisReserveInElevationGroups.map((item) => item.toString()),
            padding: this.padding.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new Reserve({
            version: new bn_js_1.default(obj.version),
            lastUpdate: types.LastUpdate.fromJSON(obj.lastUpdate),
            lendingMarket: (0, kit_1.address)(obj.lendingMarket),
            farmCollateral: (0, kit_1.address)(obj.farmCollateral),
            farmDebt: (0, kit_1.address)(obj.farmDebt),
            liquidity: types.ReserveLiquidity.fromJSON(obj.liquidity),
            reserveLiquidityPadding: obj.reserveLiquidityPadding.map((item) => new bn_js_1.default(item)),
            collateral: types.ReserveCollateral.fromJSON(obj.collateral),
            reserveCollateralPadding: obj.reserveCollateralPadding.map((item) => new bn_js_1.default(item)),
            config: types.ReserveConfig.fromJSON(obj.config),
            configPadding: obj.configPadding.map((item) => new bn_js_1.default(item)),
            borrowedAmountOutsideElevationGroup: new bn_js_1.default(obj.borrowedAmountOutsideElevationGroup),
            borrowedAmountsAgainstThisReserveInElevationGroups: obj.borrowedAmountsAgainstThisReserveInElevationGroups.map((item) => new bn_js_1.default(item)),
            padding: obj.padding.map((item) => new bn_js_1.default(item)),
        });
    }
}
exports.Reserve = Reserve;
//# sourceMappingURL=Reserve.js.map