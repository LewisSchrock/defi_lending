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
exports.VaultAllocation = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class VaultAllocation {
    reserve;
    ctokenVault;
    targetAllocationWeight;
    /** Maximum token invested in this reserve */
    tokenAllocationCap;
    ctokenVaultBump;
    configPadding;
    ctokenAllocation;
    lastInvestSlot;
    tokenTargetAllocationSf;
    statePadding;
    constructor(fields) {
        this.reserve = fields.reserve;
        this.ctokenVault = fields.ctokenVault;
        this.targetAllocationWeight = fields.targetAllocationWeight;
        this.tokenAllocationCap = fields.tokenAllocationCap;
        this.ctokenVaultBump = fields.ctokenVaultBump;
        this.configPadding = fields.configPadding;
        this.ctokenAllocation = fields.ctokenAllocation;
        this.lastInvestSlot = fields.lastInvestSlot;
        this.tokenTargetAllocationSf = fields.tokenTargetAllocationSf;
        this.statePadding = fields.statePadding;
    }
    static layout(property) {
        return borsh.struct([
            (0, utils_1.borshAddress)("reserve"),
            (0, utils_1.borshAddress)("ctokenVault"),
            borsh.u64("targetAllocationWeight"),
            borsh.u64("tokenAllocationCap"),
            borsh.u64("ctokenVaultBump"),
            borsh.array(borsh.u64(), 127, "configPadding"),
            borsh.u64("ctokenAllocation"),
            borsh.u64("lastInvestSlot"),
            borsh.u128("tokenTargetAllocationSf"),
            borsh.array(borsh.u64(), 128, "statePadding"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new VaultAllocation({
            reserve: obj.reserve,
            ctokenVault: obj.ctokenVault,
            targetAllocationWeight: obj.targetAllocationWeight,
            tokenAllocationCap: obj.tokenAllocationCap,
            ctokenVaultBump: obj.ctokenVaultBump,
            configPadding: obj.configPadding,
            ctokenAllocation: obj.ctokenAllocation,
            lastInvestSlot: obj.lastInvestSlot,
            tokenTargetAllocationSf: obj.tokenTargetAllocationSf,
            statePadding: obj.statePadding,
        });
    }
    static toEncodable(fields) {
        return {
            reserve: fields.reserve,
            ctokenVault: fields.ctokenVault,
            targetAllocationWeight: fields.targetAllocationWeight,
            tokenAllocationCap: fields.tokenAllocationCap,
            ctokenVaultBump: fields.ctokenVaultBump,
            configPadding: fields.configPadding,
            ctokenAllocation: fields.ctokenAllocation,
            lastInvestSlot: fields.lastInvestSlot,
            tokenTargetAllocationSf: fields.tokenTargetAllocationSf,
            statePadding: fields.statePadding,
        };
    }
    toJSON() {
        return {
            reserve: this.reserve,
            ctokenVault: this.ctokenVault,
            targetAllocationWeight: this.targetAllocationWeight.toString(),
            tokenAllocationCap: this.tokenAllocationCap.toString(),
            ctokenVaultBump: this.ctokenVaultBump.toString(),
            configPadding: this.configPadding.map((item) => item.toString()),
            ctokenAllocation: this.ctokenAllocation.toString(),
            lastInvestSlot: this.lastInvestSlot.toString(),
            tokenTargetAllocationSf: this.tokenTargetAllocationSf.toString(),
            statePadding: this.statePadding.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new VaultAllocation({
            reserve: (0, kit_1.address)(obj.reserve),
            ctokenVault: (0, kit_1.address)(obj.ctokenVault),
            targetAllocationWeight: new bn_js_1.default(obj.targetAllocationWeight),
            tokenAllocationCap: new bn_js_1.default(obj.tokenAllocationCap),
            ctokenVaultBump: new bn_js_1.default(obj.ctokenVaultBump),
            configPadding: obj.configPadding.map((item) => new bn_js_1.default(item)),
            ctokenAllocation: new bn_js_1.default(obj.ctokenAllocation),
            lastInvestSlot: new bn_js_1.default(obj.lastInvestSlot),
            tokenTargetAllocationSf: new bn_js_1.default(obj.tokenTargetAllocationSf),
            statePadding: obj.statePadding.map((item) => new bn_js_1.default(item)),
        });
    }
    toEncodable() {
        return VaultAllocation.toEncodable(this);
    }
}
exports.VaultAllocation = VaultAllocation;
//# sourceMappingURL=VaultAllocation.js.map