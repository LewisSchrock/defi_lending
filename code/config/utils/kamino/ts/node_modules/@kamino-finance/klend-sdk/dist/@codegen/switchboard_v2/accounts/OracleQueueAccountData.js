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
exports.OracleQueueAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class OracleQueueAccountData {
    name;
    metadata;
    authority;
    oracleTimeout;
    reward;
    minStake;
    slashingEnabled;
    varianceToleranceMultiplier;
    feedProbationPeriod;
    currIdx;
    size;
    gcIdx;
    consecutiveFeedFailureLimit;
    consecutiveOracleFailureLimit;
    unpermissionedFeedsEnabled;
    unpermissionedVrfEnabled;
    curatorRewardCut;
    lockLeaseFunding;
    mint;
    enableBufferRelayers;
    ebuf;
    maxSize;
    dataBuffer;
    static discriminator = Buffer.from([
        164, 207, 200, 51, 199, 113, 35, 109,
    ]);
    static layout = borsh.struct([
        borsh.array(borsh.u8(), 32, "name"),
        borsh.array(borsh.u8(), 64, "metadata"),
        (0, utils_1.borshAddress)("authority"),
        borsh.u32("oracleTimeout"),
        borsh.u64("reward"),
        borsh.u64("minStake"),
        borsh.bool("slashingEnabled"),
        types.SwitchboardDecimal.layout("varianceToleranceMultiplier"),
        borsh.u32("feedProbationPeriod"),
        borsh.u32("currIdx"),
        borsh.u32("size"),
        borsh.u32("gcIdx"),
        borsh.u64("consecutiveFeedFailureLimit"),
        borsh.u64("consecutiveOracleFailureLimit"),
        borsh.bool("unpermissionedFeedsEnabled"),
        borsh.bool("unpermissionedVrfEnabled"),
        types.SwitchboardDecimal.layout("curatorRewardCut"),
        borsh.bool("lockLeaseFunding"),
        (0, utils_1.borshAddress)("mint"),
        borsh.bool("enableBufferRelayers"),
        borsh.array(borsh.u8(), 968, "ebuf"),
        borsh.u32("maxSize"),
        (0, utils_1.borshAddress)("dataBuffer"),
    ]);
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.authority = fields.authority;
        this.oracleTimeout = fields.oracleTimeout;
        this.reward = fields.reward;
        this.minStake = fields.minStake;
        this.slashingEnabled = fields.slashingEnabled;
        this.varianceToleranceMultiplier = new types.SwitchboardDecimal({
            ...fields.varianceToleranceMultiplier,
        });
        this.feedProbationPeriod = fields.feedProbationPeriod;
        this.currIdx = fields.currIdx;
        this.size = fields.size;
        this.gcIdx = fields.gcIdx;
        this.consecutiveFeedFailureLimit = fields.consecutiveFeedFailureLimit;
        this.consecutiveOracleFailureLimit = fields.consecutiveOracleFailureLimit;
        this.unpermissionedFeedsEnabled = fields.unpermissionedFeedsEnabled;
        this.unpermissionedVrfEnabled = fields.unpermissionedVrfEnabled;
        this.curatorRewardCut = new types.SwitchboardDecimal({
            ...fields.curatorRewardCut,
        });
        this.lockLeaseFunding = fields.lockLeaseFunding;
        this.mint = fields.mint;
        this.enableBufferRelayers = fields.enableBufferRelayers;
        this.ebuf = fields.ebuf;
        this.maxSize = fields.maxSize;
        this.dataBuffer = fields.dataBuffer;
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
        if (!data.slice(0, 8).equals(OracleQueueAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = OracleQueueAccountData.layout.decode(data.slice(8));
        return new OracleQueueAccountData({
            name: dec.name,
            metadata: dec.metadata,
            authority: dec.authority,
            oracleTimeout: dec.oracleTimeout,
            reward: dec.reward,
            minStake: dec.minStake,
            slashingEnabled: dec.slashingEnabled,
            varianceToleranceMultiplier: types.SwitchboardDecimal.fromDecoded(dec.varianceToleranceMultiplier),
            feedProbationPeriod: dec.feedProbationPeriod,
            currIdx: dec.currIdx,
            size: dec.size,
            gcIdx: dec.gcIdx,
            consecutiveFeedFailureLimit: dec.consecutiveFeedFailureLimit,
            consecutiveOracleFailureLimit: dec.consecutiveOracleFailureLimit,
            unpermissionedFeedsEnabled: dec.unpermissionedFeedsEnabled,
            unpermissionedVrfEnabled: dec.unpermissionedVrfEnabled,
            curatorRewardCut: types.SwitchboardDecimal.fromDecoded(dec.curatorRewardCut),
            lockLeaseFunding: dec.lockLeaseFunding,
            mint: dec.mint,
            enableBufferRelayers: dec.enableBufferRelayers,
            ebuf: dec.ebuf,
            maxSize: dec.maxSize,
            dataBuffer: dec.dataBuffer,
        });
    }
    toJSON() {
        return {
            name: this.name,
            metadata: this.metadata,
            authority: this.authority,
            oracleTimeout: this.oracleTimeout,
            reward: this.reward.toString(),
            minStake: this.minStake.toString(),
            slashingEnabled: this.slashingEnabled,
            varianceToleranceMultiplier: this.varianceToleranceMultiplier.toJSON(),
            feedProbationPeriod: this.feedProbationPeriod,
            currIdx: this.currIdx,
            size: this.size,
            gcIdx: this.gcIdx,
            consecutiveFeedFailureLimit: this.consecutiveFeedFailureLimit.toString(),
            consecutiveOracleFailureLimit: this.consecutiveOracleFailureLimit.toString(),
            unpermissionedFeedsEnabled: this.unpermissionedFeedsEnabled,
            unpermissionedVrfEnabled: this.unpermissionedVrfEnabled,
            curatorRewardCut: this.curatorRewardCut.toJSON(),
            lockLeaseFunding: this.lockLeaseFunding,
            mint: this.mint,
            enableBufferRelayers: this.enableBufferRelayers,
            ebuf: this.ebuf,
            maxSize: this.maxSize,
            dataBuffer: this.dataBuffer,
        };
    }
    static fromJSON(obj) {
        return new OracleQueueAccountData({
            name: obj.name,
            metadata: obj.metadata,
            authority: (0, kit_1.address)(obj.authority),
            oracleTimeout: obj.oracleTimeout,
            reward: new bn_js_1.default(obj.reward),
            minStake: new bn_js_1.default(obj.minStake),
            slashingEnabled: obj.slashingEnabled,
            varianceToleranceMultiplier: types.SwitchboardDecimal.fromJSON(obj.varianceToleranceMultiplier),
            feedProbationPeriod: obj.feedProbationPeriod,
            currIdx: obj.currIdx,
            size: obj.size,
            gcIdx: obj.gcIdx,
            consecutiveFeedFailureLimit: new bn_js_1.default(obj.consecutiveFeedFailureLimit),
            consecutiveOracleFailureLimit: new bn_js_1.default(obj.consecutiveOracleFailureLimit),
            unpermissionedFeedsEnabled: obj.unpermissionedFeedsEnabled,
            unpermissionedVrfEnabled: obj.unpermissionedVrfEnabled,
            curatorRewardCut: types.SwitchboardDecimal.fromJSON(obj.curatorRewardCut),
            lockLeaseFunding: obj.lockLeaseFunding,
            mint: (0, kit_1.address)(obj.mint),
            enableBufferRelayers: obj.enableBufferRelayers,
            ebuf: obj.ebuf,
            maxSize: obj.maxSize,
            dataBuffer: (0, kit_1.address)(obj.dataBuffer),
        });
    }
}
exports.OracleQueueAccountData = OracleQueueAccountData;
//# sourceMappingURL=OracleQueueAccountData.js.map