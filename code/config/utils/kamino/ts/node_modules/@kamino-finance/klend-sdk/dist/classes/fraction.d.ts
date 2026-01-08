import BN from 'bn.js';
import Decimal from 'decimal.js';
import { BigFractionBytes } from '../lib';
export declare class Fraction {
    static MAX_SIZE_F: number;
    static MAX_SIZE_BF: number;
    static FRACTIONS: number;
    static MULTIPLIER: Decimal;
    static MAX_F_BN: BN;
    static MAX_BF_BN: BN;
    static MIN_BN: BN;
    valueSf: BN;
    constructor(valueSf: BN);
    toDecimal(): Decimal;
    static fromDecimal(n: Decimal | number): Fraction;
    static fromBps(n: Decimal | number): Fraction;
    static fromPercent(n: Decimal | number): Fraction;
    getValue(): BN;
    gt(x: Fraction): boolean;
    lt(x: Fraction): boolean;
    gte(x: Fraction): boolean;
    lte(x: Fraction): boolean;
    eq(x: Fraction): boolean;
}
export declare const ZERO_FRACTION: Fraction;
export declare function bfToDecimal(x: BigFractionBytes): Decimal;
//# sourceMappingURL=fraction.d.ts.map