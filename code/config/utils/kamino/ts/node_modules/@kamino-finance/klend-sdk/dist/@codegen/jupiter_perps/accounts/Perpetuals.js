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
exports.Perpetuals = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class Perpetuals {
    permissions;
    pools;
    admin;
    transferAuthorityBump;
    perpetualsBump;
    inceptionTime;
    static discriminator = Buffer.from([
        28, 167, 98, 191, 104, 82, 108, 196,
    ]);
    static layout = borsh.struct([
        types.Permissions.layout("permissions"),
        borsh.vec((0, utils_1.borshAddress)(), "pools"),
        (0, utils_1.borshAddress)("admin"),
        borsh.u8("transferAuthorityBump"),
        borsh.u8("perpetualsBump"),
        borsh.i64("inceptionTime"),
    ]);
    constructor(fields) {
        this.permissions = new types.Permissions({ ...fields.permissions });
        this.pools = fields.pools;
        this.admin = fields.admin;
        this.transferAuthorityBump = fields.transferAuthorityBump;
        this.perpetualsBump = fields.perpetualsBump;
        this.inceptionTime = fields.inceptionTime;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`PerpetualsFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
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
                throw new Error(`PerpetualsFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(Perpetuals.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = Perpetuals.layout.decode(data.slice(8));
        return new Perpetuals({
            permissions: types.Permissions.fromDecoded(dec.permissions),
            pools: dec.pools,
            admin: dec.admin,
            transferAuthorityBump: dec.transferAuthorityBump,
            perpetualsBump: dec.perpetualsBump,
            inceptionTime: dec.inceptionTime,
        });
    }
    toJSON() {
        return {
            permissions: this.permissions.toJSON(),
            pools: this.pools,
            admin: this.admin,
            transferAuthorityBump: this.transferAuthorityBump,
            perpetualsBump: this.perpetualsBump,
            inceptionTime: this.inceptionTime.toString(),
        };
    }
    static fromJSON(obj) {
        return new Perpetuals({
            permissions: types.Permissions.fromJSON(obj.permissions),
            pools: obj.pools.map((item) => (0, kit_1.address)(item)),
            admin: (0, kit_1.address)(obj.admin),
            transferAuthorityBump: obj.transferAuthorityBump,
            perpetualsBump: obj.perpetualsBump,
            inceptionTime: new bn_js_1.default(obj.inceptionTime),
        });
    }
}
exports.Perpetuals = Perpetuals;
//# sourceMappingURL=Perpetuals.js.map