"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.depositLeverageCalcs = exports.estimateDepositMode = exports.estimateAdjustMode = exports.estimateWithdrawMode = exports.calcBorrowAmount = exports.LeverageOption = void 0;
exports.calculateMultiplyEffects = calculateMultiplyEffects;
exports.calcWithdrawAmounts = calcWithdrawAmounts;
exports.calcAdjustAmounts = calcAdjustAmounts;
exports.withdrawLeverageCalcs = withdrawLeverageCalcs;
exports.adjustDepositLeverageCalcs = adjustDepositLeverageCalcs;
exports.adjustWithdrawLeverageCalcs = adjustWithdrawLeverageCalcs;
const decimal_js_1 = __importDefault(require("decimal.js"));
const classes_1 = require("../classes");
const utils_1 = require("../utils");
const closingPositionDiffTolerance = 0.0001;
var LeverageOption;
(function (LeverageOption) {
    LeverageOption["deposit"] = "Deposit";
    LeverageOption["withdraw"] = "Withdraw";
    LeverageOption["adjust"] = "Adjust";
    LeverageOption["close"] = "Close";
})(LeverageOption || (exports.LeverageOption = LeverageOption = {}));
async function calculateMultiplyEffects(getPriceByTokenMintDecimal, { depositAmount, withdrawAmount, deposited, borrowed, debtTokenMint, selectedTokenMint, collTokenMint, targetLeverage, activeLeverageOption, flashLoanFeeRatio, debtBorrowFactorPct, priceCollToDebt, priceDebtToColl, }, logEstimations = false) {
    // calculate estimations for deposit operation
    const { adjustDepositPosition: depositModeEstimatedDepositAmount, adjustBorrowPosition: depositModeEstimatedBorrowAmount, } = (0, exports.estimateDepositMode)({
        priceCollToDebt,
        priceDebtToColl,
        amount: depositAmount,
        targetLeverage,
        selectedTokenMint,
        collTokenMint: collTokenMint,
        flashLoanFee: flashLoanFeeRatio,
    });
    // calculate estimations for withdraw operation
    const { adjustDepositPosition: withdrawModeEstimatedDepositTokenWithdrawn, adjustBorrowPosition: withdrawModeEstimatedBorrowTokenWithdrawn, } = (0, exports.estimateWithdrawMode)({
        priceCollToDebt: priceCollToDebt,
        collTokenMint,
        selectedTokenMint,
        amount: withdrawAmount,
        deposited: new decimal_js_1.default(deposited),
        borrowed: new decimal_js_1.default(borrowed),
    });
    // calculate estimations for adjust operation
    const { adjustDepositPosition: adjustModeEstimatedDepositAmount, adjustBorrowPosition: adjustModeEstimateBorrowAmount, } = (0, exports.estimateAdjustMode)(priceCollToDebt, {
        targetLeverage,
        debtTokenMint,
        collTokenMint,
        totalDeposited: new decimal_js_1.default(deposited),
        totalBorrowed: new decimal_js_1.default(borrowed),
        flashLoanFee: flashLoanFeeRatio, // TODO: is this the right flash borrow?
    });
    if (logEstimations) {
        console.log('Estimations', (0, classes_1.toJson)({
            activeLeverageOption,
            depositModeEstimatedDepositAmount,
            depositModeEstimatedBorrowAmount,
            withdrawModeEstimatedDepositTokenWithdrawn,
            withdrawModeEstimatedBorrowTokenWithdrawn,
            adjustModeEstimatedDepositAmount,
            adjustModeEstimateBorrowAmount,
        }));
    }
    let [isClosingPosition, totalDeposited, totalBorrowed] = [false, new decimal_js_1.default(0), new decimal_js_1.default(0)];
    switch (activeLeverageOption) {
        case LeverageOption.deposit: {
            // Deposit and Adjust never clos the position
            isClosingPosition = false;
            totalDeposited = deposited.add(depositModeEstimatedDepositAmount);
            totalBorrowed = borrowed.add(depositModeEstimatedBorrowAmount);
            break;
        }
        case LeverageOption.close:
        case LeverageOption.withdraw: {
            isClosingPosition =
                (withdrawModeEstimatedDepositTokenWithdrawn.gte(new decimal_js_1.default(deposited)) ||
                    withdrawModeEstimatedBorrowTokenWithdrawn.gte(new decimal_js_1.default(borrowed)) ||
                    (0, utils_1.fuzzyEqual)(withdrawModeEstimatedDepositTokenWithdrawn, new decimal_js_1.default(deposited), closingPositionDiffTolerance) ||
                    (0, utils_1.fuzzyEqual)(withdrawModeEstimatedBorrowTokenWithdrawn, new decimal_js_1.default(borrowed), closingPositionDiffTolerance)) &&
                    !(0, utils_1.fuzzyEqual)(withdrawModeEstimatedDepositTokenWithdrawn, new decimal_js_1.default(0), closingPositionDiffTolerance);
            totalDeposited = isClosingPosition ? new decimal_js_1.default(0) : deposited.sub(withdrawModeEstimatedDepositTokenWithdrawn);
            totalBorrowed = isClosingPosition ? new decimal_js_1.default(0) : borrowed.sub(withdrawModeEstimatedBorrowTokenWithdrawn);
            break;
        }
        case LeverageOption.adjust: {
            // Deposit and Adjust never clos the position
            isClosingPosition = false;
            totalDeposited = deposited.add(adjustModeEstimatedDepositAmount);
            totalBorrowed = borrowed.add(adjustModeEstimateBorrowAmount);
            break;
        }
    }
    const borrowTokenPrice = await getPriceByTokenMintDecimal(debtTokenMint);
    const depositTokenPrice = await getPriceByTokenMintDecimal(collTokenMint);
    const totalDepositedUsd = depositTokenPrice.mul(totalDeposited);
    const totalBorrowedUsd = borrowTokenPrice.mul(totalBorrowed);
    const netValueUsd = totalDepositedUsd.minus(totalBorrowedUsd);
    // TODO marius this is bad, do not convert to sol as we don't only do leveraged loops only
    const netValueSol = netValueUsd.div(borrowTokenPrice);
    const ltv = totalBorrowedUsd.mul(debtBorrowFactorPct.div(100)).div(totalDepositedUsd);
    return {
        earned: new decimal_js_1.default(0),
        totalDeposited,
        totalBorrowed,
        netValue: netValueSol,
        netValueUsd: netValueUsd,
        ltv,
    };
}
/**
 * returns how much borrowToken will be borrowed to reach leverage given initial collateral amount
 * @param depositTokenAmount
 * @param leverage
 * @param priceAToB
 * @param flashBorrowFee
 */
