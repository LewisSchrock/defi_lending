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
exports.AggregatorAccountData = void 0;
/* eslint-disable @typescript-eslint/no-unused-vars */
const kit_1 = require("@solana/kit");
/* eslint-enable @typescript-eslint/no-unused-vars */
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh")); // eslint-disable-line @typescript-eslint/no-unused-vars
const utils_1 = require("../utils"); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const programId_1 = require("../programId");
class AggregatorAccountData {
    name;
    metadata;
    reserved1;
    queuePubkey;
    oracleRequestBatchSize;
    minOracleResults;
    minJobResults;
    minUpdateDelaySeconds;
    startAfter;
    varianceThreshold;
    forceReportPeriod;
    expiration;
    consecutiveFailureCount;
    nextAllowedUpdateTime;
    isLocked;
    crankPubkey;
    latestConfirmedRound;
    currentRound;
    jobPubkeysData;
    jobHashes;
    jobPubkeysSize;
    jobsChecksum;
    authority;
    historyBuffer;
    previousConfirmedRoundResult;
    previousConfirmedRoundSlot;
    disableCrank;
    jobWeights;
    creationTimestamp;
    resolutionMode;
    basePriorityFee;
    priorityFeeBump;
    priorityFeeBumpPeriod;
    maxPriorityFeeMultiplier;
    ebuf;
    static discriminator = Buffer.from([
        217, 230, 65, 101, 201, 162, 27, 125,
    ]);
    static layout = borsh.struct([
        borsh.array(borsh.u8(), 32, "name"),
        borsh.array(borsh.u8(), 128, "metadata"),
        borsh.array(borsh.u8(), 32, "reserved1"),
        (0, utils_1.borshAddress)("queuePubkey"),
        borsh.u32("oracleRequestBatchSize"),
        borsh.u32("minOracleResults"),
        borsh.u32("minJobResults"),
        borsh.u32("minUpdateDelaySeconds"),
        borsh.i64("startAfter"),
        types.SwitchboardDecimal.layout("varianceThreshold"),
        borsh.i64("forceReportPeriod"),
        borsh.i64("expiration"),
        borsh.u64("consecutiveFailureCount"),
        borsh.i64("nextAllowedUpdateTime"),
        borsh.bool("isLocked"),
        (0, utils_1.borshAddress)("crankPubkey"),
        types.AggregatorRound.layout("latestConfirmedRound"),
        types.AggregatorRound.layout("currentRound"),
        borsh.array((0, utils_1.borshAddress)(), 16, "jobPubkeysData"),
        borsh.array(types.Hash.layout(), 16, "jobHashes"),
        borsh.u32("jobPubkeysSize"),
        borsh.array(borsh.u8(), 32, "jobsChecksum"),
        (0, utils_1.borshAddress)("authority"),
        (0, utils_1.borshAddress)("historyBuffer"),
        types.SwitchboardDecimal.layout("previousConfirmedRoundResult"),
        borsh.u64("previousConfirmedRoundSlot"),
        borsh.bool("disableCrank"),
        borsh.array(borsh.u8(), 16, "jobWeights"),
        borsh.i64("creationTimestamp"),
        types.AggregatorResolutionMode.layout("resolutionMode"),
        borsh.u32("basePriorityFee"),
        borsh.u32("priorityFeeBump"),
        borsh.u32("priorityFeeBumpPeriod"),
        borsh.u32("maxPriorityFeeMultiplier"),
        borsh.array(borsh.u8(), 122, "ebuf"),
    ]);
    constructor(fields) {
        this.name = fields.name;
        this.metadata = fields.metadata;
        this.reserved1 = fields.reserved1;
        this.queuePubkey = fields.queuePubkey;
        this.oracleRequestBatchSize = fields.oracleRequestBatchSize;
        this.minOracleResults = fields.minOracleResults;
        this.minJobResults = fields.minJobResults;
        this.minUpdateDelaySeconds = fields.minUpdateDelaySeconds;
        this.startAfter = fields.startAfter;
        this.varianceThreshold = new types.SwitchboardDecimal({
            ...fields.varianceThreshold,
        });
        this.forceReportPeriod = fields.forceReportPeriod;
        this.expiration = fields.expiration;
        this.consecutiveFailureCount = fields.consecutiveFailureCount;
        this.nextAllowedUpdateTime = fields.nextAllowedUpdateTime;
        this.isLocked = fields.isLocked;
        this.crankPubkey = fields.crankPubkey;
        this.latestConfirmedRound = new types.AggregatorRound({
            ...fields.latestConfirmedRound,
        });
        this.currentRound = new types.AggregatorRound({ ...fields.currentRound });
        this.jobPubkeysData = fields.jobPubkeysData;
        this.jobHashes = fields.jobHashes.map((item) => new types.Hash({ ...item }));
        this.jobPubkeysSize = fields.jobPubkeysSize;
        this.jobsChecksum = fields.jobsChecksum;
        this.authority = fields.authority;
        this.historyBuffer = fields.historyBuffer;
        this.previousConfirmedRoundResult = new types.SwitchboardDecimal({
            ...fields.previousConfirmedRoundResult,
        });
        this.previousConfirmedRoundSlot = fields.previousConfirmedRoundSlot;
        this.disableCrank = fields.disableCrank;
        this.jobWeights = fields.jobWeights;
        this.creationTimestamp = fields.creationTimestamp;
        this.resolutionMode = fields.resolutionMode;
        this.basePriorityFee = fields.basePriorityFee;
        this.priorityFeeBump = fields.priorityFeeBump;
        this.priorityFeeBumpPeriod = fields.priorityFeeBumpPeriod;
        this.maxPriorityFeeMultiplier = fields.maxPriorityFeeMultiplier;
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
        if (!data.slice(0, 8).equals(AggregatorAccountData.discriminator)) {
            throw new Error("invalid account discriminator");
        }
        const dec = AggregatorAccountData.layout.decode(data.slice(8));
        return new AggregatorAccountData({
            name: dec.name,
            metadata: dec.metadata,
            reserved1: dec.reserved1,
            queuePubkey: dec.queuePubkey,
            oracleRequestBatchSize: dec.oracleRequestBatchSize,
            minOracleResults: dec.minOracleResults,
            minJobResults: dec.minJobResults,
            minUpdateDelaySeconds: dec.minUpdateDelaySeconds,
            startAfter: dec.startAfter,
            varianceThreshold: types.SwitchboardDecimal.fromDecoded(dec.varianceThreshold),
            forceReportPeriod: dec.forceReportPeriod,
            expiration: dec.expiration,
            consecutiveFailureCount: dec.consecutiveFailureCount,
            nextAllowedUpdateTime: dec.nextAllowedUpdateTime,
            isLocked: dec.isLocked,
            crankPubkey: dec.crankPubkey,
            latestConfirmedRound: types.AggregatorRound.fromDecoded(dec.latestConfirmedRound),
            currentRound: types.AggregatorRound.fromDecoded(dec.currentRound),
            jobPubkeysData: dec.jobPubkeysData,
            jobHashes: dec.jobHashes.map((item /* eslint-disable-line @typescript-eslint/no-explicit-any */) => types.Hash.fromDecoded(item)),
            jobPubkeysSize: dec.jobPubkeysSize,
            jobsChecksum: dec.jobsChecksum,
            authority: dec.authority,
            historyBuffer: dec.historyBuffer,
            previousConfirmedRoundResult: types.SwitchboardDecimal.fromDecoded(dec.previousConfirmedRoundResult),
            previousConfirmedRoundSlot: dec.previousConfirmedRoundSlot,
            disableCrank: dec.disableCrank,
            jobWeights: dec.jobWeights,
            creationTimestamp: dec.creationTimestamp,
            resolutionMode: types.AggregatorResolutionMode.fromDecoded(dec.resolutionMode),
            basePriorityFee: dec.basePriorityFee,
            priorityFeeBump: dec.priorityFeeBump,
            priorityFeeBumpPeriod: dec.priorityFeeBumpPeriod,
            maxPriorityFeeMultiplier: dec.maxPriorityFeeMultiplier,
            ebuf: dec.ebuf,
        });
    }
    toJSON() {
        return {
            name: this.name,
            metadata: this.metadata,
            reserved1: this.reserved1,
            queuePubkey: this.queuePubkey,
            oracleRequestBatchSize: this.oracleRequestBatchSize,
            minOracleResults: this.minOracleResults,
            minJobResults: this.minJobResults,
            minUpdateDelaySeconds: this.minUpdateDelaySeconds,
            startAfter: this.startAfter.toString(),
            varianceThreshold: this.varianceThreshold.toJSON(),
            forceReportPeriod: this.forceReportPeriod.toString(),
            expiration: this.expiration.toString(),
            consecutiveFailureCount: this.consecutiveFailureCount.toString(),
            nextAllowedUpdateTime: this.nextAllowedUpdateTime.toString(),
            isLocked: this.isLocked,
            crankPubkey: this.crankPubkey,
            latestConfirmedRound: this.latestConfirmedRound.toJSON(),
            currentRound: this.currentRound.toJSON(),
            jobPubkeysData: this.jobPubkeysData,
            jobHashes: this.jobHashes.map((item) => item.toJSON()),
            jobPubkeysSize: this.jobPubkeysSize,
            jobsChecksum: this.jobsChecksum,
            authority: this.authority,
            historyBuffer: this.historyBuffer,
            previousConfirmedRoundResult: this.previousConfirmedRoundResult.toJSON(),
            previousConfirmedRoundSlot: this.previousConfirmedRoundSlot.toString(),
            disableCrank: this.disableCrank,
            jobWeights: this.jobWeights,
            creationTimestamp: this.creationTimestamp.toString(),
            resolutionMode: this.resolutionMode.toJSON(),
            basePriorityFee: this.basePriorityFee,
            priorityFeeBump: this.priorityFeeBump,
            priorityFeeBumpPeriod: this.priorityFeeBumpPeriod,
            maxPriorityFeeMultiplier: this.maxPriorityFeeMultiplier,
            ebuf: this.ebuf,
        };
    }
    static fromJSON(obj) {
        return new AggregatorAccountData({
            name: obj.name,
            metadata: obj.metadata,
            reserved1: obj.reserved1,
            queuePubkey: (0, kit_1.address)(obj.queuePubkey),
            oracleRequestBatchSize: obj.oracleRequestBatchSize,
            minOracleResults: obj.minOracleResults,
            minJobResults: obj.minJobResults,
            minUpdateDelaySeconds: obj.minUpdateDelaySeconds,
            startAfter: new bn_js_1.default(obj.startAfter),
            varianceThreshold: types.SwitchboardDecimal.fromJSON(obj.varianceThreshold),
            forceReportPeriod: new bn_js_1.default(obj.forceReportPeriod),
            expiration: new bn_js_1.default(obj.expiration),
            consecutiveFailureCount: new bn_js_1.default(obj.consecutiveFailureCount),
            nextAllowedUpdateTime: new bn_js_1.default(obj.nextAllowedUpdateTime),
            isLocked: obj.isLocked,
            crankPubkey: (0, kit_1.address)(obj.crankPubkey),
            latestConfirmedRound: types.AggregatorRound.fromJSON(obj.latestConfirmedRound),
            currentRound: types.AggregatorRound.fromJSON(obj.currentRound),
            jobPubkeysData: obj.jobPubkeysData.map((item) => (0, kit_1.address)(item)),
            jobHashes: obj.jobHashes.map((item) => types.Hash.fromJSON(item)),
            jobPubkeysSize: obj.jobPubkeysSize,
            jobsChecksum: obj.jobsChecksum,
            authority: (0, kit_1.address)(obj.authority),
            historyBuffer: (0, kit_1.address)(obj.historyBuffer),
            previousConfirmedRoundResult: types.SwitchboardDecimal.fromJSON(obj.previousConfirmedRoundResult),
            previousConfirmedRoundSlot: new bn_js_1.default(obj.previousConfirmedRoundSlot),
            disableCrank: obj.disableCrank,
            jobWeights: obj.jobWeights,
            creationTimestamp: new bn_js_1.default(obj.creationTimestamp),
            resolutionMode: types.AggregatorResolutionMode.fromJSON(obj.resolutionMode),
            basePriorityFee: obj.basePriorityFee,
            priorityFeeBump: obj.priorityFeeBump,
            priorityFeeBumpPeriod: obj.priorityFeeBumpPeriod,
            maxPriorityFeeMultiplier: obj.maxPriorityFeeMultiplier,
            ebuf: obj.ebuf,
        });
    }
}
exports.AggregatorAccountData = AggregatorAccountData;
//# sourceMappingURL=AggregatorAccountData.js.map