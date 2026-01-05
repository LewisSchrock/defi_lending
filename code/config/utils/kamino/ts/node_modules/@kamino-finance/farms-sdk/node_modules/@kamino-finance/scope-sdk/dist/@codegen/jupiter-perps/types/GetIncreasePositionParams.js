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
exports.GetIncreasePositionParams = void 0;
const bn_js_1 = __importDefault(require("bn.js")); // eslint-disable-line @typescript-eslint/no-unused-vars
const types = __importStar(require("../types")); // eslint-disable-line @typescript-eslint/no-unused-vars
const borsh = __importStar(require("@coral-xyz/borsh"));
class GetIncreasePositionParams {
    collateralTokenDelta;
    sizeUsdDelta;
    side;
    constructor(fields) {
        this.collateralTokenDelta = fields.collateralTokenDelta;
        this.sizeUsdDelta = fields.sizeUsdDelta;
        this.side = fields.side;
    }
    static layout(property) {
        return borsh.struct([
            borsh.u64("collateralTokenDelta"),
            borsh.u64("sizeUsdDelta"),
            types.Side.layout("side"),
        ], property);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    static fromDecoded(obj) {
        return new GetIncreasePositionParams({
            collateralTokenDelta: obj.collateralTokenDelta,
            sizeUsdDelta: obj.sizeUsdDelta,
            side: types.Side.fromDecoded(obj.side),
        });
    }
    static toEncodable(fields) {
        return {
            collateralTokenDelta: fields.collateralTokenDelta,
            sizeUsdDelta: fields.sizeUsdDelta,
            side: fields.side.toEncodable(),
        };
    }
    toJSON() {
        return {
            collateralTokenDelta: this.collateralTokenDelta.toString(),
            sizeUsdDelta: this.sizeUsdDelta.toString(),
            side: this.side.toJSON(),
        };
    }
    static fromJSON(obj) {
        return new GetIncreasePositionParams({
            collateralTokenDelta: new bn_js_1.default(obj.collateralTokenDelta),
            sizeUsdDelta: new bn_js_1.default(obj.sizeUsdDelta),
            side: types.Side.fromJSON(obj.side),
        });
    }
    toEncodable() {
        return GetIncreasePositionParams.toEncodable(this);
    }
}
exports.GetIncreasePositionParams = GetIncreasePositionParams;
//# sourceMappingURL=GetIncreasePositionParams.js.map