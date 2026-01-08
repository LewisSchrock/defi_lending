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
exports.AddCustodyParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class AddCustodyParams {
    isStable;
    oracle;
    pricing;
    permissions;
    hourlyFundingBps;
    targetRatioBps;
    constructor(fields) {
        this.isStable = fields.isStable;
        this.oracle = new types.OracleParams({ ...fields.oracle });
        this.pricing = new types.PricingParams({ ...fields.pricing });
        this.permissions = new types.Permissions({ ...fields.permissions });
        this.hourlyFundingBps = fields.hourlyFundingBps;
        this.targetRatioBps = fields.targetRatioBps;
    }
    static layout(property) {
        return borsh.struct([
            borsh.bool("isStable"),
            types.OracleParams.layout("oracle"),
            types.PricingParams.layout("pricing"),
            types.Permissions.layout("permissions"),
            borsh.u64("hourlyFundingBps"),
            borsh.u64("targetRatioBps"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new AddCustodyParams({
            isStable: obj.isStable,
            oracle: types.OracleParams.fromDecoded(obj.oracle),
            pricing: types.PricingParams.fromDecoded(obj.pricing),
            permissions: types.Permissions.fromDecoded(obj.permissions),
            hourlyFundingBps: obj.hourlyFundingBps,
            targetRatioBps: obj.targetRatioBps,
        });
    }
    static toEncodable(fields) {
        return {
            isStable: fields.isStable,
            oracle: types.OracleParams.toEncodable(fields.oracle),
            pricing: types.PricingParams.toEncodable(fields.pricing),
            permissions: types.Permissions.toEncodable(fields.permissions),
            hourlyFundingBps: fields.hourlyFundingBps,
            targetRatioBps: fields.targetRatioBps,
        };
    }
    toJSON() {
        return {
            isStable: this.isStable,
            oracle: this.oracle.toJSON(),
            pricing: this.pricing.toJSON(),
            permissions: this.permissions.toJSON(),
            hourlyFundingBps: this.hourlyFundingBps.toString(),
            targetRatioBps: this.targetRatioBps.toString(),
        };
    }
    static fromJSON(obj) {
        return new AddCustodyParams({
            isStable: obj.isStable,
            oracle: types.OracleParams.fromJSON(obj.oracle),
            pricing: types.PricingParams.fromJSON(obj.pricing),
            permissions: types.Permissions.fromJSON(obj.permissions),
            hourlyFundingBps: new bn_js_1.default(obj.hourlyFundingBps),
            targetRatioBps: new bn_js_1.default(obj.targetRatioBps),
        });
    }
    toEncodable() {
        return AddCustodyParams.toEncodable(this);
    }
}
exports.AddCustodyParams = AddCustodyParams;
//# sourceMappingURL=AddCustodyParams.js.map