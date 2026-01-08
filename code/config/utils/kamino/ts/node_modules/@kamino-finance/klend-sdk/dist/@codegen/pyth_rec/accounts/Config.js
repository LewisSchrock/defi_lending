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
exports.Config = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class Config {
    governanceAuthority;
    targetGovernanceAuthority;
    wormhole;
    validDataSources;
    singleUpdateFeeInLamports;
    minimumSignatures;
    static discriminator = Buffer.from([
        155, 12, 170, 224, 30, 250, 204, 130,
    ]);
    static layout = borsh.struct([
        (0, utils_1.borshAddress)("governanceAuthority"),
        borsh.option((0, utils_1.borshAddress)(), "targetGovernanceAuthority"),
        (0, utils_1.borshAddress)("wormhole"),
        borsh.vec(types.DataSource.layout(), "validDataSources"),
        borsh.u64("singleUpdateFeeInLamports"),
        borsh.u8("minimumSignatures"),
    ]);
    constructor(fields) {
        this.governanceAuthority = fields.governanceAuthority;
        this.targetGovernanceAuthority = fields.targetGovernanceAuthority;
        this.wormhole = fields.wormhole;
        this.validDataSources = fields.validDataSources.map((item) => new types.DataSource({ ...item }));
        this.singleUpdateFeeInLamports = fields.singleUpdateFeeInLamports;
        this.minimumSignatures = fields.minimumSignatures;
    }
    static async fetch(rpc, address, programId = programId_1.PROGRAM_ID) {
        const info = await (0, kit_1.fetchEncodedAccount)(rpc, address);
        if (!info.exists) {
            return null;
        }
        if (info.programAddress !== programId) {
            throw new Error(`ConfigFields account ${address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
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
                throw new Error(`ConfigFields account ${info.address} belongs to wrong program ${info.programAddress}, expected ${programId}`);
            }
            return this.decode(Buffer.from(info.data));
        });
    }
    static decode(data) {
        if (!data.slice(0, 8).equals(Config.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = Config.layout.decode(data.slice(8));
        return new Config({
            governanceAuthority: dec.governanceAuthority,
            targetGovernanceAuthority: dec.targetGovernanceAuthority,
            wormhole: dec.wormhole,
            validDataSources: dec.validDataSources.map((item /* eslint-disable-line @typescript-eslint/no-explicit-any */) => types.DataSource.fromDecoded(item)),
            singleUpdateFeeInLamports: dec.singleUpdateFeeInLamports,
            minimumSignatures: dec.minimumSignatures,
        });
    }
    toJSON() {
        return {
            governanceAuthority: this.governanceAuthority,
            targetGovernanceAuthority: this.targetGovernanceAuthority,
            wormhole: this.wormhole,
            validDataSources: this.validDataSources.map((item) => item.toJSON()),
            singleUpdateFeeInLamports: this.singleUpdateFeeInLamports.toString(),
            minimumSignatures: this.minimumSignatures,
        };
    }
    static fromJSON(obj) {
        return new Config({
            governanceAuthority: (0, kit_1.address)(obj.governanceAuthority),
            targetGovernanceAuthority: (obj.targetGovernanceAuthority &&
                (0, kit_1.address)(obj.targetGovernanceAuthority)) ||
                null,
            wormhole: (0, kit_1.address)(obj.wormhole),
            validDataSources: obj.validDataSources.map((item) => types.DataSource.fromJSON(item)),
            singleUpdateFeeInLamports: new bn_js_1.default(obj.singleUpdateFeeInLamports),
            minimumSignatures: obj.minimumSignatures,
        });
    }
}
exports.Config = Config;
//# sourceMappingURL=Config.js.map