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
exports.Limit = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class Limit {
    maxAumUsd;
    maxIndividualLpToken;
    maxPositionUsd;
    constructor(fields) {
        this.maxAumUsd = fields.maxAumUsd;
        this.maxIndividualLpToken = fields.maxIndividualLpToken;
        this.maxPositionUsd = fields.maxPositionUsd;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u128("maxAumUsd"),
            borsh.u128("maxIndividualLpToken"),
            borsh.u64("maxPositionUsd"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new Limit({
            maxAumUsd: obj.maxAumUsd,
            maxIndividualLpToken: obj.maxIndividualLpToken,
            maxPositionUsd: obj.maxPositionUsd,
        });
    }
    static toEncodable(fields) {
        return {
            maxAumUsd: fields.maxAumUsd,
            maxIndividualLpToken: fields.maxIndividualLpToken,
            maxPositionUsd: fields.maxPositionUsd,
        };
    }
    toJSON() {
        return {
            maxAumUsd: this.maxAumUsd.toString(),
            maxIndividualLpToken: this.maxIndividualLpToken.toString(),
            maxPositionUsd: this.maxPositionUsd.toString(),
        };
    }
    static fromJSON(obj) {
        return new Limit({
            maxAumUsd: new bn_js_1.default(obj.maxAumUsd),
            maxIndividualLpToken: new bn_js_1.default(obj.maxIndividualLpToken),
            maxPositionUsd: new bn_js_1.default(obj.maxPositionUsd),
        });
    }
    toEncodable() {
        return Limit.toEncodable(this);
    }
}
exports.Limit = Limit;
//# sourceMappingURL=Limit.js.map