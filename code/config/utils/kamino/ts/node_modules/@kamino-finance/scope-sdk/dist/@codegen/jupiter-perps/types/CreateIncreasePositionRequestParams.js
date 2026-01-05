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
exports.CreateIncreasePositionRequestParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class CreateIncreasePositionRequestParams {
    sizeUsdDelta;
    collateralTokenDelta;
    side;
    requestType;
    priceSlippage;
    jupiterMinimumOut;
    triggerPrice;
    triggerAboveThreshold;
    counter;
    constructor(fields) {
        this.sizeUsdDelta = fields.sizeUsdDelta;
        this.collateralTokenDelta = fields.collateralTokenDelta;
        this.side = fields.side;
        this.requestType = fields.requestType;
        this.priceSlippage = fields.priceSlippage;
        this.jupiterMinimumOut = fields.jupiterMinimumOut;
        this.triggerPrice = fields.triggerPrice;
        this.triggerAboveThreshold = fields.triggerAboveThreshold;
        this.counter = fields.counter;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("sizeUsdDelta"),
            borsh.u64("collateralTokenDelta"),
            types.Side.layout("side"),
            types.RequestType.layout("requestType"),
            borsh.option(borsh.u64(), "priceSlippage"),
            borsh.option(borsh.u64(), "jupiterMinimumOut"),
            borsh.option(borsh.u64(), "triggerPrice"),
            borsh.option(borsh.bool(), "triggerAboveThreshold"),
            borsh.u64("counter"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new CreateIncreasePositionRequestParams({
            sizeUsdDelta: obj.sizeUsdDelta,
            collateralTokenDelta: obj.collateralTokenDelta,
            side: types.Side.fromDecoded(obj.side),
            requestType: types.RequestType.fromDecoded(obj.requestType),
            priceSlippage: obj.priceSlippage,
            jupiterMinimumOut: obj.jupiterMinimumOut,
            triggerPrice: obj.triggerPrice,
            triggerAboveThreshold: obj.triggerAboveThreshold,
            counter: obj.counter,
        });
    }
    static toEncodable(fields) {
        return {
            sizeUsdDelta: fields.sizeUsdDelta,
            collateralTokenDelta: fields.collateralTokenDelta,
            side: fields.side.toEncodable(),
            requestType: fields.requestType.toEncodable(),
            priceSlippage: fields.priceSlippage,
            jupiterMinimumOut: fields.jupiterMinimumOut,
            triggerPrice: fields.triggerPrice,
            triggerAboveThreshold: fields.triggerAboveThreshold,
            counter: fields.counter,
        };
    }
    toJSON() {
        return {
            sizeUsdDelta: this.sizeUsdDelta.toString(),
            collateralTokenDelta: this.collateralTokenDelta.toString(),
            side: this.side.toJSON(),
            requestType: this.requestType.toJSON(),
            priceSlippage: (this.priceSlippage && this.priceSlippage.toString()) || null,
            jupiterMinimumOut: (this.jupiterMinimumOut && this.jupiterMinimumOut.toString()) || null,
            triggerPrice: (this.triggerPrice && this.triggerPrice.toString()) || null,
            triggerAboveThreshold: this.triggerAboveThreshold,
            counter: this.counter.toString(),
        };
    }
    static fromJSON(obj) {
        return new CreateIncreasePositionRequestParams({
            sizeUsdDelta: new bn_js_1.default(obj.sizeUsdDelta),
            collateralTokenDelta: new bn_js_1.default(obj.collateralTokenDelta),
            side: types.Side.fromJSON(obj.side),
            requestType: types.RequestType.fromJSON(obj.requestType),
            priceSlippage: (obj.priceSlippage && new bn_js_1.default(obj.priceSlippage)) || null,
            jupiterMinimumOut: (obj.jupiterMinimumOut && new bn_js_1.default(obj.jupiterMinimumOut)) || null,
            triggerPrice: (obj.triggerPrice && new bn_js_1.default(obj.triggerPrice)) || null,
            triggerAboveThreshold: obj.triggerAboveThreshold,
            counter: new bn_js_1.default(obj.counter),
        });
    }
    toEncodable() {
        return CreateIncreasePositionRequestParams.toEncodable(this);
    }
}
exports.CreateIncreasePositionRequestParams = CreateIncreasePositionRequestParams;
//# sourceMappingURL=CreateIncreasePositionRequestParams.js.map