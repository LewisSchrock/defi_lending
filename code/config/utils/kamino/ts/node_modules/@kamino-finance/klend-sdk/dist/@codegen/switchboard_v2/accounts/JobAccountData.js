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
exports.JobAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class JobAccountData {
    name;
    metadata;
    authority;
    expiration;
    hash;
    data;
    referenceCount;
    totalSpent;
    createdAt;
    isInitializing;
    static discriminator = Buffer.from([
        124, 69, 101, 195, 229, 218, 144, 63,
    ]);
    static layout = borsh.struct([
        borsh.array(borsh.u8(), 32, "name"),
        borsh.array(borsh.u8(), 64, "metadata"),
        (0, utils_1.borshAddress)("authority"),
        borsh.i64("expiration"),
        borsh.array(borsh.u8(), 32, "hash"),
        borsh.vecU8("data"),
        borsh.u32("referenceCount"),
        borsh.u64("totalSpent"),
        borsh.i64("createdAt"),
        borsh.u8("isInitializing"),
    ]);
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.authority = fields.authority;
        this.expiration = fields.expiration;
        this.hash = fields.hash;
        this.data = fields.data;
        this.referenceCount = fields.referenceCount;
        this.totalSpent = fields.totalSpent;
        this.createdAt = fields.createdAt;
        this.isInitializing = fields.isInitializing;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error("account doesn't belong to this program");
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
                throw new Error("account doesn't belong to this program");
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(JobAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = JobAccountData.layout.decode(data.slice(8));
        return new JobAccountData({
            name: dec.name,
            metadata: dec.metadata,
            authority: dec.authority,
            expiration: dec.expiration,
            hash: dec.hash,
            data: new Uint8Array(dec.data.buffer, dec.data.byteOffset, dec.data.length),
            referenceCount: dec.referenceCount,
            totalSpent: dec.totalSpent,
            createdAt: dec.createdAt,
            isInitializing: dec.isInitializing,
        });
    }
    toJSON() {
        return {
            name: this.name,
            metadata: this.metadata,
            authority: this.authority,
            expiration: this.expiration.toString(),
            hash: this.hash,
            data: Array.from(this.data.values()),
            referenceCount: this.referenceCount,
            totalSpent: this.totalSpent.toString(),
            createdAt: this.createdAt.toString(),
            isInitializing: this.isInitializing,
        };
    }
    static fromJSON(obj) {
        return new JobAccountData({
            name: obj.name,
            metadata: obj.metadata,
            authority: (0, kit_1.address)(obj.authority),
            expiration: new bn_js_1.default(obj.expiration),
            hash: obj.hash,
            data: Uint8Array.from(obj.data),
            referenceCount: obj.referenceCount,
            totalSpent: new bn_js_1.default(obj.totalSpent),
            createdAt: new bn_js_1.default(obj.createdAt),
            isInitializing: obj.isInitializing,
        });
    }
}
exports.JobAccountData = JobAccountData;
//# sourceMappingURL=JobAccountData.js.map