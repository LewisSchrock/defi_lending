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
exports.VrfPoolAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class VrfPoolAccountData {
    authority;
    queue;
    escrow;
    minInterval;
    maxRows;
    size;
    idx;
    stateBump;
    ebuf;
    static discriminator = Buffer.from([86, 67, 58, 9, 46, 21, 101, 248]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("authority"),
        (0, utils_1.borshAddress)("queue"),
        (0, utils_1.borshAddress)("escrow"),
        borsh.u32("minInterval"),
        borsh.u32("maxRows"),
        borsh.u32("size"),
        borsh.u32("idx"),
        borsh.u8("stateBump"),
        borsh.array(borsh.u8(), 135, "ebuf"),
    ]);
    constructor(fields) {
        this.authority = fields.authority;
        this.queue = fields.queue;
        this.escrow = fields.escrow;
        this.minInterval = fields.minInterval;
        this.maxRows = fields.maxRows;
        this.size = fields.size;
        this.idx = fields.idx;
        this.stateBump = fields.stateBump;
        this.ebuf = fields.ebuf;
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
        if (!data.slice(0, 8).equals(VrfPoolAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = VrfPoolAccountData.layout.decode(data.slice(8));
        return new VrfPoolAccountData({
            authority: dec.authority,
            queue: dec.queue,
            escrow: dec.escrow,
            minInterval: dec.minInterval,
            maxRows: dec.maxRows,
            size: dec.size,
            idx: dec.idx,
            stateBump: dec.stateBump,
            ebuf: dec.ebuf,
        });
    }
    toJSON() {
        return {
            authority: this.authority,
            queue: this.queue,
            escrow: this.escrow,
            minInterval: this.minInterval,
            maxRows: this.maxRows,
            size: this.size,
            idx: this.idx,
            stateBump: this.stateBump,
            ebuf: this.ebuf,
        };
    }
    static fromJSON(obj) {
        return new VrfPoolAccountData({
            authority: (0, kit_1.address)(obj.authority),
            queue: (0, kit_1.address)(obj.queue),
            escrow: (0, kit_1.address)(obj.escrow),
            minInterval: obj.minInterval,
            maxRows: obj.maxRows,
            size: obj.size,
            idx: obj.idx,
            stateBump: obj.stateBump,
            ebuf: obj.ebuf,
        });
    }
}
exports.VrfPoolAccountData = VrfPoolAccountData;
//# sourceMappingURL=VrfPoolAccountData.js.map