const calcBorrowAmount = ({ depositTokenAmount, targetLeverage, priceCollToDebt, flashLoanFeeRatio, }) => {
    const initialCollAmountInCollToken = depositTokenAmount;
    const finalCollAmountInCollToken = initialCollAmountInCollToken.mul(targetLeverage);
    const finalDebtAmountInCollToken = finalCollAmountInCollToken.sub(initialCollAmountInCollToken);
    const finalDebtAmountInDebtToken = finalDebtAmountInCollToken.mul(priceCollToDebt);
    const flashFeeFactor = new decimal_js_1.default(1).add(flashLoanFeeRatio);
    const debtTokenToBorrow = finalDebtAmountInDebtToken.mul(flashFeeFactor);
    return debtTokenToBorrow;
};
exports.calcBorrowAmount = calcBorrowAmount;
const estimateWithdrawMode = (props) => {
    const { amount, collTokenMint, selectedTokenMint, deposited, borrowed, priceCollToDebt } = props;
    return calcWithdrawAmounts({
        selectedTokenMint,
        collTokenMint,
        withdrawAmount: new decimal_js_1.default(amount),
        priceCollToDebt,
        currentBorrowPosition: borrowed,
        currentDepositPosition: deposited,
    });
};
exports.estimateWithdrawMode = estimateWithdrawMode;
function calcWithdrawAmounts(params) {
    const { currentBorrowPosition, currentDepositPosition, priceCollToDebt, withdrawAmount, selectedTokenMint, collTokenMint, } = params;
    // MSOL/SOL
    const currentDepositInCollateralToken = currentDepositPosition;
    const currentDebtInCollateralToken = currentBorrowPosition.div(priceCollToDebt);
    const currentNetPositionInCollateralToken = currentDepositInCollateralToken.minus(currentDebtInCollateralToken);
    const targetLeverage = currentDepositInCollateralToken.div(currentNetPositionInCollateralToken);
    const initialDepositInCollateralToken = currentDepositPosition.minus(currentBorrowPosition.div(priceCollToDebt));
    const amountToWithdrawDepositToken = selectedTokenMint === collTokenMint ? withdrawAmount : withdrawAmount.div(priceCollToDebt);
    const targetDeposit = initialDepositInCollateralToken.minus(amountToWithdrawDepositToken).mul(targetLeverage);
    const targetBorrow = (0, exports.calcBorrowAmount)({
        depositTokenAmount: initialDepositInCollateralToken.minus(amountToWithdrawDepositToken),
        priceCollToDebt: new decimal_js_1.default(priceCollToDebt),
        targetLeverage: new decimal_js_1.default(targetLeverage),
        flashLoanFeeRatio: new decimal_js_1.default(0),
    });
    const adjustDepositPosition = currentDepositPosition.minus(targetDeposit);
    const adjustBorrowPosition = currentBorrowPosition.minus(targetBorrow);
    // TODO: add flashLoan fee here in final values
    return {
        adjustDepositPosition,
        adjustBorrowPosition,
    };
}
/**
 * Calculate how much token will be deposited or withdrawn in case of position adjustment
 * @param leverage
 * @param totalDeposited
 * @param totalBorrowed
 */
