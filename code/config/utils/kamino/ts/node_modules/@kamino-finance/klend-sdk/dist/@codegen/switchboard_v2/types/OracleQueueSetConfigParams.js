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
exports.OracleQueueSetConfigParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class OracleQueueSetConfigParams {
    name;
    metadata;
    unpermissionedFeedsEnabled;
    unpermissionedVrfEnabled;
    enableBufferRelayers;
    varianceToleranceMultiplier;
    slashingEnabled;
    reward;
    minStake;
    oracleTimeout;
    consecutiveFeedFailureLimit;
    consecutiveOracleFailureLimit;
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.unpermissionedFeedsEnabled = fields.unpermissionedFeedsEnabled;
        this.unpermissionedVrfEnabled = fields.unpermissionedVrfEnabled;
        this.enableBufferRelayers = fields.enableBufferRelayers;
        this.varianceToleranceMultiplier =
            (fields.varianceToleranceMultiplier &&
                new types.BorshDecimal({ ...fields.varianceToleranceMultiplier })) ||
                null;
        this.slashingEnabled = fields.slashingEnabled;
        this.reward = fields.reward;
        this.minStake = fields.minStake;
        this.oracleTimeout = fields.oracleTimeout;
        this.consecutiveFeedFailureLimit = fields.consecutiveFeedFailureLimit;
        this.consecutiveOracleFailureLimit = fields.consecutiveOracleFailureLimit;
    }
    static layout(property) {
        return borsh.struct([
            borsh.option(borsh.array(borsh.u8(), 32), "name"),
            borsh.option(borsh.array(borsh.u8(), 64), "metadata"),
            borsh.option(borsh.bool(), "unpermissionedFeedsEnabled"),
            borsh.option(borsh.bool(), "unpermissionedVrfEnabled"),
            borsh.option(borsh.bool(), "enableBufferRelayers"),
            borsh.option(types.BorshDecimal.layout(), "varianceToleranceMultiplier"),
            borsh.option(borsh.bool(), "slashingEnabled"),
            borsh.option(borsh.u64(), "reward"),
            borsh.option(borsh.u64(), "minStake"),
            borsh.option(borsh.u32(), "oracleTimeout"),
            borsh.option(borsh.u64(), "consecutiveFeedFailureLimit"),
            borsh.option(borsh.u64(), "consecutiveOracleFailureLimit"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new OracleQueueSetConfigParams({
            name: obj.name,
            metadata: obj.metadata,
            unpermissionedFeedsEnabled: obj.unpermissionedFeedsEnabled,
            unpermissionedVrfEnabled: obj.unpermissionedVrfEnabled,
            enableBufferRelayers: obj.enableBufferRelayers,
            varianceToleranceMultiplier: (obj.varianceToleranceMultiplier &&
                types.BorshDecimal.fromDecoded(obj.varianceToleranceMultiplier)) ||
                null,
            slashingEnabled: obj.slashingEnabled,
            reward: obj.reward,
            minStake: obj.minStake,
            oracleTimeout: obj.oracleTimeout,
            consecutiveFeedFailureLimit: obj.consecutiveFeedFailureLimit,
            consecutiveOracleFailureLimit: obj.consecutiveOracleFailureLimit,
        });
    }
    static toEncodable(fields) {
        return {
            name: fields.name,
            metadata: fields.metadata,
            unpermissionedFeedsEnabled: fields.unpermissionedFeedsEnabled,
            unpermissionedVrfEnabled: fields.unpermissionedVrfEnabled,
            enableBufferRelayers: fields.enableBufferRelayers,
            varianceToleranceMultiplier: (fields.varianceToleranceMultiplier &&
                types.BorshDecimal.toEncodable(fields.varianceToleranceMultiplier)) ||
                null,
            slashingEnabled: fields.slashingEnabled,
            reward: fields.reward,
            minStake: fields.minStake,
            oracleTimeout: fields.oracleTimeout,
            consecutiveFeedFailureLimit: fields.consecutiveFeedFailureLimit,
            consecutiveOracleFailureLimit: fields.consecutiveOracleFailureLimit,
        };
    }
    toJSON() {
        return {
            name: this.name,
            metadata: this.metadata,
            unpermissionedFeedsEnabled: this.unpermissionedFeedsEnabled,
            unpermissionedVrfEnabled: this.unpermissionedVrfEnabled,
            enableBufferRelayers: this.enableBufferRelayers,
            varianceToleranceMultiplier: (this.varianceToleranceMultiplier &&
                this.varianceToleranceMultiplier.toJSON()) ||
                null,
            slashingEnabled: this.slashingEnabled,
            reward: (this.reward && this.reward.toString()) || null,
            minStake: (this.minStake && this.minStake.toString()) || null,
            oracleTimeout: this.oracleTimeout,
            consecutiveFeedFailureLimit: (this.consecutiveFeedFailureLimit &&
                this.consecutiveFeedFailureLimit.toString()) ||
                null,
            consecutiveOracleFailureLimit: (this.consecutiveOracleFailureLimit &&
                this.consecutiveOracleFailureLimit.toString()) ||
                null,
        };
    }
    static fromJSON(obj) {
        return new OracleQueueSetConfigParams({
            name: obj.name,
            metadata: obj.metadata,
            unpermissionedFeedsEnabled: obj.unpermissionedFeedsEnabled,
            unpermissionedVrfEnabled: obj.unpermissionedVrfEnabled,
            enableBufferRelayers: obj.enableBufferRelayers,
            varianceToleranceMultiplier: (obj.varianceToleranceMultiplier &&
                types.BorshDecimal.fromJSON(obj.varianceToleranceMultiplier)) ||
                null,
            slashingEnabled: obj.slashingEnabled,
            reward: (obj.reward && new bn_js_1.default(obj.reward)) || null,
            minStake: (obj.minStake && new bn_js_1.default(obj.minStake)) || null,
            oracleTimeout: obj.oracleTimeout,
            consecutiveFeedFailureLimit: (obj.consecutiveFeedFailureLimit &&
                new bn_js_1.default(obj.consecutiveFeedFailureLimit)) ||
                null,
            consecutiveOracleFailureLimit: (obj.consecutiveOracleFailureLimit &&
                new bn_js_1.default(obj.consecutiveOracleFailureLimit)) ||
                null,
        });
    }
    toEncodable() {
        return OracleQueueSetConfigParams.toEncodable(this);
    }
}
exports.OracleQueueSetConfigParams = OracleQueueSetConfigParams;
//# sourceMappingURL=OracleQueueSetConfigParams.js.map