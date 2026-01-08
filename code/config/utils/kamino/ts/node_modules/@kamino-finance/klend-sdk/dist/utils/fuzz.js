"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.fuzzyEqual = fuzzyEqual;
const decimal_js_1 = __importDefault(require("decimal.js"));
function fuzzyEqual(a, b, epsilon = 0.0001) {
    return new decimal_js_1.default(a).sub(b).abs().lte(epsilon);
}
//# sourceMappingURL=fuzz.js.map