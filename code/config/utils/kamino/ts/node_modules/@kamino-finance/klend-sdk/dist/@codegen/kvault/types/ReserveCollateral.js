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
exports.ReserveCollateral = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
/** Reserve collateral */
class ReserveCollateral {
    /** Reserve collateral mint address */
    mintPubkey;
    /** Reserve collateral mint supply, used for exchange rate */
    mintTotalSupply;
    /** Reserve collateral supply address */
    supplyVault;
    padding1;
    padding2;
    constructor(fields) {
        this.mintPubkey = fields.mintPubkey;
        this.mintTotalSupply = fields.mintTotalSupply;
        this.supplyVault = fields.supplyVault;
        this.padding1 = fields.padding1;
        this.padding2 = fields.padding2;
    }
    static layout(property) {
        return borsh.struct([
            (0, utils_1.borshAddress)("mintPubkey"),
            borsh.u64("mintTotalSupply"),
            (0, utils_1.borshAddress)("supplyVault"),
            borsh.array(borsh.u128(), 32, "padding1"),
            borsh.array(borsh.u128(), 32, "padding2"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new ReserveCollateral({
            mintPubkey: obj.mintPubkey,
            mintTotalSupply: obj.mintTotalSupply,
            supplyVault: obj.supplyVault,
            padding1: obj.padding1,
            padding2: obj.padding2,
        });
    }
    static toEncodable(fields) {
        return {
            mintPubkey: fields.mintPubkey,
            mintTotalSupply: fields.mintTotalSupply,
            supplyVault: fields.supplyVault,
            padding1: fields.padding1,
            padding2: fields.padding2,
        };
    }
    toJSON() {
        return {
            mintPubkey: this.mintPubkey,
            mintTotalSupply: this.mintTotalSupply.toString(),
            supplyVault: this.supplyVault,
            padding1: this.padding1.map((item) => item.toString()),
            padding2: this.padding2.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new ReserveCollateral({
            mintPubkey: (0, kit_1.address)(obj.mintPubkey),
            mintTotalSupply: new bn_js_1.default(obj.mintTotalSupply),
            supplyVault: (0, kit_1.address)(obj.supplyVault),
            padding1: obj.padding1.map((item) => new bn_js_1.default(item)),
            padding2: obj.padding2.map((item) => new bn_js_1.default(item)),
        });
    }
    toEncodable() {
        return ReserveCollateral.toEncodable(this);
    }
}
exports.ReserveCollateral = ReserveCollateral;
//# sourceMappingURL=ReserveCollateral.js.map