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
exports.OraclePriceInfo = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class OraclePriceInfo {
    increaseLong;
    increaseShort;
    decreaseLong;
    decreaseShort;
    buyLp;
    sellLp;
    constructor(fields) {
        this.increaseLong = fields.increaseLong;
        this.increaseShort = fields.increaseShort;
        this.decreaseLong = fields.decreaseLong;
        this.decreaseShort = fields.decreaseShort;
        this.buyLp = fields.buyLp;
        this.sellLp = fields.sellLp;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("increaseLong"),
            borsh.u64("increaseShort"),
            borsh.u64("decreaseLong"),
            borsh.u64("decreaseShort"),
            borsh.u64("buyLp"),
            borsh.u64("sellLp"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new OraclePriceInfo({
            increaseLong: obj.increaseLong,
            increaseShort: obj.increaseShort,
            decreaseLong: obj.decreaseLong,
            decreaseShort: obj.decreaseShort,
            buyLp: obj.buyLp,
            sellLp: obj.sellLp,
        });
    }
    static toEncodable(fields) {
        return {
            increaseLong: fields.increaseLong,
            increaseShort: fields.increaseShort,
            decreaseLong: fields.decreaseLong,
            decreaseShort: fields.decreaseShort,
            buyLp: fields.buyLp,
            sellLp: fields.sellLp,
        };
    }
    toJSON() {
        return {
            increaseLong: this.increaseLong.toString(),
            increaseShort: this.increaseShort.toString(),
            decreaseLong: this.decreaseLong.toString(),
            decreaseShort: this.decreaseShort.toString(),
            buyLp: this.buyLp.toString(),
            sellLp: this.sellLp.toString(),
        };
    }
    static fromJSON(obj) {
        return new OraclePriceInfo({
            increaseLong: new bn_js_1.default(obj.increaseLong),
            increaseShort: new bn_js_1.default(obj.increaseShort),
            decreaseLong: new bn_js_1.default(obj.decreaseLong),
            decreaseShort: new bn_js_1.default(obj.decreaseShort),
            buyLp: new bn_js_1.default(obj.buyLp),
            sellLp: new bn_js_1.default(obj.sellLp),
        });
    }
    toEncodable() {
        return OraclePriceInfo.toEncodable(this);
    }
}
exports.OraclePriceInfo = OraclePriceInfo;
//# sourceMappingURL=OraclePriceInfo.js.map