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
exports.UserMetadata = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
/** Referrer account -> each owner can have multiple accounts for specific reserves */
class UserMetadata {
    /** Pubkey of the referrer/owner - pubkey::default if no referrer */
    referrer;
    /** Bump used for validation of account address */
    bump;
    /** User lookup table - used to store all user accounts - atas for each reserve mint, each obligation PDA, UserMetadata itself and all referrer_token_states if there is a referrer */
    userLookupTable;
    /** User metadata account owner */
    owner;
    padding1;
    padding2;
    static discriminator = Buffer.from([
        157, 214, 220, 235, 98, 135, 171, 28,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("referrer"),
        borsh.u64("bump"),
        (0, utils_1.borshAddress)("userLookupTable"),
        (0, utils_1.borshAddress)("owner"),
        borsh.array(borsh.u64(), 51, "padding1"),
        borsh.array(borsh.u64(), 64, "padding2"),
    ]);
    constructor(fields) {
        this.referrer = fields.referrer;
        this.bump = fields.bump;
        this.userLookupTable = fields.userLookupTable;
        this.owner = fields.owner;
        this.padding1 = fields.padding1;
        this.padding2 = fields.padding2;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`UserMetadataFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
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
                throw new Error(`UserMetadataFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(UserMetadata.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = UserMetadata.layout.decode(data.slice(8));
        return new UserMetadata({
            referrer: dec.referrer,
            bump: dec.bump,
            userLookupTable: dec.userLookupTable,
            owner: dec.owner,
            padding1: dec.padding1,
            padding2: dec.padding2,
        });
    }
    toJSON() {
        return {
            referrer: this.referrer,
            bump: this.bump.toString(),
            userLookupTable: this.userLookupTable,
            owner: this.owner,
            padding1: this.padding1.map((item) => item.toString()),
            padding2: this.padding2.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new UserMetadata({
            referrer: (0, kit_1.address)(obj.referrer),
            bump: new bn_js_1.default(obj.bump),
            userLookupTable: (0, kit_1.address)(obj.userLookupTable),
            owner: (0, kit_1.address)(obj.owner),
            padding1: obj.padding1.map((item) => new bn_js_1.default(item)),
            padding2: obj.padding2.map((item) => new bn_js_1.default(item)),
        });
    }
}
exports.UserMetadata = UserMetadata;
//# sourceMappingURL=UserMetadata.js.map