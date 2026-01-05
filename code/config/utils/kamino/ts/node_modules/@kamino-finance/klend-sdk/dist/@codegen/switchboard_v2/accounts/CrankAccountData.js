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
exports.CrankAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class CrankAccountData {
    name;
    metadata;
    queuePubkey;
    pqSize;
    maxRows;
    jitterModifier;
    ebuf;
    dataBuffer;
    static discriminator = Buffer.from([
        111, 81, 146, 73, 172, 180, 134, 209,
    ]);
    static layout = borsh.struct([
        borsh.array(borsh.u8(), 32, "name"),
        borsh.array(borsh.u8(), 64, "metadata"),
        (0, utils_1.borshAddress)("queuePubkey"),
        borsh.u32("pqSize"),
        borsh.u32("maxRows"),
        borsh.u8("jitterModifier"),
        borsh.array(borsh.u8(), 255, "ebuf"),
        (0, utils_1.borshAddress)("dataBuffer"),
    ]);
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.queuePubkey = fields.queuePubkey;
        this.pqSize = fields.pqSize;
        this.maxRows = fields.maxRows;
        this.jitterModifier = fields.jitterModifier;
        this.ebuf = fields.ebuf;
        this.dataBuffer = fields.dataBuffer;
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
        if (!data.slice(0, 8).equals(CrankAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = CrankAccountData.layout.decode(data.slice(8));
        return new CrankAccountData({
            name: dec.name,
            metadata: dec.metadata,
            queuePubkey: dec.queuePubkey,
            pqSize: dec.pqSize,
            maxRows: dec.maxRows,
            jitterModifier: dec.jitterModifier,
            ebuf: dec.ebuf,
            dataBuffer: dec.dataBuffer,
        });
    }
    toJSON() {
        return {
            name: this.name,
            metadata: this.metadata,
            queuePubkey: this.queuePubkey,
            pqSize: this.pqSize,
            maxRows: this.maxRows,
            jitterModifier: this.jitterModifier,
            ebuf: this.ebuf,
            dataBuffer: this.dataBuffer,
        };
    }
    static fromJSON(obj) {
        return new CrankAccountData({
            name: obj.name,
            metadata: obj.metadata,
            queuePubkey: (0, kit_1.address)(obj.queuePubkey),
            pqSize: obj.pqSize,
            maxRows: obj.maxRows,
            jitterModifier: obj.jitterModifier,
            ebuf: obj.ebuf,
            dataBuffer: (0, kit_1.address)(obj.dataBuffer),
        });
    }
}
exports.CrankAccountData = CrankAccountData;
//# sourceMappingURL=CrankAccountData.js.map