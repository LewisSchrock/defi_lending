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
exports.OracleMetrics = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class OracleMetrics {
    consecutiveSuccess;
    consecutiveError;
    consecutiveDisagreement;
    consecutiveLateResponse;
    consecutiveFailure;
    totalSuccess;
    totalError;
    totalDisagreement;
    totalLateResponse;
    constructor(fields) {
        this.consecutiveSuccess = fields.consecutiveSuccess;
        this.consecutiveError = fields.consecutiveError;
        this.consecutiveDisagreement = fields.consecutiveDisagreement;
        this.consecutiveLateResponse = fields.consecutiveLateResponse;
        this.consecutiveFailure = fields.consecutiveFailure;
        this.totalSuccess = fields.totalSuccess;
        this.totalError = fields.totalError;
        this.totalDisagreement = fields.totalDisagreement;
        this.totalLateResponse = fields.totalLateResponse;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("consecutiveSuccess"),
            borsh.u64("consecutiveError"),
            borsh.u64("consecutiveDisagreement"),
            borsh.u64("consecutiveLateResponse"),
            borsh.u64("consecutiveFailure"),
            borsh.u128("totalSuccess"),
            borsh.u128("totalError"),
            borsh.u128("totalDisagreement"),
            borsh.u128("totalLateResponse"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new OracleMetrics({
            consecutiveSuccess: obj.consecutiveSuccess,
            consecutiveError: obj.consecutiveError,
            consecutiveDisagreement: obj.consecutiveDisagreement,
            consecutiveLateResponse: obj.consecutiveLateResponse,
            consecutiveFailure: obj.consecutiveFailure,
            totalSuccess: obj.totalSuccess,
            totalError: obj.totalError,
            totalDisagreement: obj.totalDisagreement,
            totalLateResponse: obj.totalLateResponse,
        });
    }
    static toEncodable(fields) {
        return {
            consecutiveSuccess: fields.consecutiveSuccess,
            consecutiveError: fields.consecutiveError,
            consecutiveDisagreement: fields.consecutiveDisagreement,
            consecutiveLateResponse: fields.consecutiveLateResponse,
            consecutiveFailure: fields.consecutiveFailure,
            totalSuccess: fields.totalSuccess,
            totalError: fields.totalError,
            totalDisagreement: fields.totalDisagreement,
            totalLateResponse: fields.totalLateResponse,
        };
    }
    toJSON() {
        return {
            consecutiveSuccess: this.consecutiveSuccess.toString(),
            consecutiveError: this.consecutiveError.toString(),
            consecutiveDisagreement: this.consecutiveDisagreement.toString(),
            consecutiveLateResponse: this.consecutiveLateResponse.toString(),
            consecutiveFailure: this.consecutiveFailure.toString(),
            totalSuccess: this.totalSuccess.toString(),
            totalError: this.totalError.toString(),
            totalDisagreement: this.totalDisagreement.toString(),
            totalLateResponse: this.totalLateResponse.toString(),
        };
    }
    static fromJSON(obj) {
        return new OracleMetrics({
            consecutiveSuccess: new bn_js_1.default(obj.consecutiveSuccess),
            consecutiveError: new bn_js_1.default(obj.consecutiveError),
            consecutiveDisagreement: new bn_js_1.default(obj.consecutiveDisagreement),
            consecutiveLateResponse: new bn_js_1.default(obj.consecutiveLateResponse),
            consecutiveFailure: new bn_js_1.default(obj.consecutiveFailure),
            totalSuccess: new bn_js_1.default(obj.totalSuccess),
            totalError: new bn_js_1.default(obj.totalError),
            totalDisagreement: new bn_js_1.default(obj.totalDisagreement),
            totalLateResponse: new bn_js_1.default(obj.totalLateResponse),
        });
    }
    toEncodable() {
        return OracleMetrics.toEncodable(this);
    }
}
exports.OracleMetrics = OracleMetrics;
//# sourceMappingURL=OracleMetrics.js.map