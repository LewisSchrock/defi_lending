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
exports.Position = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class Position {
    owner;
    pool;
    custody;
    collateralCustody;
    openTime;
    updateTime;
    side;
    price;
    sizeUsd;
    collateralUsd;
    realisedPnlUsd;
    cumulativeInterestSnapshot;
    lockedAmount;
    bump;
    static discriminator = Buffer.from([
        170, 188, 143, 228, 122, 64, 247, 208,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("owner"),
        (0, utils_1.borshAddress)("pool"),
        (0, utils_1.borshAddress)("custody"),
        (0, utils_1.borshAddress)("collateralCustody"),
        borsh.i64("openTime"),
        borsh.i64("updateTime"),
        types.Side.layout("side"),
        borsh.u64("price"),
        borsh.u64("sizeUsd"),
        borsh.u64("collateralUsd"),
        borsh.i64("realisedPnlUsd"),
        borsh.u128("cumulativeInterestSnapshot"),
        borsh.u64("lockedAmount"),
        borsh.u8("bump"),
    ]);
    constructor(fields) {
        this.owner = fields.owner;
        this.pool = fields.pool;
        this.custody = fields.custody;
        this.collateralCustody = fields.collateralCustody;
        this.openTime = fields.openTime;
        this.updateTime = fields.updateTime;
        this.side = fields.side;
        this.price = fields.price;
        this.sizeUsd = fields.sizeUsd;
        this.collateralUsd = fields.collateralUsd;
        this.realisedPnlUsd = fields.realisedPnlUsd;
        this.cumulativeInterestSnapshot = fields.cumulativeInterestSnapshot;
        this.lockedAmount = fields.lockedAmount;
        this.bump = fields.bump;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`PositionFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
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
                throw new Error(`PositionFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(Position.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = Position.layout.decode(data.slice(8));
        return new Position({
            owner: dec.owner,
            pool: dec.pool,
            custody: dec.custody,
            collateralCustody: dec.collateralCustody,
            openTime: dec.openTime,
            updateTime: dec.updateTime,
            side: types.Side.fromDecoded(dec.side),
            price: dec.price,
            sizeUsd: dec.sizeUsd,
            collateralUsd: dec.collateralUsd,
            realisedPnlUsd: dec.realisedPnlUsd,
            cumulativeInterestSnapshot: dec.cumulativeInterestSnapshot,
            lockedAmount: dec.lockedAmount,
            bump: dec.bump,
        });
    }
    toJSON() {
        return {
            owner: this.owner,
            pool: this.pool,
            custody: this.custody,
            collateralCustody: this.collateralCustody,
            openTime: this.openTime.toString(),
            updateTime: this.updateTime.toString(),
            side: this.side.toJSON(),
            price: this.price.toString(),
            sizeUsd: this.sizeUsd.toString(),
            collateralUsd: this.collateralUsd.toString(),
            realisedPnlUsd: this.realisedPnlUsd.toString(),
            cumulativeInterestSnapshot: this.cumulativeInterestSnapshot.toString(),
            lockedAmount: this.lockedAmount.toString(),
            bump: this.bump,
        };
    }
    static fromJSON(obj) {
        return new Position({
            owner: (0, kit_1.address)(obj.owner),
            pool: (0, kit_1.address)(obj.pool),
            custody: (0, kit_1.address)(obj.custody),
            collateralCustody: (0, kit_1.address)(obj.collateralCustody),
            openTime: new bn_js_1.default(obj.openTime),
            updateTime: new bn_js_1.default(obj.updateTime),
            side: types.Side.fromJSON(obj.side),
            price: new bn_js_1.default(obj.price),
            sizeUsd: new bn_js_1.default(obj.sizeUsd),
            collateralUsd: new bn_js_1.default(obj.collateralUsd),
            realisedPnlUsd: new bn_js_1.default(obj.realisedPnlUsd),
            cumulativeInterestSnapshot: new bn_js_1.default(obj.cumulativeInterestSnapshot),
            lockedAmount: new bn_js_1.default(obj.lockedAmount),
            bump: obj.bump,
        });
    }
}
exports.Position = Position;
//# sourceMappingURL=Position.js.map