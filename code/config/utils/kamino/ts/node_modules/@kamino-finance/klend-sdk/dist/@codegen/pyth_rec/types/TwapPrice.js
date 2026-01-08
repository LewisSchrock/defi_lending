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
exports.TwapPrice = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
/**
 * The time weighted average price & conf for a feed over the window [start_time, end_time].
 * This type is used to persist the calculated TWAP in TwapUpdate accounts on Solana.
 */
class TwapPrice {
    feedId;
    startTime;
    endTime;
    price;
    conf;
    exponent;
    /**
     * Ratio out of 1_000_000, where a value of 1_000_000 represents
     * all slots were missed and 0 represents no slots were missed.
     */
    downSlotsRatio;
    constructor(fields) {
        this.feedId = fields.feedId;
        this.startTime = fields.startTime;
        this.endTime = fields.endTime;
        this.price = fields.price;
        this.conf = fields.conf;
        this.exponent = fields.exponent;
        this.downSlotsRatio = fields.downSlotsRatio;
    }
    static layout(property) {
        return borsh.struct([
            borsh.array(borsh.u8(), 32, "feedId"),
            borsh.i64("startTime"),
            borsh.i64("endTime"),
            borsh.i64("price"),
            borsh.u64("conf"),
            borsh.i32("exponent"),
            borsh.u32("downSlotsRatio"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new TwapPrice({
            feedId: obj.feedId,
            startTime: obj.startTime,
            endTime: obj.endTime,
            price: obj.price,
            conf: obj.conf,
            exponent: obj.exponent,
            downSlotsRatio: obj.downSlotsRatio,
        });
    }
    static toEncodable(fields) {
        return {
            feedId: fields.feedId,
            startTime: fields.startTime,
            endTime: fields.endTime,
            price: fields.price,
            conf: fields.conf,
            exponent: fields.exponent,
            downSlotsRatio: fields.downSlotsRatio,
        };
    }
    toJSON() {
        return {
            feedId: this.feedId,
            startTime: this.startTime.toString(),
            endTime: this.endTime.toString(),
            price: this.price.toString(),
            conf: this.conf.toString(),
            exponent: this.exponent,
            downSlotsRatio: this.downSlotsRatio,
        };
    }
    static fromJSON(obj) {
        return new TwapPrice({
            feedId: obj.feedId,
            startTime: new bn_js_1.default(obj.startTime),
            endTime: new bn_js_1.default(obj.endTime),
            price: new bn_js_1.default(obj.price),
            conf: new bn_js_1.default(obj.conf),
            exponent: obj.exponent,
            downSlotsRatio: obj.downSlotsRatio,
        });
    }
    toEncodable() {
        return TwapPrice.toEncodable(this);
    }
}
exports.TwapPrice = TwapPrice;
//# sourceMappingURL=TwapPrice.js.map