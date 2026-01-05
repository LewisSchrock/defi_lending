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
exports.TokenInfo = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class TokenInfo {
    /** UTF-8 encoded name of the token (null-terminated) */
    name;
    /** Heuristics limits of acceptable price */
    heuristic;
    /** Max divergence between twap and price in bps */
    maxTwapDivergenceBps;
    maxAgePriceSeconds;
    maxAgeTwapSeconds;
    /** Scope price configuration */
    scopeConfiguration;
    /** Switchboard configuration */
    switchboardConfiguration;
    /** Pyth configuration */
    pythConfiguration;
    blockPriceUsage;
    reserved;
    padding;
    constructor(fields) {
        this.name = fields.name;
        this.heuristic = new types.PriceHeuristic({ ...fields.heuristic });
        this.maxTwapDivergenceBps = fields.maxTwapDivergenceBps;
        this.maxAgePriceSeconds = fields.maxAgePriceSeconds;
        this.maxAgeTwapSeconds = fields.maxAgeTwapSeconds;
        this.scopeConfiguration = new types.ScopeConfiguration({
            ...fields.scopeConfiguration,
        });
        this.switchboardConfiguration = new types.SwitchboardConfiguration({
            ...fields.switchboardConfiguration,
        });
        this.pythConfiguration = new types.PythConfiguration({
            ...fields.pythConfiguration,
        });
        this.blockPriceUsage = fields.blockPriceUsage;
        this.reserved = fields.reserved;
        this.padding = fields.padding;
    }
    static layout(property) {
        return borsh.struct([
            borsh.array(borsh.u8(), 32, "name"),
            types.PriceHeuristic.layout("heuristic"),
            borsh.u64("maxTwapDivergenceBps"),
            borsh.u64("maxAgePriceSeconds"),
            borsh.u64("maxAgeTwapSeconds"),
            types.ScopeConfiguration.layout("scopeConfiguration"),
            types.SwitchboardConfiguration.layout("switchboardConfiguration"),
            types.PythConfiguration.layout("pythConfiguration"),
            borsh.u8("blockPriceUsage"),
            borsh.array(borsh.u8(), 7, "reserved"),
            borsh.array(borsh.u64(), 19, "padding"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new TokenInfo({
            name: obj.name,
            heuristic: types.PriceHeuristic.fromDecoded(obj.heuristic),
            maxTwapDivergenceBps: obj.maxTwapDivergenceBps,
            maxAgePriceSeconds: obj.maxAgePriceSeconds,
            maxAgeTwapSeconds: obj.maxAgeTwapSeconds,
            scopeConfiguration: types.ScopeConfiguration.fromDecoded(obj.scopeConfiguration),
            switchboardConfiguration: types.SwitchboardConfiguration.fromDecoded(obj.switchboardConfiguration),
            pythConfiguration: types.PythConfiguration.fromDecoded(obj.pythConfiguration),
            blockPriceUsage: obj.blockPriceUsage,
            reserved: obj.reserved,
            padding: obj.padding,
        });
    }
    static toEncodable(fields) {
        return {
            name: fields.name,
            heuristic: types.PriceHeuristic.toEncodable(fields.heuristic),
            maxTwapDivergenceBps: fields.maxTwapDivergenceBps,
            maxAgePriceSeconds: fields.maxAgePriceSeconds,
            maxAgeTwapSeconds: fields.maxAgeTwapSeconds,
            scopeConfiguration: types.ScopeConfiguration.toEncodable(fields.scopeConfiguration),
            switchboardConfiguration: types.SwitchboardConfiguration.toEncodable(fields.switchboardConfiguration),
            pythConfiguration: types.PythConfiguration.toEncodable(fields.pythConfiguration),
            blockPriceUsage: fields.blockPriceUsage,
            reserved: fields.reserved,
            padding: fields.padding,
        };
    }
    toJSON() {
        return {
            name: this.name,
            heuristic: this.heuristic.toJSON(),
            maxTwapDivergenceBps: this.maxTwapDivergenceBps.toString(),
            maxAgePriceSeconds: this.maxAgePriceSeconds.toString(),
            maxAgeTwapSeconds: this.maxAgeTwapSeconds.toString(),
            scopeConfiguration: this.scopeConfiguration.toJSON(),
            switchboardConfiguration: this.switchboardConfiguration.toJSON(),
            pythConfiguration: this.pythConfiguration.toJSON(),
            blockPriceUsage: this.blockPriceUsage,
            reserved: this.reserved,
            padding: this.padding.map((item) => item.toString()),
        };
    }
    static fromJSON(obj) {
        return new TokenInfo({
            name: obj.name,
            heuristic: types.PriceHeuristic.fromJSON(obj.heuristic),
            maxTwapDivergenceBps: new bn_js_1.default(obj.maxTwapDivergenceBps),
            maxAgePriceSeconds: new bn_js_1.default(obj.maxAgePriceSeconds),
            maxAgeTwapSeconds: new bn_js_1.default(obj.maxAgeTwapSeconds),
            scopeConfiguration: types.ScopeConfiguration.fromJSON(obj.scopeConfiguration),
            switchboardConfiguration: types.SwitchboardConfiguration.fromJSON(obj.switchboardConfiguration),
            pythConfiguration: types.PythConfiguration.fromJSON(obj.pythConfiguration),
            blockPriceUsage: obj.blockPriceUsage,
            reserved: obj.reserved,
            padding: obj.padding.map((item) => new bn_js_1.default(item)),
        });
    }
    toEncodable() {
        return TokenInfo.toEncodable(this);
    }
}
exports.TokenInfo = TokenInfo;
//# sourceMappingURL=TokenInfo.js.map