"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.maxBigInt = maxBigInt;
function maxBigInt(...values) {
    return values.reduce((max, current) => (current > max ? current : max), values[0]);
}
//# sourceMappingURL=bigint.js.map