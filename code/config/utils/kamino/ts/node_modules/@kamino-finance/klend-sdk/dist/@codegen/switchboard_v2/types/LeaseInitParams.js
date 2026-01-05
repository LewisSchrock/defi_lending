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
exports.LeaseInitParams = void 0;
const kit_1 = require("@solana/kit"); // eslint-disable-line @typescript-eslint/no-unused-vars
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
const utils_1 = require("../utils");
class LeaseInitParams {
    loadAmount;
    withdrawAuthority;
    leaseBump;
    stateBump;
    walletBumps;
    constructor(fields) {
        this.loadAmount = fields.loadAmount;
        this.withdrawAuthority = fields.withdrawAuthority;
        this.leaseBump = fields.leaseBump;
        this.stateBump = fields.stateBump;
        this.walletBumps = fields.walletBumps;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("loadAmount"),
            (0, utils_1.borshAddress)("withdrawAuthority"),
            borsh.u8("leaseBump"),
            borsh.u8("stateBump"),
            borsh.vecU8("walletBumps"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new LeaseInitParams({
            loadAmount: obj.loadAmount,
            withdrawAuthority: obj.withdrawAuthority,
            leaseBump: obj.leaseBump,
            stateBump: obj.stateBump,
            walletBumps: new Uint8Array(obj.walletBumps.buffer, obj.walletBumps.byteOffset, obj.walletBumps.length),
        });
    }
    static toEncodable(fields) {
        return {
            loadAmount: fields.loadAmount,
            withdrawAuthority: fields.withdrawAuthority,
            leaseBump: fields.leaseBump,
            stateBump: fields.stateBump,
            walletBumps: Buffer.from(fields.walletBumps.buffer, fields.walletBumps.byteOffset, fields.walletBumps.length),
        };
    }
    toJSON() {
        return {
            loadAmount: this.loadAmount.toString(),
            withdrawAuthority: this.withdrawAuthority,
            leaseBump: this.leaseBump,
            stateBump: this.stateBump,
            walletBumps: Array.from(this.walletBumps.values()),
        };
    }
    static fromJSON(obj) {
        return new LeaseInitParams({
            loadAmount: new bn_js_1.default(obj.loadAmount),
            withdrawAuthority: (0, kit_1.address)(obj.withdrawAuthority),
            leaseBump: obj.leaseBump,
            stateBump: obj.stateBump,
            walletBumps: Uint8Array.from(obj.walletBumps),
        });
    }
    toEncodable() {
        return LeaseInitParams.toEncodable(this);
    }
}
exports.LeaseInitParams = LeaseInitParams;
//# sourceMappingURL=LeaseInitParams.js.map