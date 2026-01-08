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
exports.BufferRelayerAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class BufferRelayerAccountData {
    name;
    queuePubkey;
    escrow;
    authority;
    jobPubkey;
    jobHash;
    minUpdateDelaySeconds;
    isLocked;
    currentRound;
    latestConfirmedRound;
    result;
    static discriminator = Buffer.from([
        50, 35, 51, 115, 169, 219, 158, 52,
    ]);
    static layout = borsh.struct([
        borsh.array(borsh.u8(), 32, "name"),
        (0, utils_1.borshAddress)("queuePubkey"),
        (0, utils_1.borshAddress)("escrow"),
        (0, utils_1.borshAddress)("authority"),
        (0, utils_1.borshAddress)("jobPubkey"),
        borsh.array(borsh.u8(), 32, "jobHash"),
        borsh.u32("minUpdateDelaySeconds"),
        borsh.bool("isLocked"),
        types.BufferRelayerRound.layout("currentRound"),
        types.BufferRelayerRound.layout("latestConfirmedRound"),
        borsh.vecU8("result"),
    ]);
    constructor(fields) {
        this.name = fields.name;
        this.queuePubkey = fields.queuePubkey;
        this.escrow = fields.escrow;
        this.authority = fields.authority;
        this.jobPubkey = fields.jobPubkey;
        this.jobHash = fields.jobHash;
        this.minUpdateDelaySeconds = fields.minUpdateDelaySeconds;
        this.isLocked = fields.isLocked;
        this.currentRound = new types.BufferRelayerRound({ ...fields.currentRound });
        this.latestConfirmedRound = new types.BufferRelayerRound({
            ...fields.latestConfirmedRound,
        });
        this.result = fields.result;
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
        if (!data.slice(0, 8).equals(BufferRelayerAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = BufferRelayerAccountData.layout.decode(data.slice(8));
        return new BufferRelayerAccountData({
            name: dec.name,
            queuePubkey: dec.queuePubkey,
            escrow: dec.escrow,
            authority: dec.authority,
            jobPubkey: dec.jobPubkey,
            jobHash: dec.jobHash,
            minUpdateDelaySeconds: dec.minUpdateDelaySeconds,
            isLocked: dec.isLocked,
            currentRound: types.BufferRelayerRound.fromDecoded(dec.currentRound),
            latestConfirmedRound: types.BufferRelayerRound.fromDecoded(dec.latestConfirmedRound),
            result: new Uint8Array(dec.result.buffer, dec.result.byteOffset, dec.result.length),
        });
    }
    toJSON() {
        return {
            name: this.name,
            queuePubkey: this.queuePubkey,
            escrow: this.escrow,
            authority: this.authority,
            jobPubkey: this.jobPubkey,
            jobHash: this.jobHash,
            minUpdateDelaySeconds: this.minUpdateDelaySeconds,
            isLocked: this.isLocked,
            currentRound: this.currentRound.toJSON(),
            latestConfirmedRound: this.latestConfirmedRound.toJSON(),
            result: Array.from(this.result.values()),
        };
    }
    static fromJSON(obj) {
        return new BufferRelayerAccountData({
            name: obj.name,
            queuePubkey: (0, kit_1.address)(obj.queuePubkey),
            escrow: (0, kit_1.address)(obj.escrow),
            authority: (0, kit_1.address)(obj.authority),
            jobPubkey: (0, kit_1.address)(obj.jobPubkey),
            jobHash: obj.jobHash,
            minUpdateDelaySeconds: obj.minUpdateDelaySeconds,
            isLocked: obj.isLocked,
            currentRound: types.BufferRelayerRound.fromJSON(obj.currentRound),
            latestConfirmedRound: types.BufferRelayerRound.fromJSON(obj.latestConfirmedRound),
            result: Uint8Array.from(obj.result),
        });
    }
}
exports.BufferRelayerAccountData = BufferRelayerAccountData;
//# sourceMappingURL=BufferRelayerAccountData.js.map