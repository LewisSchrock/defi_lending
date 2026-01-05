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
exports.VrfLiteAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class VrfLiteAccountData {
    stateBump;
    permissionBump;
    vrfPool;
    status;
    result;
    counter;
    alpha;
    alphaLen;
    requestSlot;
    requestTimestamp;
    authority;
    queue;
    escrow;
    callback;
    builder;
    expiration;
    ebuf;
    static discriminator = Buffer.from([
        98, 127, 126, 124, 166, 81, 97, 100,
    ]);
    static layout = borsh.struct([
        borsh.u8("stateBump"),
        borsh.u8("permissionBump"),
        (0, utils_1.borshAddress)("vrfPool"),
        types.VrfStatus.layout("status"),
        borsh.array(borsh.u8(), 32, "result"),
        borsh.u128("counter"),
        borsh.array(borsh.u8(), 256, "alpha"),
        borsh.u32("alphaLen"),
        borsh.u64("requestSlot"),
        borsh.i64("requestTimestamp"),
        (0, utils_1.borshAddress)("authority"),
        (0, utils_1.borshAddress)("queue"),
        (0, utils_1.borshAddress)("escrow"),
        types.CallbackZC.layout("callback"),
        types.VrfBuilder.layout("builder"),
        borsh.i64("expiration"),
        borsh.array(borsh.u8(), 1024, "ebuf"),
    ]);
    constructor(fields) {
        this.stateBump = fields.stateBump;
        this.permissionBump = fields.permissionBump;
        this.vrfPool = fields.vrfPool;
        this.status = fields.status;
        this.result = fields.result;
        this.counter = fields.counter;
        this.alpha = fields.alpha;
        this.alphaLen = fields.alphaLen;
        this.requestSlot = fields.requestSlot;
        this.requestTimestamp = fields.requestTimestamp;
        this.authority = fields.authority;
        this.queue = fields.queue;
        this.escrow = fields.escrow;
        this.callback = new types.CallbackZC({ ...fields.callback });
        this.builder = new types.VrfBuilder({ ...fields.builder });
        this.expiration = fields.expiration;
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
        if (!data.slice(0, 8).equals(VrfLiteAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = VrfLiteAccountData.layout.decode(data.slice(8));
        return new VrfLiteAccountData({
            stateBump: dec.stateBump,
            permissionBump: dec.permissionBump,
            vrfPool: dec.vrfPool,
            status: types.VrfStatus.fromDecoded(dec.status),
            result: dec.result,
            counter: dec.counter,
            alpha: dec.alpha,
            alphaLen: dec.alphaLen,
            requestSlot: dec.requestSlot,
            requestTimestamp: dec.requestTimestamp,
            authority: dec.authority,
            queue: dec.queue,
            escrow: dec.escrow,
            callback: types.CallbackZC.fromDecoded(dec.callback),
            builder: types.VrfBuilder.fromDecoded(dec.builder),
            expiration: dec.expiration,
            ebuf: dec.ebuf,
        });
    }
    toJSON() {
        return {
            stateBump: this.stateBump,
            permissionBump: this.permissionBump,
            vrfPool: this.vrfPool,
            status: this.status.toJSON(),
            result: this.result,
            counter: this.counter.toString(),
            alpha: this.alpha,
            alphaLen: this.alphaLen,
            requestSlot: this.requestSlot.toString(),
            requestTimestamp: this.requestTimestamp.toString(),
            authority: this.authority,
            queue: this.queue,
            escrow: this.escrow,
            callback: this.callback.toJSON(),
            builder: this.builder.toJSON(),
            expiration: this.expiration.toString(),
            ebuf: this.ebuf,
        };
    }
    static fromJSON(obj) {
        return new VrfLiteAccountData({
            stateBump: obj.stateBump,
            permissionBump: obj.permissionBump,
            vrfPool: (0, kit_1.address)(obj.vrfPool),
            status: types.VrfStatus.fromJSON(obj.status),
            result: obj.result,
            counter: new bn_js_1.default(obj.counter),
            alpha: obj.alpha,
            alphaLen: obj.alphaLen,
            requestSlot: new bn_js_1.default(obj.requestSlot),
            requestTimestamp: new bn_js_1.default(obj.requestTimestamp),
            authority: (0, kit_1.address)(obj.authority),
            queue: (0, kit_1.address)(obj.queue),
            escrow: (0, kit_1.address)(obj.escrow),
            callback: types.CallbackZC.fromJSON(obj.callback),
            builder: types.VrfBuilder.fromJSON(obj.builder),
            expiration: new bn_js_1.default(obj.expiration),
            ebuf: obj.ebuf,
        });
    }
}
exports.VrfLiteAccountData = VrfLiteAccountData;
//# sourceMappingURL=VrfLiteAccountData.js.map