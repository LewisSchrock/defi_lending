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
exports.ReferrerTokenState = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
/** Referrer account -> each owner can have multiple accounts for specific reserves */
class ReferrerTokenState {
    /** Pubkey of the referrer/owner */
    referrer;
    /** Token mint for the account */
    mint;
    /** Amount that has been accumulated and not claimed yet -> available to claim (scaled fraction) */
    amountUnclaimedSf;
    /** Amount that has been accumulated in total -> both already claimed and unclaimed (scaled fraction) */
    amountCumulativeSf;
    /** Referrer token state bump, used for address validation */
    bump;
    padding;
    static discriminator = Buffer.from([
        39, 15, 208, 77, 32, 195, 105, 56,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("referrer"),
        (0, utils_1.borshAddress)("mint"),
        borsh.u128("amountUnclaimedSf"),
        borsh.u128("amountCumulativeSf"),
        borsh.u64("bump"),
        borsh.array(borsh.u64(), 31, "padding"),
    ]);
    constructor(fields) {
        this.referrer = fields.referrer;
        this.mint = fields.mint;
        this.amountUnclaimedSf = fields.amountUnclaimedSf;
        this.amountCumulativeSf = fields.amountCumulativeSf;
        this.bump = fields.bump;
        this.padding = fields.padding;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`ReferrerTokenStateFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
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
                throw new Error(`ReferrerTokenStateFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(ReferrerTokenState.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = ReferrerTokenState.layout.decode(data.slice(8));
        return new ReferrerTokenState({
            referrer: dec.referrer,
            mint: dec.mint,
            amountUnclaimedSf: dec.amountUnclaimedSf,
            amountCumulativeSf: dec.amountCumulativeSf,
            bump: dec.bump,
            padding: dec.padding,
        });
    }
    toJSON() {
        return {
            referrer: this.referrer,
            mint: this.mint,
            amountUnclaimedSf: this.amountUnclaimedSf.toString(),
            amountCumulativeSf: this.amountCumulativeSf.toString(),
            bump: this.bump.toString(),
            padding: this.padding.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new ReferrerTokenState({
            referrer: (0, kit_1.address)(obj.referrer),
            mint: (0, kit_1.address)(obj.mint),
            amountUnclaimedSf: new bn_js_1.default(obj.amountUnclaimedSf),
            amountCumulativeSf: new bn_js_1.default(obj.amountCumulativeSf),
            bump: new bn_js_1.default(obj.bump),
            padding: obj.padding.map((item) => new bn_js_1.default(item)),
        });
    }
}
exports.ReferrerTokenState = ReferrerTokenState;
//# sourceMappingURL=ReferrerTokenState.js.map