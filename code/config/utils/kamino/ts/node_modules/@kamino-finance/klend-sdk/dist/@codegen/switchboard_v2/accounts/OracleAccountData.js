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
exports.OracleAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class OracleAccountData {
    name;
    metadata;
    oracleAuthority;
    lastHeartbeat;
    numInUse;
    tokenAccount;
    queuePubkey;
    metrics;
    ebuf;
    static discriminator = Buffer.from([
        128, 30, 16, 241, 170, 73, 55, 54,
    ]);
    static layout = borsh.struct([
        borsh.array(borsh.u8(), 32, "name"),
        borsh.array(borsh.u8(), 128, "metadata"),
        (0, utils_1.borshAddress)("oracleAuthority"),
        borsh.i64("lastHeartbeat"),
        borsh.u32("numInUse"),
        (0, utils_1.borshAddress)("tokenAccount"),
        (0, utils_1.borshAddress)("queuePubkey"),
        types.OracleMetrics.layout("metrics"),
        borsh.array(borsh.u8(), 256, "ebuf"),
    ]);
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.oracleAuthority = fields.oracleAuthority;
        this.lastHeartbeat = fields.lastHeartbeat;
        this.numInUse = fields.numInUse;
        this.tokenAccount = fields.tokenAccount;
        this.queuePubkey = fields.queuePubkey;
        this.metrics = new types.OracleMetrics({ ...fields.metrics });
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
        if (!data.slice(0, 8).equals(OracleAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = OracleAccountData.layout.decode(data.slice(8));
        return new OracleAccountData({
            name: dec.name,
            metadata: dec.metadata,
            oracleAuthority: dec.oracleAuthority,
            lastHeartbeat: dec.lastHeartbeat,
            numInUse: dec.numInUse,
            tokenAccount: dec.tokenAccount,
            queuePubkey: dec.queuePubkey,
            metrics: types.OracleMetrics.fromDecoded(dec.metrics),
            ebuf: dec.ebuf,
        });
    }
    toJSON() {
        return {
            name: this.name,
            metadata: this.metadata,
            oracleAuthority: this.oracleAuthority,
            lastHeartbeat: this.lastHeartbeat.toString(),
            numInUse: this.numInUse,
            tokenAccount: this.tokenAccount,
            queuePubkey: this.queuePubkey,
            metrics: this.metrics.toJSON(),
            ebuf: this.ebuf,
        };
    }
    static fromJSON(obj) {
        return new OracleAccountData({
            name: obj.name,
            metadata: obj.metadata,
            oracleAuthority: (0, kit_1.address)(obj.oracleAuthority),
            lastHeartbeat: new bn_js_1.default(obj.lastHeartbeat),
            numInUse: obj.numInUse,
            tokenAccount: (0, kit_1.address)(obj.tokenAccount),
            queuePubkey: (0, kit_1.address)(obj.queuePubkey),
            metrics: types.OracleMetrics.fromJSON(obj.metrics),
            ebuf: obj.ebuf,
        });
    }
}
exports.OracleAccountData = OracleAccountData;
//# sourceMappingURL=OracleAccountData.js.map