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
exports.CurvePoint = void 0;
const borsh = __importStar(require("@coral-xyz/borsh"));
class CurvePoint {
    utilizationRateBps;
    borrowRateBps;
    constructor(fields) {
        this.utilizationRateBps = fields.utilizationRateBps;
        this.borrowRateBps = fields.borrowRateBps;
    }
    static layout(property) {
        return borsh.struct([borsh.u32("utilizationRateBps"), borsh.u32("borrowRateBps")], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new CurvePoint({
            utilizationRateBps: obj.utilizationRateBps,
            borrowRateBps: obj.borrowRateBps,
        });
    }
    static toEncodable(fields) {
        return {
            utilizationRateBps: fields.utilizationRateBps,
            borrowRateBps: fields.borrowRateBps,
        };
    }
    toJSON() {
        return {
            utilizationRateBps: this.utilizationRateBps,
            borrowRateBps: this.borrowRateBps,
        };
    }
    static fromJSON(obj) {
        return new CurvePoint({
            utilizationRateBps: obj.utilizationRateBps,
            borrowRateBps: obj.borrowRateBps,
        });
    }
    toEncodable() {
        return CurvePoint.toEncodable(this);
    }
}
exports.CurvePoint = CurvePoint;
//# sourceMappingURL=CurvePoint.js.map