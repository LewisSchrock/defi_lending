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
exports.CreateDecreasePositionRequestParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class CreateDecreasePositionRequestParams {
    collateralUsdDelta;
    sizeUsdDelta;
    requestType;
    priceSlippage;
    jupiterMinimumOut;
    triggerPrice;
    triggerAboveThreshold;
    entirePosition;
    counter;
    constructor(fields) {
        this.collateralUsdDelta = fields.collateralUsdDelta;
        this.sizeUsdDelta = fields.sizeUsdDelta;
        this.requestType = fields.requestType;
        this.priceSlippage = fields.priceSlippage;
        this.jupiterMinimumOut = fields.jupiterMinimumOut;
        this.triggerPrice = fields.triggerPrice;
        this.triggerAboveThreshold = fields.triggerAboveThreshold;
        this.entirePosition = fields.entirePosition;
        this.counter = fields.counter;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("collateralUsdDelta"),
            borsh.u64("sizeUsdDelta"),
            types.RequestType.layout("requestType"),
            borsh.option(borsh.u64(), "priceSlippage"),
            borsh.option(borsh.u64(), "jupiterMinimumOut"),
            borsh.option(borsh.u64(), "triggerPrice"),
            borsh.option(borsh.bool(), "triggerAboveThreshold"),
            borsh.option(borsh.bool(), "entirePosition"),
            borsh.u64("counter"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new CreateDecreasePositionRequestParams({
            collateralUsdDelta: obj.collateralUsdDelta,
            sizeUsdDelta: obj.sizeUsdDelta,
            requestType: types.RequestType.fromDecoded(obj.requestType),
            priceSlippage: obj.priceSlippage,
            jupiterMinimumOut: obj.jupiterMinimumOut,
            triggerPrice: obj.triggerPrice,
            triggerAboveThreshold: obj.triggerAboveThreshold,
            entirePosition: obj.entirePosition,
            counter: obj.counter,
        });
    }
    static toEncodable(fields) {
        return {
            collateralUsdDelta: fields.collateralUsdDelta,
            sizeUsdDelta: fields.sizeUsdDelta,
            requestType: fields.requestType.toEncodable(),
            priceSlippage: fields.priceSlippage,
            jupiterMinimumOut: fields.jupiterMinimumOut,
            triggerPrice: fields.triggerPrice,
            triggerAboveThreshold: fields.triggerAboveThreshold,
            entirePosition: fields.entirePosition,
            counter: fields.counter,
        };
    }
    toJSON() {
        return {
            collateralUsdDelta: this.collateralUsdDelta.toString(),
            sizeUsdDelta: this.sizeUsdDelta.toString(),
            requestType: this.requestType.toJSON(),
            priceSlippage: (this.priceSlippage && this.priceSlippage.toString()) || null,
            jupiterMinimumOut: (this.jupiterMinimumOut && this.jupiterMinimumOut.toString()) || null,
            triggerPrice: (this.triggerPrice && this.triggerPrice.toString()) || null,
            triggerAboveThreshold: this.triggerAboveThreshold,
            entirePosition: this.entirePosition,
            counter: this.counter.toString(),
        };
    }
    static fromJSON(obj) {
        return new CreateDecreasePositionRequestParams({
            collateralUsdDelta: new bn_js_1.default(obj.collateralUsdDelta),
            sizeUsdDelta: new bn_js_1.default(obj.sizeUsdDelta),
            requestType: types.RequestType.fromJSON(obj.requestType),
            priceSlippage: (obj.priceSlippage && new bn_js_1.default(obj.priceSlippage)) || null,
            jupiterMinimumOut: (obj.jupiterMinimumOut && new bn_js_1.default(obj.jupiterMinimumOut)) || null,
            triggerPrice: (obj.triggerPrice && new bn_js_1.default(obj.triggerPrice)) || null,
            triggerAboveThreshold: obj.triggerAboveThreshold,
            entirePosition: obj.entirePosition,
            counter: new bn_js_1.default(obj.counter),
        });
    }
    toEncodable() {
        return CreateDecreasePositionRequestParams.toEncodable(this);
    }
}
exports.CreateDecreasePositionRequestParams = CreateDecreasePositionRequestParams;
//# sourceMappingURL=CreateDecreasePositionRequestParams.js.map