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
exports.SetPoolConfigParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class SetPoolConfigParams {
    fees;
    limit;
    maxRequestExecutionSec;
    constructor(fields) {
        this.fees = new types.Fees({ ...fields.fees });
        this.limit = new types.Limit({ ...fields.limit });
        this.maxRequestExecutionSec = fields.maxRequestExecutionSec;
    }
    static layout(property) {
        return borsh.struct([
            types.Fees.layout("fees"),
            types.Limit.layout("limit"),
            borsh.i64("maxRequestExecutionSec"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new SetPoolConfigParams({
            fees: types.Fees.fromDecoded(obj.fees),
            limit: types.Limit.fromDecoded(obj.limit),
            maxRequestExecutionSec: obj.maxRequestExecutionSec,
        });
    }
    static toEncodable(fields) {
        return {
            fees: types.Fees.toEncodable(fields.fees),
            limit: types.Limit.toEncodable(fields.limit),
            maxRequestExecutionSec: fields.maxRequestExecutionSec,
        };
    }
    toJSON() {
        return {
            fees: this.fees.toJSON(),
            limit: this.limit.toJSON(),
            maxRequestExecutionSec: this.maxRequestExecutionSec.toString(),
        };
    }
    static fromJSON(obj) {
        return new SetPoolConfigParams({
            fees: types.Fees.fromJSON(obj.fees),
            limit: types.Limit.fromJSON(obj.limit),
            maxRequestExecutionSec: new bn_js_1.default(obj.maxRequestExecutionSec),
        });
    }
    toEncodable() {
        return SetPoolConfigParams.toEncodable(this);
    }
}
exports.SetPoolConfigParams = SetPoolConfigParams;
//# sourceMappingURL=SetPoolConfigParams.js.map