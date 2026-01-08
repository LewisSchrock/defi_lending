import Decimal from 'decimal.js';
import { Account, Address } from '@solana/kit';
import { Token } from '@solana-program/token-2022';
type ObligationFarmScoreType = {
    obligationId: string;
    balance: string;
    debt: string;
    score: string;
    lastSlot: number;
    tokenMint: string;
    side: 'supply' | 'borrow';
};
type RewardRate = {
    beginningSlot: number;
    rewardRate: string;
    name?: string;
};
export declare const calculateNewScore: (rewardStat: {
    lastSlot: number;
    rewardRates: Array<RewardRate>;
    rewardsPerShare: string;
    totalBalance: string;
}, pool: ObligationFarmScoreType, rewardRate: string, endSlot: number, startSlot: number) => Decimal;
export declare const estimateCurrentScore: (rewardStat: {
    lastSlot: number;
    rewardRates: Array<RewardRate>;
    rewardsPerShare: string;
    totalBalance: string;
}, rewardScore: ObligationFarmScoreType, mostRecentSlot: number, mostRecentSlotTime: number) => Decimal;
export declare const interpolate: (x: number, x0: number, x1: number, y0: number, y1: number) => number;
export declare const getBorrowRate: (currentUtilization: number, curve: [number, number][]) => number;
export declare const parseTokenSymbol: (tokenSymbol: number[]) => string;
export declare function parseZeroPaddedUtf8(utf8Array: number[]): string;
export declare function renderZeroPaddedUtf8(str: string, utf8ArrayLength: number): number[];
export declare function sleep(ms: number): Promise<unknown>;
export declare function numberToLamportsDecimal(amount: Decimal.Value, decimals: number): Decimal;
export declare function lamportsToNumberDecimal(amount: Decimal.Value, decimals: number): Decimal;
export declare function lamportsToDecimal(amount: Decimal.Value, decimals: Decimal.Value): Decimal;
export declare const isSolMint: (mint: Address) => boolean;
export declare const valueOrZero: (value: Decimal) => Decimal;
export declare const isEmptyObject: (obj: any) => boolean;
export declare const positiveOrZero: (value: Decimal) => Decimal;
export declare function calculateAPYFromAPR(apr: number): number;
export declare function calculateAPRFromAPY(apy: Decimal.Value): Decimal;
export declare function sameLengthArrayEquals<T>(left: Array<T>, right: Array<T>): boolean;
export declare function getTokenBalanceFromAccountInfoLamports(token: Account<Token>): Decimal;
export declare function bpsToPct(bps: Decimal): Decimal;
/**
 * Truncate ( not round ) number to keep up to max amount of decimals
 * @param num
 * @param maxDecimals
 */
export declare function truncateDecimals(num: Decimal.Value, maxDecimals: number): Decimal;
/**Convert an u8 array to a string */
export declare function decodeVaultName(token: number[]): string;
export declare function pubkeyHashMapToJson(map: Map<Address, any>): {
    [key: string]: string;
};
export declare function toJson(object: any, inline?: boolean): string;
export declare function assertNever(x: never): never;
export declare function orThrow(message: string): never;
export declare function blobEquals(left: Uint8Array, right: Uint8Array): boolean;
/**
 * Returns an integer {@link Decimal} nearest to the given one.
 *
 * NOTE: the `Decimal.round()` should actually be called `.trunc()` (by default, it uses floor rounding). In most cases,
 * we prefer the traditional behavior (as `Math.round()`).
 */
export declare function roundNearest(decimal: Decimal): Decimal;
/**
 * Fetch median slot duration in milliseconds from the last 10 epochs
 */
export declare function getMedianSlotDurationInMsFromLastEpochs(): Promise<number>;
export {};
//# sourceMappingURL=utils.d.ts.map