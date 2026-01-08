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
exports.PermissionAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class PermissionAccountData {
    authority;
    permissions;
    granter;
    grantee;
    expiration;
    ebuf;
    static discriminator = Buffer.from([
        77, 37, 177, 164, 38, 39, 34, 109,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("authority"),
        borsh.u32("permissions"),
        (0, utils_1.borshAddress)("granter"),
        (0, utils_1.borshAddress)("grantee"),
        borsh.i64("expiration"),
        borsh.array(borsh.u8(), 256, "ebuf"),
    ]);
    constructor(fields) {
        this.authority = fields.authority;
        this.permissions = fields.permissions;
        this.granter = fields.granter;
        this.grantee = fields.grantee;
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
        if (!data.slice(0, 8).equals(PermissionAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = PermissionAccountData.layout.decode(data.slice(8));
        return new PermissionAccountData({
            authority: dec.authority,
            permissions: dec.permissions,
            granter: dec.granter,
            grantee: dec.grantee,
            expiration: dec.expiration,
            ebuf: dec.ebuf,
        });
    }
    toJSON() {
        return {
            authority: this.authority,
            permissions: this.permissions,
            granter: this.granter,
            grantee: this.grantee,
            expiration: this.expiration.toString(),
            ebuf: this.ebuf,
        };
    }
    static fromJSON(obj) {
        return new PermissionAccountData({
            authority: (0, kit_1.address)(obj.authority),
            permissions: obj.permissions,
            granter: (0, kit_1.address)(obj.granter),
            grantee: (0, kit_1.address)(obj.grantee),
            expiration: new bn_js_1.default(obj.expiration),
            ebuf: obj.ebuf,
        });
    }
}
exports.PermissionAccountData = PermissionAccountData;
//# sourceMappingURL=PermissionAccountData.js.map