const estimateAdjustMode = (priceCollToDebt, { targetLeverage, totalDeposited, totalBorrowed, flashLoanFee }) => {
    return calcAdjustAmounts({
        currentBorrowPosition: totalBorrowed,
        currentDepositPosition: totalDeposited,
        priceCollToDebt,
        targetLeverage,
        flashLoanFee,
    });
};
exports.estimateAdjustMode = estimateAdjustMode;
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
function calcAdjustAmounts({ targetLeverage, currentBorrowPosition, currentDepositPosition, priceCollToDebt, flashLoanFee, }) {
    const initialDeposit = currentDepositPosition.minus(currentBorrowPosition.div(priceCollToDebt));
    const targetDeposit = initialDeposit.mul(targetLeverage);
    const targetBorrow = (0, exports.calcBorrowAmount)({
        depositTokenAmount: initialDeposit,
        priceCollToDebt: new decimal_js_1.default(priceCollToDebt),
        targetLeverage: new decimal_js_1.default(targetLeverage),
        flashLoanFeeRatio: flashLoanFee,
    });
    const adjustDepositPosition = targetDeposit.minus(currentDepositPosition);
    const adjustBorrowPosition = targetBorrow.minus(currentBorrowPosition);
    return {
        adjustDepositPosition,
        adjustBorrowPosition,
    };
}
// Given a deposit amount of Deposit|Borrow token
// and a target leverage, calculate final { collateral, debt } value
const estimateDepositMode = ({ priceCollToDebt, priceDebtToColl, amount, targetLeverage, selectedTokenMint, collTokenMint, flashLoanFee, slippagePct = new decimal_js_1.default(0), }) => {
    const isDepositingCollToken = selectedTokenMint === collTokenMint;
    const finalCollTokenAmount = isDepositingCollToken
        ? new decimal_js_1.default(amount).mul(targetLeverage).toNumber()
        : new decimal_js_1.default(amount).mul(priceDebtToColl).mul(targetLeverage).toNumber();
    const depositCollTokenAmount = isDepositingCollToken ? amount : amount.mul(priceDebtToColl);
    const borrowAmount = (0, exports.calcBorrowAmount)({
        depositTokenAmount: depositCollTokenAmount,
        targetLeverage: new decimal_js_1.default(targetLeverage),
        priceCollToDebt: new decimal_js_1.default(priceCollToDebt),
        flashLoanFeeRatio: new decimal_js_1.default(flashLoanFee),
    });
    const slippageFactor = new decimal_js_1.default(1).add(slippagePct.div(new decimal_js_1.default(100)));
    const borrowAmountWithSlippage = borrowAmount.mul(slippageFactor);
    return {
        adjustDepositPosition: finalCollTokenAmount,
        adjustBorrowPosition: borrowAmountWithSlippage.toNumber(),
    };
};
exports.estimateDepositMode = estimateDepositMode;
const depositLeverageCalcs = (props) => {
    // Initialize local variables from the props object
    const { depositAmount, depositTokenIsCollToken, depositTokenIsSol, priceDebtToColl, targetLeverage, slippagePct, flashLoanFee, } = props;
    const slippage = slippagePct.div('100');
    const initDepositInSol = depositTokenIsSol ? depositAmount : new decimal_js_1.default(0);
    // Core logic
    if (depositTokenIsCollToken) {
        const y = targetLeverage.mul(priceDebtToColl);
        const x = flashLoanFee.add('1').mul(slippage.add('1')).div(priceDebtToColl);
        const finalColl = depositAmount.mul(x).div(x.sub(targetLeverage.sub('1').div(y)));
        const debt = finalColl.sub(depositAmount).mul(x);
        const flashBorrowColl = finalColl.sub(depositAmount).mul(flashLoanFee.add('1'));
        return {
            flashBorrowInCollToken: flashBorrowColl,
            initDepositInSol,
            debtTokenToBorrow: debt,
            collTokenToDeposit: finalColl,
            swapDebtTokenIn: debt,
            swapCollTokenExpectedOut: finalColl.sub(depositAmount),
        };
    }
    else {
        const y = targetLeverage.mul(priceDebtToColl);
        const x = flashLoanFee.add('1').mul(slippage.add('1')).div(priceDebtToColl);
        const finalColl = depositAmount.div(x.sub(targetLeverage.sub('1').div(y)));
        const flashBorrowColl = finalColl.mul(flashLoanFee.add('1'));
        const debt = targetLeverage.sub('1').mul(finalColl).div(y);
        return {
            flashBorrowInCollToken: flashBorrowColl,
            initDepositInSol,
            debtTokenToBorrow: debt,
            collTokenToDeposit: finalColl,
            swapDebtTokenIn: debt.add(depositAmount),
            swapCollTokenExpectedOut: finalColl,
        };
    }
};
exports.depositLeverageCalcs = depositLeverageCalcs;
function withdrawLeverageCalcs(market, collReserve, debtReserve, priceCollToDebt, withdrawAmount, deposited, borrowed, currentSlot, isClosingPosition, selectedTokenIsCollToken, selectedTokenMint, obligation, flashLoanFee, slippagePct) {
    // 1. Calculate coll_amount and debt_amount to repay such that we maintain leverage and we withdraw to
    // the wallet `amountInDepositTokenToWithdrawToWallet` amount of collateral token
    // We need to withdraw withdrawAmountInDepositToken coll tokens
    // and repay repayAmountInBorrowToken debt tokens
    const { adjustDepositPosition: withdrawAmountCalculated, adjustBorrowPosition: initialRepayAmount } = isClosingPosition
        ? { adjustDepositPosition: deposited, adjustBorrowPosition: borrowed }
        : calcWithdrawAmounts({
            collTokenMint: collReserve.getLiquidityMint(),
            priceCollToDebt: new decimal_js_1.default(priceCollToDebt),
            currentDepositPosition: deposited,
            currentBorrowPosition: borrowed,
            withdrawAmount: new decimal_js_1.default(withdrawAmount),
            selectedTokenMint: selectedTokenMint,
        });
    // Add slippage for the accrued interest rate amount
    const irSlippageBpsForDebt = obligation
        .estimateObligationInterestRate(market, debtReserve, obligation?.state.borrows[0], currentSlot)
        .toDecimalPlaces(debtReserve?.getMintDecimals(), decimal_js_1.default.ROUND_CEIL);
    // add 0.1 to irSlippageBpsForDebt because we don't want to estimate slightly less than SC and end up not repaying enough
    const repayAmount = initialRepayAmount
        .mul(irSlippageBpsForDebt.add('0.1').div('10_000').add('1'))
        .toDecimalPlaces(debtReserve?.getMintDecimals(), decimal_js_1.default.ROUND_CEIL);
    // 6. Get swap ixs
    // 5. Get swap estimations to understand how much we need to borrow from borrow reserve
    // prevent withdrawing more then deposited if we close position
    const depositTokenWithdrawAmount = !isClosingPosition
        ? withdrawAmountCalculated.mul(new decimal_js_1.default(1).plus(flashLoanFee))
        : withdrawAmountCalculated;
    // We are swapping debt token
    // When withdrawing coll, it means we just need to swap enough to pay for the flash borrow
    const swapAmountIfWithdrawingColl = repayAmount
        .mul(new decimal_js_1.default(1).plus(flashLoanFee))
        .mul(new decimal_js_1.default(1).plus(slippagePct.div(100)))
        .div(priceCollToDebt);
    // When withdrawing debt, it means we need to swap just the collateral we are withdrwaing
    // enough to cover the debt we are repaying, leaving the remaining in the wallet
    const swapAmountIfWithdrawingDebt = withdrawAmountCalculated;
    const collTokenSwapIn = selectedTokenIsCollToken ? swapAmountIfWithdrawingColl : swapAmountIfWithdrawingDebt;
    const debtTokenExpectedSwapOut = collTokenSwapIn.mul(priceCollToDebt).div(new decimal_js_1.default(1).add(slippagePct.div(100)));
    return {
        withdrawAmount: withdrawAmountCalculated,
        repayAmount,
        collTokenSwapIn,
        debtTokenExpectedSwapOut,
        depositTokenWithdrawAmount,
    };
}
function adjustDepositLeverageCalcs(debtReserve, adjustDepositPosition, adjustBorrowPosition, priceDebtToColl, flashLoanFee, slippagePct) {
    const amountToFlashBorrowDebt = adjustDepositPosition
        .div(priceDebtToColl)
        .mul(new decimal_js_1.default(new decimal_js_1.default(1).add(slippagePct.div(100))))
        .toDecimalPlaces(debtReserve.stats.decimals, decimal_js_1.default.ROUND_UP);
    const borrowAmount = adjustDepositPosition
        .mul(new decimal_js_1.default(1).plus(flashLoanFee))
        .mul(new decimal_js_1.default(new decimal_js_1.default(1).add(slippagePct.div(100))))
        .div(priceDebtToColl);
    return {
        adjustDepositPosition,
        adjustBorrowPosition,
        amountToFlashBorrowDebt,
        borrowAmount,
        withdrawAmountWithSlippageAndFlashLoanFee: new decimal_js_1.default(0),
    };
}
function adjustWithdrawLeverageCalcs(adjustDepositPosition, adjustBorrowPosition, flashLoanFee, slippagePct) {
    const withdrawAmountWithSlippageAndFlashLoanFee = decimal_js_1.default.abs(adjustDepositPosition)
        .mul(new decimal_js_1.default(1).plus(flashLoanFee))
        .mul(new decimal_js_1.default(1).add(slippagePct.div(100)));
    return {
        adjustDepositPosition,
        adjustBorrowPosition,
        amountToFlashBorrowDebt: new decimal_js_1.default(0),
        borrowAmount: new decimal_js_1.default(0),
        withdrawAmountWithSlippageAndFlashLoanFee,
    };
}
//# sourceMappingURL=calcs.js.map