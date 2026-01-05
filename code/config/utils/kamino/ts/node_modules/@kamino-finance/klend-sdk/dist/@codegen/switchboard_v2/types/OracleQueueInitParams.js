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
exports.OracleQueueInitParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class OracleQueueInitParams {
    name;
    metadata;
    reward;
    minStake;
    feedProbationPeriod;
    oracleTimeout;
    slashingEnabled;
    varianceToleranceMultiplier;
    consecutiveFeedFailureLimit;
    consecutiveOracleFailureLimit;
    queueSize;
    unpermissionedFeeds;
    unpermissionedVrf;
    enableBufferRelayers;
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.reward = fields.reward;
        this.minStake = fields.minStake;
        this.feedProbationPeriod = fields.feedProbationPeriod;
        this.oracleTimeout = fields.oracleTimeout;
        this.slashingEnabled = fields.slashingEnabled;
        this.varianceToleranceMultiplier = new types.BorshDecimal({
            ...fields.varianceToleranceMultiplier,
        });
        this.consecutiveFeedFailureLimit = fields.consecutiveFeedFailureLimit;
        this.consecutiveOracleFailureLimit = fields.consecutiveOracleFailureLimit;
        this.queueSize = fields.queueSize;
        this.unpermissionedFeeds = fields.unpermissionedFeeds;
        this.unpermissionedVrf = fields.unpermissionedVrf;
        this.enableBufferRelayers = fields.enableBufferRelayers;
    }
    static layout(property) {
        return borsh.struct([
            borsh.array(borsh.u8(), 32, "name"),
            borsh.array(borsh.u8(), 64, "metadata"),
            borsh.u64("reward"),
            borsh.u64("minStake"),
            borsh.u32("feedProbationPeriod"),
            borsh.u32("oracleTimeout"),
            borsh.bool("slashingEnabled"),
            types.BorshDecimal.layout("varianceToleranceMultiplier"),
            borsh.u64("consecutiveFeedFailureLimit"),
            borsh.u64("consecutiveOracleFailureLimit"),
            borsh.u32("queueSize"),
            borsh.bool("unpermissionedFeeds"),
            borsh.bool("unpermissionedVrf"),
            borsh.bool("enableBufferRelayers"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new OracleQueueInitParams({
            name: obj.name,
            metadata: obj.metadata,
            reward: obj.reward,
            minStake: obj.minStake,
            feedProbationPeriod: obj.feedProbationPeriod,
            oracleTimeout: obj.oracleTimeout,
            slashingEnabled: obj.slashingEnabled,
            varianceToleranceMultiplier: types.BorshDecimal.fromDecoded(obj.varianceToleranceMultiplier),
            consecutiveFeedFailureLimit: obj.consecutiveFeedFailureLimit,
            consecutiveOracleFailureLimit: obj.consecutiveOracleFailureLimit,
            queueSize: obj.queueSize,
            unpermissionedFeeds: obj.unpermissionedFeeds,
            unpermissionedVrf: obj.unpermissionedVrf,
            enableBufferRelayers: obj.enableBufferRelayers,
        });
    }
    static toEncodable(fields) {
        return {
            name: fields.name,
            metadata: fields.metadata,
            reward: fields.reward,
            minStake: fields.minStake,
            feedProbationPeriod: fields.feedProbationPeriod,
            oracleTimeout: fields.oracleTimeout,
            slashingEnabled: fields.slashingEnabled,
            varianceToleranceMultiplier: types.BorshDecimal.toEncodable(fields.varianceToleranceMultiplier),
            consecutiveFeedFailureLimit: fields.consecutiveFeedFailureLimit,
            consecutiveOracleFailureLimit: fields.consecutiveOracleFailureLimit,
            queueSize: fields.queueSize,
            unpermissionedFeeds: fields.unpermissionedFeeds,
            unpermissionedVrf: fields.unpermissionedVrf,
            enableBufferRelayers: fields.enableBufferRelayers,
        };
    }
    toJSON() {
        return {
            name: this.name,
            metadata: this.metadata,
            reward: this.reward.toString(),
            minStake: this.minStake.toString(),
            feedProbationPeriod: this.feedProbationPeriod,
            oracleTimeout: this.oracleTimeout,
            slashingEnabled: this.slashingEnabled,
            varianceToleranceMultiplier: this.varianceToleranceMultiplier.toJSON(),
            consecutiveFeedFailureLimit: this.consecutiveFeedFailureLimit.toString(),
            consecutiveOracleFailureLimit: this.consecutiveOracleFailureLimit.toString(),
            queueSize: this.queueSize,
            unpermissionedFeeds: this.unpermissionedFeeds,
            unpermissionedVrf: this.unpermissionedVrf,
            enableBufferRelayers: this.enableBufferRelayers,
        };
    }
    static fromJSON(obj) {
        return new OracleQueueInitParams({
            name: obj.name,
            metadata: obj.metadata,
            reward: new bn_js_1.default(obj.reward),
            minStake: new bn_js_1.default(obj.minStake),
            feedProbationPeriod: obj.feedProbationPeriod,
            oracleTimeout: obj.oracleTimeout,
            slashingEnabled: obj.slashingEnabled,
            varianceToleranceMultiplier: types.BorshDecimal.fromJSON(obj.varianceToleranceMultiplier),
            consecutiveFeedFailureLimit: new bn_js_1.default(obj.consecutiveFeedFailureLimit),
            consecutiveOracleFailureLimit: new bn_js_1.default(obj.consecutiveOracleFailureLimit),
            queueSize: obj.queueSize,
            unpermissionedFeeds: obj.unpermissionedFeeds,
            unpermissionedVrf: obj.unpermissionedVrf,
            enableBufferRelayers: obj.enableBufferRelayers,
        });
    }
    toEncodable() {
        return OracleQueueInitParams.toEncodable(this);
    }
}
exports.OracleQueueInitParams = OracleQueueInitParams;
//# sourceMappingURL=OracleQueueInitParams.js.map