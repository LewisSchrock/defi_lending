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
exports.twapUpdate = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class twapUpdate {
    writeAuthority;
    twap;
    static discriminator = Buffer.from([
        104, 192, 188, 72, 246, 166, 12, 81,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("writeAuthority"),
        types.TwapPrice.layout("twap"),
    ]);
    constructor(fields) {
        this.writeAuthority = fields.writeAuthority;
        this.twap = new types.TwapPrice({ ...fields.twap });
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`twapUpdateFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
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
                throw new Error(`twapUpdateFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(twapUpdate.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = twapUpdate.layout.decode(data.slice(8));
        return new twapUpdate({
            writeAuthority: dec.writeAuthority,
            twap: types.TwapPrice.fromDecoded(dec.twap),
        });
    }
    toJSON() {
        return {
            writeAuthority: this.writeAuthority,
            twap: this.twap.toJSON(),
        };
    }
    static fromJSON(obj) {
        return new twapUpdate({
            writeAuthority: (0, kit_1.address)(obj.writeAuthority),
            twap: types.TwapPrice.fromJSON(obj.twap),
        });
    }
}
exports.twapUpdate = twapUpdate;
//# sourceMappingURL=twapUpdate.js.map