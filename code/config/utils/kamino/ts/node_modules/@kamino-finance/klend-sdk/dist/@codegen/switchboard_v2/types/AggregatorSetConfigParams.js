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
exports.AggregatorSetConfigParams = void 0;
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class AggregatorSetConfigParams {
    name;
    metadata;
    minUpdateDelaySeconds;
    minJobResults;
    batchSize;
    minOracleResults;
    forceReportPeriod;
    varianceThreshold;
    basePriorityFee;
    priorityFeeBump;
    priorityFeeBumpPeriod;
    maxPriorityFeeMultiplier;
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.minUpdateDelaySeconds = fields.minUpdateDelaySeconds;
        this.minJobResults = fields.minJobResults;
        this.batchSize = fields.batchSize;
        this.minOracleResults = fields.minOracleResults;
        this.forceReportPeriod = fields.forceReportPeriod;
        this.varianceThreshold =
            (fields.varianceThreshold &&
                new types.BorshDecimal({ ...fields.varianceThreshold })) ||
                null;
        this.basePriorityFee = fields.basePriorityFee;
        this.priorityFeeBump = fields.priorityFeeBump;
        this.priorityFeeBumpPeriod = fields.priorityFeeBumpPeriod;
        this.maxPriorityFeeMultiplier = fields.maxPriorityFeeMultiplier;
    }
    static layout(property) {
        return borsh.struct([
            borsh.option(borsh.array(borsh.u8(), 32), "name"),
            borsh.option(borsh.array(borsh.u8(), 128), "metadata"),
            borsh.option(borsh.u32(), "minUpdateDelaySeconds"),
            borsh.option(borsh.u32(), "minJobResults"),
            borsh.option(borsh.u32(), "batchSize"),
            borsh.option(borsh.u32(), "minOracleResults"),
            borsh.option(borsh.u32(), "forceReportPeriod"),
            borsh.option(types.BorshDecimal.layout(), "varianceThreshold"),
            borsh.option(borsh.u32(), "basePriorityFee"),
            borsh.option(borsh.u32(), "priorityFeeBump"),
            borsh.option(borsh.u32(), "priorityFeeBumpPeriod"),
            borsh.option(borsh.u32(), "maxPriorityFeeMultiplier"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new AggregatorSetConfigParams({
            name: obj.name,
            metadata: obj.metadata,
            minUpdateDelaySeconds: obj.minUpdateDelaySeconds,
            minJobResults: obj.minJobResults,
            batchSize: obj.batchSize,
            minOracleResults: obj.minOracleResults,
            forceReportPeriod: obj.forceReportPeriod,
            varianceThreshold: (obj.varianceThreshold &&
                types.BorshDecimal.fromDecoded(obj.varianceThreshold)) ||
                null,
            basePriorityFee: obj.basePriorityFee,
            priorityFeeBump: obj.priorityFeeBump,
            priorityFeeBumpPeriod: obj.priorityFeeBumpPeriod,
            maxPriorityFeeMultiplier: obj.maxPriorityFeeMultiplier,
        });
    }
    static toEncodable(fields) {
        return {
            name: fields.name,
            metadata: fields.metadata,
            minUpdateDelaySeconds: fields.minUpdateDelaySeconds,
            minJobResults: fields.minJobResults,
            batchSize: fields.batchSize,
            minOracleResults: fields.minOracleResults,
            forceReportPeriod: fields.forceReportPeriod,
            varianceThreshold: (fields.varianceThreshold &&
                types.BorshDecimal.toEncodable(fields.varianceThreshold)) ||
                null,
            basePriorityFee: fields.basePriorityFee,
            priorityFeeBump: fields.priorityFeeBump,
            priorityFeeBumpPeriod: fields.priorityFeeBumpPeriod,
            maxPriorityFeeMultiplier: fields.maxPriorityFeeMultiplier,
        };
    }
    toJSON() {
        return {
            name: this.name,
            metadata: this.metadata,
            minUpdateDelaySeconds: this.minUpdateDelaySeconds,
            minJobResults: this.minJobResults,
            batchSize: this.batchSize,
            minOracleResults: this.minOracleResults,
            forceReportPeriod: this.forceReportPeriod,
            varianceThreshold: (this.varianceThreshold && this.varianceThreshold.toJSON()) || null,
            basePriorityFee: this.basePriorityFee,
            priorityFeeBump: this.priorityFeeBump,
            priorityFeeBumpPeriod: this.priorityFeeBumpPeriod,
            maxPriorityFeeMultiplier: this.maxPriorityFeeMultiplier,
        };
    }
    static fromJSON(obj) {
        return new AggregatorSetConfigParams({
            name: obj.name,
            metadata: obj.metadata,
            minUpdateDelaySeconds: obj.minUpdateDelaySeconds,
            minJobResults: obj.minJobResults,
            batchSize: obj.batchSize,
            minOracleResults: obj.minOracleResults,
            forceReportPeriod: obj.forceReportPeriod,
            varianceThreshold: (obj.varianceThreshold &&
                types.BorshDecimal.fromJSON(obj.varianceThreshold)) ||
                null,
            basePriorityFee: obj.basePriorityFee,
            priorityFeeBump: obj.priorityFeeBump,
            priorityFeeBumpPeriod: obj.priorityFeeBumpPeriod,
            maxPriorityFeeMultiplier: obj.maxPriorityFeeMultiplier,
        });
    }
    toEncodable() {
        return AggregatorSetConfigParams.toEncodable(this);
    }
}
exports.AggregatorSetConfigParams = AggregatorSetConfigParams;
//# sourceMappingURL=AggregatorSetConfigParams.js.map