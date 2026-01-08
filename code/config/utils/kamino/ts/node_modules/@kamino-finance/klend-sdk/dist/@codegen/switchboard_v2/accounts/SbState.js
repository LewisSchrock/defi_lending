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
exports.SbState = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class SbState {
    authority;
    tokenMint;
    tokenVault;
    daoMint;
    ebuf;
    static discriminator = Buffer.from([
        159, 42, 192, 191, 139, 62, 168, 28,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("authority"),
        (0, utils_1.borshAddress)("tokenMint"),
        (0, utils_1.borshAddress)("tokenVault"),
        (0, utils_1.borshAddress)("daoMint"),
        borsh.array(borsh.u8(), 992, "ebuf"),
    ]);
    constructor(fields) {
        this.authority = fields.authority;
        this.tokenMint = fields.tokenMint;
        this.tokenVault = fields.tokenVault;
        this.daoMint = fields.daoMint;
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
        if (!data.slice(0, 8).equals(SbState.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = SbState.layout.decode(data.slice(8));
        return new SbState({
            authority: dec.authority,
            tokenMint: dec.tokenMint,
            tokenVault: dec.tokenVault,
            daoMint: dec.daoMint,
            ebuf: dec.ebuf,
        });
    }
    toJSON() {
        return {
            authority: this.authority,
            tokenMint: this.tokenMint,
            tokenVault: this.tokenVault,
            daoMint: this.daoMint,
            ebuf: this.ebuf,
        };
    }
    static fromJSON(obj) {
        return new SbState({
            authority: (0, kit_1.address)(obj.authority),
            tokenMint: (0, kit_1.address)(obj.tokenMint),
            tokenVault: (0, kit_1.address)(obj.tokenVault),
            daoMint: (0, kit_1.address)(obj.daoMint),
            ebuf: obj.ebuf,
        });
    }
}
exports.SbState = SbState;
//# sourceMappingURL=SbState.js.map