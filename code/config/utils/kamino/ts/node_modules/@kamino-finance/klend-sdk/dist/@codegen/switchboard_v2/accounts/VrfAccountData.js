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
exports.VrfAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class VrfAccountData {
    status;
    counter;
    authority;
    oracleQueue;
    escrow;
    callback;
    batchSize;
    builders;
    buildersLen;
    testMode;
    currentRound;
    ebuf;
    static discriminator = Buffer.from([
        101, 35, 62, 239, 103, 151, 6, 18,
    ]);
    static layout = borsh.struct([
        types.VrfStatus.layout("status"),
        borsh.u128("counter"),
        (0, utils_1.borshAddress)("authority"),
        (0, utils_1.borshAddress)("oracleQueue"),
        (0, utils_1.borshAddress)("escrow"),
        types.CallbackZC.layout("callback"),
        borsh.u32("batchSize"),
        borsh.array(types.VrfBuilder.layout(), 8, "builders"),
        borsh.u32("buildersLen"),
        borsh.bool("testMode"),
        types.VrfRound.layout("currentRound"),
        borsh.array(borsh.u8(), 1024, "ebuf"),
    ]);
    constructor(fields) {
        this.status = fields.status;
        this.counter = fields.counter;
        this.authority = fields.authority;
        this.oracleQueue = fields.oracleQueue;
        this.escrow = fields.escrow;
        this.callback = new types.CallbackZC({ ...fields.callback });
        this.batchSize = fields.batchSize;
        this.builders = fields.builders.map((item) => new types.VrfBuilder({ ...item }));
        this.buildersLen = fields.buildersLen;
        this.testMode = fields.testMode;
        this.currentRound = new types.VrfRound({ ...fields.currentRound });
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
        if (!data.slice(0, 8).equals(VrfAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = VrfAccountData.layout.decode(data.slice(8));
        return new VrfAccountData({
            status: types.VrfStatus.fromDecoded(dec.status),
            counter: dec.counter,
            authority: dec.authority,
            oracleQueue: dec.oracleQueue,
            escrow: dec.escrow,
            callback: types.CallbackZC.fromDecoded(dec.callback),
            batchSize: dec.batchSize,
            builders: dec.builders.map((item /* eslint-disable-line @typescript-eslint/no-explicit-any */) => types.VrfBuilder.fromDecoded(item)),
            buildersLen: dec.buildersLen,
            testMode: dec.testMode,
            currentRound: types.VrfRound.fromDecoded(dec.currentRound),
            ebuf: dec.ebuf,
        });
    }
    toJSON() {
        return {
            status: this.status.toJSON(),
            counter: this.counter.toString(),
            authority: this.authority,
            oracleQueue: this.oracleQueue,
            escrow: this.escrow,
            callback: this.callback.toJSON(),
            batchSize: this.batchSize,
            builders: this.builders.map((item) => item.toJSON()),
            buildersLen: this.buildersLen,
            testMode: this.testMode,
            currentRound: this.currentRound.toJSON(),
            ebuf: this.ebuf,
        };
    }
    static fromJSON(obj) {
        return new VrfAccountData({
            status: types.VrfStatus.fromJSON(obj.status),
            counter: new bn_js_1.default(obj.counter),
            authority: (0, kit_1.address)(obj.authority),
            oracleQueue: (0, kit_1.address)(obj.oracleQueue),
            escrow: (0, kit_1.address)(obj.escrow),
            callback: types.CallbackZC.fromJSON(obj.callback),
            batchSize: obj.batchSize,
            builders: obj.builders.map((item) => types.VrfBuilder.fromJSON(item)),
            buildersLen: obj.buildersLen,
            testMode: obj.testMode,
            currentRound: types.VrfRound.fromJSON(obj.currentRound),
            ebuf: obj.ebuf,
        });
    }
}
exports.VrfAccountData = VrfAccountData;
//# sourceMappingURL=VrfAccountData.js.map