"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getLatestAggregatorValue = getLatestAggregatorValue;
const bn_js_1 = __importDefault(require("bn.js"));
const decimal_js_1 = __importDefault(require("decimal.js"));
function getLatestAggregatorValue(aggregator, maxStaleness = 0) {
    if ((aggregator.latestConfirmedRound?.numSuccess ?? 0) === 0) {
        return null;
    }
    if (maxStaleness !== 0) {
        const now = new bn_js_1.default(Date.now() / 1000);
        const latestRoundTimestamp = aggregator.latestConfirmedRound.roundOpenTimestamp;
        const staleness = now.sub(latestRoundTimestamp);
        if (staleness.gt(new bn_js_1.default(maxStaleness))) {
            return null;
        }
    }
    const mantissa = new decimal_js_1.default(aggregator.latestConfirmedRound.result.mantissa.toString());
    const scale = aggregator.latestConfirmedRound.result.scale;
    const result = mantissa.div(new decimal_js_1.default(10).pow(scale));
    return new decimal_js_1.default(result.toPrecision(20));
}
//# sourceMappingURL=switchboard.js.map