"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ZERO_FRACTION = exports.Fraction = void 0;
exports.bfToDecimal = bfToDecimal;
const bn_js_1 = __importDefault(require("bn.js"));
const decimal_js_1 = __importDefault(require("decimal.js"));
const utils_1 = require("./utils");
/**
 * The higher-precision {@link Decimal} counterpart that *must* be used by all operations within {@link Fraction}.
 *
 * ## How to use it?
 * Simply do `new FractionDecimal(x)` instead of `new Decimal(x)`.
 *
 * ## Why is this needed?
 * The default {@link Decimal.precision} is 20.
 * Some fractions on which we operate (most notably: the {@link Fraction.MAX_F_BN}) have more than 20 significant
 * digits, and at the same time they must encode to exact representation (e.g. because the smart contract expects an
 * exact `0xffff...ff` which has a speciyaal meaning, like "withdraw *all*").
 *
 * ## Why was this *not* needed before?
 * Some vibe-coded libraries that we use (e.g. `@orca-so/whirlpool-sdk`) statically initialize the global
 * `Decimal.set({ precision: ... })` when loaded. A previous, fortunate import order allowed our {@link Fraction}'s
 * constants to be computed using a sufficiently-high precision. This of course was broken by a random, unrelated
 * refactor, and from that point on we decided to not rely on the thoughtful Orca developers.
 */
const FractionDecimal = decimal_js_1.default.clone({ precision: 40 });
class Fraction {
    static MAX_SIZE_F = 128;
    static MAX_SIZE_BF = 256;
    static FRACTIONS = 60;
    static MULTIPLIER = new FractionDecimal(2).pow(Fraction.FRACTIONS);
    static MAX_F_BN = new bn_js_1.default(2).pow(new bn_js_1.default(Fraction.MAX_SIZE_F)).sub(new bn_js_1.default(1));
    static MAX_BF_BN = new bn_js_1.default(2).pow(new bn_js_1.default(Fraction.MAX_SIZE_BF)).sub(new bn_js_1.default(1));
    static MIN_BN = new bn_js_1.default(0);
    valueSf;
    constructor(valueSf) {
        if (valueSf.lt(Fraction.MIN_BN) || valueSf.gt(Fraction.MAX_BF_BN)) {
            throw new Error('Number out of range');
        }
        this.valueSf = valueSf;
    }
    toDecimal() {
        return new FractionDecimal(this.valueSf.toString()).div(Fraction.MULTIPLIER);
    }
    static fromDecimal(n) {
        const scaledDecimal = new FractionDecimal(n).mul(Fraction.MULTIPLIER);
        const roundedScaledDecimal = (0, utils_1.roundNearest)(scaledDecimal);
        // Note: the `Decimal.toString()` can return exponential notation (e.g. "1e9") for large numbers. This notation is
        // not accepted by `BN` constructor (i.e. invalid character "e"). Hence, we use `Decimal.toFixed()` (which is
        // different than `number.toFixed()` - it will not do any rounding, just render a normal notation).
        const scaledValue = new bn_js_1.default(roundedScaledDecimal.toFixed());
        return new Fraction(scaledValue);
    }
    static fromBps(n) {
        const decimal = new FractionDecimal(n).div(10000);
        return Fraction.fromDecimal(decimal);
    }
    static fromPercent(n) {
        const decimal = new FractionDecimal(n).div(100);
        return Fraction.fromDecimal(decimal);
    }
    getValue() {
        return this.valueSf;
    }
    gt(x) {
        return this.valueSf.gt(x.getValue());
    }
    lt(x) {
        return this.valueSf.lt(x.getValue());
    }
    gte(x) {
        return this.valueSf.gte(x.getValue());
    }
    lte(x) {
        return this.valueSf.lte(x.getValue());
    }
    eq(x) {
        return this.valueSf.eq(x.getValue());
    }
}
exports.Fraction = Fraction;
exports.ZERO_FRACTION = new Fraction(new bn_js_1.default(0));
function bfToDecimal(x) {
    const bsf = x.value;
    const accSf = bsf.reduce((acc, curr, i) => acc.add(curr.shln(i * 64)), new bn_js_1.default(0));
    return new Fraction(accSf).toDecimal();
}
//# sourceMappingURL=fraction.js.map