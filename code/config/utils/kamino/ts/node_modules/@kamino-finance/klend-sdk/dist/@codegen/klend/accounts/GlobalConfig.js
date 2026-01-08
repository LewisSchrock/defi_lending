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
exports.GlobalConfig = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class GlobalConfig {
    /** Global admin of the program */
    globalAdmin;
    /** Pending admin must sign a specific transaction to become the global admin */
    pendingAdmin;
    /** Fee collector is the only allowed owner of token accounts receiving protocol fees */
    feeCollector;
    /** Padding to make the struct size 1024 bytes */
    padding;
    static discriminator = Buffer.from([
        149, 8, 156, 202, 160, 252, 176, 217,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("globalAdmin"),
        (0, utils_1.borshAddress)("pendingAdmin"),
        (0, utils_1.borshAddress)("feeCollector"),
        borsh.array(borsh.u8(), 928, "padding"),
    ]);
    constructor(fields) {
        this.globalAdmin = fields.globalAdmin;
        this.pendingAdmin = fields.pendingAdmin;
        this.feeCollector = fields.feeCollector;
        this.padding = fields.padding;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`GlobalConfigFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
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
                throw new Error(`GlobalConfigFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(GlobalConfig.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = GlobalConfig.layout.decode(data.slice(8));
        return new GlobalConfig({
            globalAdmin: dec.globalAdmin,
            pendingAdmin: dec.pendingAdmin,
            feeCollector: dec.feeCollector,
            padding: dec.padding,
        });
    }
    toJSON() {
        return {
            globalAdmin: this.globalAdmin,
            pendingAdmin: this.pendingAdmin,
            feeCollector: this.feeCollector,
            padding: this.padding,
        };
    }
    static fromJSON(obj) {
        return new GlobalConfig({
            globalAdmin: (0, kit_1.address)(obj.globalAdmin),
            pendingAdmin: (0, kit_1.address)(obj.pendingAdmin),
            feeCollector: (0, kit_1.address)(obj.feeCollector),
            padding: obj.padding,
        });
    }
}
exports.GlobalConfig = GlobalConfig;
//# sourceMappingURL=GlobalConfig.js.map