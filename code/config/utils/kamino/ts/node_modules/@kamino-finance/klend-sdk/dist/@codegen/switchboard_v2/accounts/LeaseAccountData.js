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
exports.LeaseAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class LeaseAccountData {
    escrow;
    queue;
    aggregator;
    tokenProgram;
    isActive;
    crankRowCount;
    createdAt;
    updateCount;
    withdrawAuthority;
    ebuf;
    static discriminator = Buffer.from([
        55, 254, 208, 251, 164, 44, 150, 50,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("escrow"),
        (0, utils_1.borshAddress)("queue"),
        (0, utils_1.borshAddress)("aggregator"),
        (0, utils_1.borshAddress)("tokenProgram"),
        borsh.bool("isActive"),
        borsh.u32("crankRowCount"),
        borsh.i64("createdAt"),
        borsh.u128("updateCount"),
        (0, utils_1.borshAddress)("withdrawAuthority"),
        borsh.array(borsh.u8(), 256, "ebuf"),
    ]);
    constructor(fields) {
        this.escrow = fields.escrow;
        this.queue = fields.queue;
        this.aggregator = fields.aggregator;
        this.tokenProgram = fields.tokenProgram;
        this.isActive = fields.isActive;
        this.crankRowCount = fields.crankRowCount;
        this.createdAt = fields.createdAt;
        this.updateCount = fields.updateCount;
        this.withdrawAuthority = fields.withdrawAuthority;
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
        if (!data.slice(0, 8).equals(LeaseAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = LeaseAccountData.layout.decode(data.slice(8));
        return new LeaseAccountData({
            escrow: dec.escrow,
            queue: dec.queue,
            aggregator: dec.aggregator,
            tokenProgram: dec.tokenProgram,
            isActive: dec.isActive,
            crankRowCount: dec.crankRowCount,
            createdAt: dec.createdAt,
            updateCount: dec.updateCount,
            withdrawAuthority: dec.withdrawAuthority,
            ebuf: dec.ebuf,
        });
    }
    toJSON() {
        return {
            escrow: this.escrow,
            queue: this.queue,
            aggregator: this.aggregator,
            tokenProgram: this.tokenProgram,
            isActive: this.isActive,
            crankRowCount: this.crankRowCount,
            createdAt: this.createdAt.toString(),
            updateCount: this.updateCount.toString(),
            withdrawAuthority: this.withdrawAuthority,
            ebuf: this.ebuf,
        };
    }
    static fromJSON(obj) {
        return new LeaseAccountData({
            escrow: (0, kit_1.address)(obj.escrow),
            queue: (0, kit_1.address)(obj.queue),
            aggregator: (0, kit_1.address)(obj.aggregator),
            tokenProgram: (0, kit_1.address)(obj.tokenProgram),
            isActive: obj.isActive,
            crankRowCount: obj.crankRowCount,
            createdAt: new bn_js_1.default(obj.createdAt),
            updateCount: new bn_js_1.default(obj.updateCount),
            withdrawAuthority: (0, kit_1.address)(obj.withdrawAuthority),
            ebuf: obj.ebuf,
        });
    }
}
exports.LeaseAccountData = LeaseAccountData;
//# sourceMappingURL=LeaseAccountData.js.map