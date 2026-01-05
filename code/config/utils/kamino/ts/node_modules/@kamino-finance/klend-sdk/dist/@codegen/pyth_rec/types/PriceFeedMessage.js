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
exports.PriceFeedMessage = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class PriceFeedMessage {
    feedId;
    price;
    conf;
    exponent;
    publishTime;
    prevPublishTime;
    emaPrice;
    emaConf;
    constructor(fields) {
        this.feedId = fields.feedId;
        this.price = fields.price;
        this.conf = fields.conf;
        this.exponent = fields.exponent;
        this.publishTime = fields.publishTime;
        this.prevPublishTime = fields.prevPublishTime;
        this.emaPrice = fields.emaPrice;
        this.emaConf = fields.emaConf;
    }
    static layout(property) {
        return borsh.struct([
            borsh.array(borsh.u8(), 32, "feedId"),
            borsh.i64("price"),
            borsh.u64("conf"),
            borsh.i32("exponent"),
            borsh.i64("publishTime"),
            borsh.i64("prevPublishTime"),
            borsh.i64("emaPrice"),
            borsh.u64("emaConf"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new PriceFeedMessage({
            feedId: obj.feedId,
            price: obj.price,
            conf: obj.conf,
            exponent: obj.exponent,
            publishTime: obj.publishTime,
            prevPublishTime: obj.prevPublishTime,
            emaPrice: obj.emaPrice,
            emaConf: obj.emaConf,
        });
    }
    static toEncodable(fields) {
        return {
            feedId: fields.feedId,
            price: fields.price,
            conf: fields.conf,
            exponent: fields.exponent,
            publishTime: fields.publishTime,
            prevPublishTime: fields.prevPublishTime,
            emaPrice: fields.emaPrice,
            emaConf: fields.emaConf,
        };
    }
    toJSON() {
        return {
            feedId: this.feedId,
            price: this.price.toString(),
            conf: this.conf.toString(),
            exponent: this.exponent,
            publishTime: this.publishTime.toString(),
            prevPublishTime: this.prevPublishTime.toString(),
            emaPrice: this.emaPrice.toString(),
            emaConf: this.emaConf.toString(),
        };
    }
    static fromJSON(obj) {
        return new PriceFeedMessage({
            feedId: obj.feedId,
            price: new bn_js_1.default(obj.price),
            conf: new bn_js_1.default(obj.conf),
            exponent: obj.exponent,
            publishTime: new bn_js_1.default(obj.publishTime),
            prevPublishTime: new bn_js_1.default(obj.prevPublishTime),
            emaPrice: new bn_js_1.default(obj.emaPrice),
            emaConf: new bn_js_1.default(obj.emaConf),
        });
    }
    toEncodable() {
        return PriceFeedMessage.toEncodable(this);
    }
}
exports.PriceFeedMessage = PriceFeedMessage;
//# sourceMappingURL=PriceFeedMessage.js.map