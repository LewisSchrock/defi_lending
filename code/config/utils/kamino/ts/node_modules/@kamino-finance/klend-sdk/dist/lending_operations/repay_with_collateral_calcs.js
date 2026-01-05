"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.calcFlashRepayAmount = void 0;
exports.calcRepayAmountWithSlippage = calcRepayAmountWithSlippage;
exports.calcMaxWithdrawCollateral = calcMaxWithdrawCollateral;
exports.estimateDebtRepaymentWithColl = estimateDebtRepaymentWithColl;
exports.estimateCollNeededForDebtRepayment = estimateCollNeededForDebtRepayment;
const decimal_js_1 = __importDefault(require("decimal.js"));
const classes_1 = require("../classes");
const kit_1 = require("@solana/kit");
const utils_1 = require("../classes/utils");
const repay_with_collateral_operations_1 = require("./repay_with_collateral_operations");
function calcRepayAmountWithSlippage(kaminoMarket, debtReserve, currentSlot, obligation, amount, referrer) {
    const interestRateAccrued = obligation
        .estimateObligationInterestRate(kaminoMarket, debtReserve, obligation.state.borrows.find((borrow) => borrow.borrowReserve === debtReserve.address), currentSlot)
        .toDecimalPlaces(debtReserve.state.liquidity.mintDecimals.toNumber(), decimal_js_1.default.ROUND_CEIL);
    // add 0.1% to interestRateAccrued because we don't want to estimate slightly less than SC and end up not repaying enough
    const repayAmountIrAdjusted = amount
        .mul(interestRateAccrued.mul(new decimal_js_1.default('1.001')))
        .toDecimalPlaces(debtReserve.state.liquidity.mintDecimals.toNumber(), decimal_js_1.default.ROUND_CEIL);
    let repayAmount;
    // Ensure when repaying close to the full amount, we repay the full amount as otherwise we might end up having a small amount left
    if (repayAmountIrAdjusted.greaterThanOrEqualTo((0, utils_1.lamportsToDecimal)(obligation.getBorrowByReserve(debtReserve.address)?.amount || new decimal_js_1.default(0), debtReserve.stats.decimals))) {
        repayAmount = repayAmountIrAdjusted;
    }
    else {
        repayAmount = amount;
    }
    const repayAmountLamports = (0, classes_1.numberToLamportsDecimal)(repayAmount, debtReserve.stats.decimals);
    const { flashRepayAmountLamports } = (0, exports.calcFlashRepayAmount)({
        reserve: debtReserve,
        referralFeeBps: kaminoMarket.state.referralFeeBps,
        hasReferral: (0, kit_1.isSome)(referrer),
        flashBorrowAmountLamports: repayAmountLamports,
    });
    return { repayAmount, repayAmountLamports, flashRepayAmountLamports };
}
const calcFlashRepayAmount = (props) => {
    const { reserve, referralFeeBps, hasReferral, flashBorrowAmountLamports } = props;
    const { referrerFees, protocolFees } = reserve.calculateFlashLoanFees(flashBorrowAmountLamports, referralFeeBps, hasReferral);
    const flashRepayAmountLamports = flashBorrowAmountLamports.add(referrerFees).add(protocolFees);
    return {
        flashRepayAmountLamports,
    };
};
exports.calcFlashRepayAmount = calcFlashRepayAmount;
function calcMaxWithdrawCollateral(market, obligation, collReserveAddr, debtReserveAddr, repayAmountLamports) {
    const deposit = obligation.getDepositByReserve(collReserveAddr);
    const borrow = obligation.getBorrowByReserve(debtReserveAddr);
    const depositReserve = market.getReserveByAddress(deposit.reserveAddress);
    const debtReserve = market.getReserveByAddress(borrow.reserveAddress);
    const depositTotalLamports = deposit.amount.floor(); // TODO: can remove floor, we have lamports only for deposits
    // Calculate the market value of the remaining debt after repaying
    const remainingBorrowLamports = borrow.amount.sub(repayAmountLamports).ceil();
    const remainingBorrowAmount = remainingBorrowLamports.div(debtReserve.getMintFactor());
    let remainingBorrowsValue = remainingBorrowAmount.mul(debtReserve.getOracleMarketPrice());
    if (obligation.getBorrows().length > 1) {
        remainingBorrowsValue = obligation
            .getBorrows()
            .filter((p) => p.reserveAddress !== borrow.reserveAddress)
            .reduce((acc, b) => acc.add(b.marketValueRefreshed), new decimal_js_1.default('0'));
    }
    const hypotheticalWithdrawLamports = (0, repay_with_collateral_operations_1.getMaxCollateralFromRepayAmount)(repayAmountLamports.div(debtReserve.getMintFactor()), debtReserve, depositReserve);
    // Calculate the max withdraw ltv we can withdraw up to
    const maxWithdrawLtvCheck = (0, repay_with_collateral_operations_1.getMaxWithdrawLtvCheck)(obligation, repayAmountLamports, debtReserve, hypotheticalWithdrawLamports, depositReserve);
    // Calculate the max borrowable value remaining against deposits
    let maxBorrowableValueRemainingAgainstDeposits = new decimal_js_1.default('0');
    if (obligation.getDeposits().length > 1) {
        maxBorrowableValueRemainingAgainstDeposits = obligation
            .getDeposits()
            .filter((p) => p.reserveAddress !== deposit.reserveAddress)
            .reduce((acc, d) => {
            const { maxLtv, liquidationLtv } = obligation.getLtvForReserve(market, d.reserveAddress);
            const maxWithdrawLtv = maxWithdrawLtvCheck === repay_with_collateral_operations_1.MaxWithdrawLtvCheck.LIQUIDATION_THRESHOLD ? liquidationLtv : maxLtv;
            return acc.add(d.marketValueRefreshed.mul(maxWithdrawLtv));
        }, new decimal_js_1.default('0'));
    }
    // if the remaining borrow value is less than the
    // this means that the user's ltv is less or equal to the max ltv
    if (maxBorrowableValueRemainingAgainstDeposits.gte(remainingBorrowsValue)) {
        return {
            maxWithdrawableCollLamports: depositTotalLamports,
            canWithdrawAllColl: true,
            repayingAllDebt: repayAmountLamports.gte(borrow.amount),
        };
    }
    else {
        const { maxLtv: collMaxLtv, liquidationLtv: collLiquidationLtv } = obligation.getLtvForReserve(market, depositReserve.address);
        const maxWithdrawLtv = maxWithdrawLtvCheck === repay_with_collateral_operations_1.MaxWithdrawLtvCheck.LIQUIDATION_THRESHOLD ? collLiquidationLtv : collMaxLtv;
        const numerator = deposit.marketValueRefreshed
            .mul(maxWithdrawLtv)
            .add(maxBorrowableValueRemainingAgainstDeposits)
            .sub(remainingBorrowsValue);
        const denominator = depositReserve.getOracleMarketPrice().mul(maxWithdrawLtv);
        const maxCollWithdrawAmount = numerator.div(denominator);
        const maxWithdrawableCollLamports = maxCollWithdrawAmount.mul(depositReserve.getMintFactor()).floor();
        return {
            maxWithdrawableCollLamports,
            canWithdrawAllColl: false,
            repayingAllDebt: repayAmountLamports.gte(borrow.amount),
        };
    }
}
function estimateDebtRepaymentWithColl(props) {
    const { collAmount, priceDebtToColl, slippagePct, flashLoanFeePct, kaminoMarket, debtTokenMint, obligation, currentSlot, } = props;
    const slippageMultiplier = new decimal_js_1.default(1.0).add(slippagePct.div('100'));
    const flashLoanFeeMultiplier = new decimal_js_1.default(1.0).add(flashLoanFeePct.div('100'));
    const debtReserve = kaminoMarket.getExistingReserveByMint(debtTokenMint);
    const debtAfterSwap = collAmount.div(slippageMultiplier).div(priceDebtToColl);
    const debtAfterFlashLoanRepay = debtAfterSwap.div(flashLoanFeeMultiplier);
    const accruedInterestRate = obligation
        .estimateObligationInterestRate(kaminoMarket, debtReserve, obligation.getObligationLiquidityByReserve(debtReserve.address), currentSlot)
        .toDecimalPlaces(debtReserve.state.liquidity.mintDecimals.toNumber(), decimal_js_1.default.ROUND_CEIL);
    // Estimate slightly more, by adding 1% to IR in order to avoid the case where UI users can repay the max we allow them
    const debtIrAdjusted = debtAfterFlashLoanRepay
        .div(accruedInterestRate.mul(new decimal_js_1.default('1.01')))
        .toDecimalPlaces(debtReserve.state.liquidity.mintDecimals.toNumber(), decimal_js_1.default.ROUND_CEIL);
    return debtIrAdjusted;
}
function estimateCollNeededForDebtRepayment(props) {
    const { debtAmount, // in decimals
    priceDebtToColl, slippagePct, flashLoanFeePct, } = props;
    const slippageRatio = slippagePct.div('100');
    const flashLoanFeeRatio = flashLoanFeePct.div('100');
    const slippageMultiplier = new decimal_js_1.default(1.0).add(slippageRatio);
    const flashLoanFeeMultiplier = new decimal_js_1.default(1.0).add(flashLoanFeeRatio);
    const debtFlashLoanRepay = debtAmount.mul(flashLoanFeeMultiplier);
    const collToSwap = debtFlashLoanRepay.mul(slippageMultiplier).mul(priceDebtToColl);
    return collToSwap;
}
//# sourceMappingURL=repay_with_collateral_calcs.js.map