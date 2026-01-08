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
exports.Pool = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class Pool {
    name;
    custodies;
    aumUsd;
    limit;
    fees;
    poolApr;
    maxRequestExecutionSec;
    bump;
    lpTokenBump;
    inceptionTime;
    static discriminator = Buffer.from([
        241, 154, 109, 4, 17, 177, 109, 188,
    ]);
    static layout = borsh.struct([
        borsh.str("name"),
        borsh.vec((0, utils_1.borshAddress)(), "custodies"),
        borsh.u128("aumUsd"),
        types.Limit.layout("limit"),
        types.Fees.layout("fees"),
        types.PoolApr.layout("poolApr"),
        borsh.i64("maxRequestExecutionSec"),
        borsh.u8("bump"),
        borsh.u8("lpTokenBump"),
        borsh.i64("inceptionTime"),
    ]);
    constructor(fields) {
        this.name = fields.name;
        this.custodies = fields.custodies;
        this.aumUsd = fields.aumUsd;
        this.limit = new types.Limit({ ...fields.limit });
        this.fees = new types.Fees({ ...fields.fees });
        this.poolApr = new types.PoolApr({ ...fields.poolApr });
        this.maxRequestExecutionSec = fields.maxRequestExecutionSec;
        this.bump = fields.bump;
        this.lpTokenBump = fields.lpTokenBump;
        this.inceptionTime = fields.inceptionTime;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`PoolFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
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
                throw new Error(`PoolFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(Pool.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = Pool.layout.decode(data.slice(8));
        return new Pool({
            name: dec.name,
            custodies: dec.custodies,
            aumUsd: dec.aumUsd,
            limit: types.Limit.fromDecoded(dec.limit),
            fees: types.Fees.fromDecoded(dec.fees),
            poolApr: types.PoolApr.fromDecoded(dec.poolApr),
            maxRequestExecutionSec: dec.maxRequestExecutionSec,
            bump: dec.bump,
            lpTokenBump: dec.lpTokenBump,
            inceptionTime: dec.inceptionTime,
        });
    }
    toJSON() {
        return {
            name: this.name,
            custodies: this.custodies,
            aumUsd: this.aumUsd.toString(),
            limit: this.limit.toJSON(),
            fees: this.fees.toJSON(),
            poolApr: this.poolApr.toJSON(),
            maxRequestExecutionSec: this.maxRequestExecutionSec.toString(),
            bump: this.bump,
            lpTokenBump: this.lpTokenBump,
            inceptionTime: this.inceptionTime.toString(),
        };
    }
    static fromJSON(obj) {
        return new Pool({
            name: obj.name,
            custodies: obj.custodies.map((item) => (0, kit_1.address)(item)),
            aumUsd: new bn_js_1.default(obj.aumUsd),
            limit: types.Limit.fromJSON(obj.limit),
            fees: types.Fees.fromJSON(obj.fees),
            poolApr: types.PoolApr.fromJSON(obj.poolApr),
            maxRequestExecutionSec: new bn_js_1.default(obj.maxRequestExecutionSec),
            bump: obj.bump,
            lpTokenBump: obj.lpTokenBump,
            inceptionTime: new bn_js_1.default(obj.inceptionTime),
        });
    }
}
exports.Pool = Pool;
//# sourceMappingURL=Pool.js.map