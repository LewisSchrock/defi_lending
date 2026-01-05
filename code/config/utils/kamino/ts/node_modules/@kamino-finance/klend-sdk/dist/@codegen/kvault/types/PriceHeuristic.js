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
exports.PriceHeuristic = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class PriceHeuristic {
    /** Lower value of acceptable price */
    lower;
    /** Upper value of acceptable price */
    upper;
    /** Number of decimals of the previously defined values */
    exp;
    constructor(fields) {
        this.lower = fields.lower;
        this.upper = fields.upper;
        this.exp = fields.exp;
    }
    static layout(property) {
        return borsh.struct([borsh.u64("lower"), borsh.u64("upper"), borsh.u64("exp")], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new PriceHeuristic({
            lower: obj.lower,
            upper: obj.upper,
            exp: obj.exp,
        });
    }
    static toEncodable(fields) {
        return {
            lower: fields.lower,
            upper: fields.upper,
            exp: fields.exp,
        };
    }
    toJSON() {
        return {
            lower: this.lower.toString(),
            upper: this.upper.toString(),
            exp: this.exp.toString(),
        };
    }
    static fromJSON(obj) {
        return new PriceHeuristic({
            lower: new bn_js_1.default(obj.lower),
            upper: new bn_js_1.default(obj.upper),
            exp: new bn_js_1.default(obj.exp),
        });
    }
    toEncodable() {
        return PriceHeuristic.toEncodable(this);
    }
}
exports.PriceHeuristic = PriceHeuristic;
//# sourceMappingURL=PriceHeuristic.js.map