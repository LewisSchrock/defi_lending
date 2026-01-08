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
exports.AggregatorSaveResultParams = void 0;
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class AggregatorSaveResultParams {
    oracleIdx;
    error;
    value;
    jobsChecksum;
    minResponse;
    maxResponse;
    feedPermissionBump;
    oraclePermissionBump;
    leaseBump;
    stateBump;
    constructor(fields) {
        this.oracleIdx = fields.oracleIdx;
        this.error = fields.error;
        this.value = new types.BorshDecimal({ ...fields.value });
        this.jobsChecksum = fields.jobsChecksum;
        this.minResponse = new types.BorshDecimal({ ...fields.minResponse });
        this.maxResponse = new types.BorshDecimal({ ...fields.maxResponse });
        this.feedPermissionBump = fields.feedPermissionBump;
        this.oraclePermissionBump = fields.oraclePermissionBump;
        this.leaseBump = fields.leaseBump;
        this.stateBump = fields.stateBump;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u32("oracleIdx"),
            borsh.bool("error"),
            types.BorshDecimal.layout("value"),
            borsh.array(borsh.u8(), 32, "jobsChecksum"),
            types.BorshDecimal.layout("minResponse"),
            types.BorshDecimal.layout("maxResponse"),
            borsh.u8("feedPermissionBump"),
            borsh.u8("oraclePermissionBump"),
            borsh.u8("leaseBump"),
            borsh.u8("stateBump"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new AggregatorSaveResultParams({
            oracleIdx: obj.oracleIdx,
            error: obj.error,
            value: types.BorshDecimal.fromDecoded(obj.value),
            jobsChecksum: obj.jobsChecksum,
            minResponse: types.BorshDecimal.fromDecoded(obj.minResponse),
            maxResponse: types.BorshDecimal.fromDecoded(obj.maxResponse),
            feedPermissionBump: obj.feedPermissionBump,
            oraclePermissionBump: obj.oraclePermissionBump,
            leaseBump: obj.leaseBump,
            stateBump: obj.stateBump,
        });
    }
    static toEncodable(fields) {
        return {
            oracleIdx: fields.oracleIdx,
            error: fields.error,
            value: types.BorshDecimal.toEncodable(fields.value),
            jobsChecksum: fields.jobsChecksum,
            minResponse: types.BorshDecimal.toEncodable(fields.minResponse),
            maxResponse: types.BorshDecimal.toEncodable(fields.maxResponse),
            feedPermissionBump: fields.feedPermissionBump,
            oraclePermissionBump: fields.oraclePermissionBump,
            leaseBump: fields.leaseBump,
            stateBump: fields.stateBump,
        };
    }
    toJSON() {
        return {
            oracleIdx: this.oracleIdx,
            error: this.error,
            value: this.value.toJSON(),
            jobsChecksum: this.jobsChecksum,
            minResponse: this.minResponse.toJSON(),
            maxResponse: this.maxResponse.toJSON(),
            feedPermissionBump: this.feedPermissionBump,
            oraclePermissionBump: this.oraclePermissionBump,
            leaseBump: this.leaseBump,
            stateBump: this.stateBump,
        };
    }
    static fromJSON(obj) {
        return new AggregatorSaveResultParams({
            oracleIdx: obj.oracleIdx,
            error: obj.error,
            value: types.BorshDecimal.fromJSON(obj.value),
            jobsChecksum: obj.jobsChecksum,
            minResponse: types.BorshDecimal.fromJSON(obj.minResponse),
            maxResponse: types.BorshDecimal.fromJSON(obj.maxResponse),
            feedPermissionBump: obj.feedPermissionBump,
            oraclePermissionBump: obj.oraclePermissionBump,
            leaseBump: obj.leaseBump,
            stateBump: obj.stateBump,
        });
    }
    toEncodable() {
        return AggregatorSaveResultParams.toEncodable(this);
    }
}
exports.AggregatorSaveResultParams = AggregatorSaveResultParams;
//# sourceMappingURL=AggregatorSaveResultParams.js.map