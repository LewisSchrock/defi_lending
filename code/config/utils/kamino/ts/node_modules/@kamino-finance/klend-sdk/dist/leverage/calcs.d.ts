import { Address, Slot } from '@solana/kit';
import Decimal from 'decimal.js';
import { KaminoMarket, KaminoObligation, KaminoReserve } from '../classes';
import { AdjustLeverageCalcsResult, DepositLeverageCalcsResult, WithdrawLeverageCalcsResult } from './types';
export declare enum LeverageOption {
    deposit = "Deposit",
    withdraw = "Withdraw",
    adjust = "Adjust",
    close = "Close"
}
export interface LeverageCalcsArgs {
    depositAmount: Decimal;
    withdrawAmount: Decimal;
    deposited: Decimal;
    borrowed: Decimal;
    debtTokenMint: Address;
    selectedTokenMint: Address;
    collTokenMint: Address;
    targetLeverage: Decimal;
    activeLeverageOption: LeverageOption;
    flashLoanFeeRatio: Decimal;
    debtBorrowFactorPct: Decimal;
    priceCollToDebt: Decimal;
    priceDebtToColl: Decimal;
}
export interface LeverageCalcsResult {
    earned: Decimal;
    totalDeposited: Decimal;
    totalBorrowed: Decimal;
    netValue: Decimal;
    netValueUsd: Decimal;
    ltv: Decimal;
}
export declare function calculateMultiplyEffects(getPriceByTokenMintDecimal: (mint: Address) => Promise<Decimal>, { depositAmount, withdrawAmount, deposited, borrowed, debtTokenMint, selectedTokenMint, collTokenMint, targetLeverage, activeLeverageOption, flashLoanFeeRatio, debtBorrowFactorPct, priceCollToDebt, priceDebtToColl, }: LeverageCalcsArgs, logEstimations?: boolean): Promise<LeverageCalcsResult>;
/**
 * returns how much borrowToken will be borrowed to reach leverage given initial collateral amount
 * @param depositTokenAmount
 * @param leverage
 * @param priceAToB
 * @param flashBorrowFee
 */
export declare const calcBorrowAmount: ({ depositTokenAmount, targetLeverage, priceCollToDebt, flashLoanFeeRatio, }: {
    depositTokenAmount: Decimal;
    targetLeverage: Decimal;
    priceCollToDebt: Decimal;
    flashLoanFeeRatio: Decimal;
}) => Decimal;
interface UseEstimateWithdrawAmountsProps {
    priceCollToDebt: Decimal;
    amount: Decimal.Value;
    deposited: Decimal;
    borrowed: Decimal;
    collTokenMint: Address;
    selectedTokenMint: Address;
}
export declare const estimateWithdrawMode: (props: UseEstimateWithdrawAmountsProps) => WithdrawResult;
export interface WithdrawParams {
    currentBorrowPosition: Decimal;
    currentDepositPosition: Decimal;
    priceCollToDebt: Decimal;
    withdrawAmount: Decimal;
    selectedTokenMint: Address;
    collTokenMint: Address;
}
interface WithdrawResult {
    adjustDepositPosition: Decimal;
    adjustBorrowPosition: Decimal;
}
export declare function calcWithdrawAmounts(params: WithdrawParams): WithdrawResult;
interface UseEstimateAdjustAmountsProps {
    targetLeverage: Decimal;
    debtTokenMint: Address;
    collTokenMint: Address;
    totalDeposited: Decimal;
    totalBorrowed: Decimal;
    flashLoanFee: Decimal;
}
/**
 * Calculate how much token will be deposited or withdrawn in case of position adjustment
 * @param leverage
 * @param totalDeposited
 * @param totalBorrowed
 */
export declare const estimateAdjustMode: (priceCollToDebt: Decimal, { targetLeverage, totalDeposited, totalBorrowed, flashLoanFee }: UseEstimateAdjustAmountsProps) => AdjustLeverageResult;
export interface AdjustLeverageParams {
    targetLeverage: Decimal;
    currentBorrowPosition: Decimal;
    currentDepositPosition: Decimal;
    priceCollToDebt: Decimal;
    flashLoanFee: Decimal;
}
interface AdjustLeverageResult {
    adjustDepositPosition: Decimal;
    adjustBorrowPosition: Decimal;
}
/**
 * Calculates the amounts of tokenA to deposit/withdraw and tokenB to borrow/repay proportionally to adjust the leverage of a position.
 *
 * @param {AdjustLeverageParams} params - Parameters for the calculation
 * @param {number} params.targetLeverage - The target leverage for the position
 * @param {Decimal} params.currentPositionTokenA - The current amount of tokenA in the position
 * @param {Decimal} params.currentPositionTokenB - The current amount of borrowed tokenB in the position
 * @param {number} params.priceAtoB - The conversion rate from tokenA to tokenB (tokenA price = tokenB price * priceAtoB)
 * @returns {AdjustLeverageResult} An object containing the amounts of tokenA to deposit/withdraw and tokenB to borrow/repay
 */
export declare function calcAdjustAmounts({ targetLeverage, currentBorrowPosition, currentDepositPosition, priceCollToDebt, flashLoanFee, }: AdjustLeverageParams): AdjustLeverageResult;
interface UseTransactionInfoStats {
    priceCollToDebt: Decimal;
    priceDebtToColl: Decimal;
    amount: Decimal;
    targetLeverage: Decimal;
    selectedTokenMint: Address;
    collTokenMint: Address;
    flashLoanFee: Decimal;
    slippagePct?: Decimal;
}
export declare const estimateDepositMode: ({ priceCollToDebt, priceDebtToColl, amount, targetLeverage, selectedTokenMint, collTokenMint, flashLoanFee, slippagePct, }: UseTransactionInfoStats) => {
    adjustDepositPosition: number;
    adjustBorrowPosition: number;
};
export declare const depositLeverageCalcs: (props: {
    depositAmount: Decimal;
    depositTokenIsCollToken: boolean;
    depositTokenIsSol: boolean;
    priceDebtToColl: Decimal;
    targetLeverage: Decimal;
    slippagePct: Decimal;
    flashLoanFee: Decimal;
}) => DepositLeverageCalcsResult;
export declare function withdrawLeverageCalcs(market: KaminoMarket, collReserve: KaminoReserve, debtReserve: KaminoReserve, priceCollToDebt: Decimal, withdrawAmount: Decimal, deposited: Decimal, borrowed: Decimal, currentSlot: Slot, isClosingPosition: boolean, selectedTokenIsCollToken: boolean, selectedTokenMint: Address, obligation: KaminoObligation, flashLoanFee: Decimal, slippagePct: Decimal): WithdrawLeverageCalcsResult;
export declare function adjustDepositLeverageCalcs(debtReserve: KaminoReserve, adjustDepositPosition: Decimal, adjustBorrowPosition: Decimal, priceDebtToColl: Decimal, flashLoanFee: Decimal, slippagePct: Decimal): AdjustLeverageCalcsResult;
export declare function adjustWithdrawLeverageCalcs(adjustDepositPosition: Decimal, adjustBorrowPosition: Decimal, flashLoanFee: Decimal, slippagePct: Decimal): AdjustLeverageCalcsResult;
export {};
//# sourceMappingURL=calcs.d.ts.map