"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getMaxWithdrawLtvCheck = exports.MaxWithdrawLtvCheck = void 0;
exports.getRepayWithCollSwapInputs = getRepayWithCollSwapInputs;
exports.getRepayWithCollIxs = getRepayWithCollIxs;
exports.getMaxCollateralFromRepayAmount = getMaxCollateralFromRepayAmount;
const classes_1 = require("../classes");
const leverage_1 = require("../leverage");
const utils_1 = require("../utils");
const kit_1 = require("@solana/kit");
const decimal_js_1 = __importDefault(require("decimal.js"));
const repay_with_collateral_calcs_1 = require("./repay_with_collateral_calcs");
var MaxWithdrawLtvCheck;
(function (MaxWithdrawLtvCheck) {
    MaxWithdrawLtvCheck[MaxWithdrawLtvCheck["MAX_LTV"] = 0] = "MAX_LTV";
    MaxWithdrawLtvCheck[MaxWithdrawLtvCheck["LIQUIDATION_THRESHOLD"] = 1] = "LIQUIDATION_THRESHOLD";
})(MaxWithdrawLtvCheck || (exports.MaxWithdrawLtvCheck = MaxWithdrawLtvCheck = {}));
async function getRepayWithCollSwapInputs({ collTokenMint, currentSlot, debtTokenMint, kaminoMarket, owner, obligation, quoter, referrer, repayAmount, isClosingPosition, budgetAndPriorityFeeIxs, scopeRefreshIx, useV2Ixs, }) {
    const collReserve = kaminoMarket.getExistingReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getExistingReserveByMint(debtTokenMint);
    const { repayAmountLamports, flashRepayAmountLamports, repayAmount: finalRepayAmount, } = (0, repay_with_collateral_calcs_1.calcRepayAmountWithSlippage)(kaminoMarket, debtReserve, currentSlot, obligation, repayAmount, referrer);
    const debtPosition = obligation.getBorrowByReserve(debtReserve.address);
    const collPosition = obligation.getDepositByReserve(collReserve.address);
    if (!debtPosition) {
        throw new Error(`Debt position not found for ${debtReserve.stats.symbol} reserve ${debtReserve.address} in obligation ${obligation.obligationAddress}`);
    }
    if (!collPosition) {
        throw new Error(`Collateral position not found for ${collReserve.stats.symbol} reserve ${collReserve.address} in obligation ${obligation.obligationAddress}`);
    }
    const { maxWithdrawableCollLamports } = (0, repay_with_collateral_calcs_1.calcMaxWithdrawCollateral)(kaminoMarket, obligation, collReserve.address, debtReserve.address, repayAmountLamports);
    const maxCollNeededFromOracle = getMaxCollateralFromRepayAmount(finalRepayAmount, debtReserve, collReserve);
    const inputAmountLamports = decimal_js_1.default.min(maxWithdrawableCollLamports, maxCollNeededFromOracle);
    // Build the repay & withdraw collateral tx to get the number of accounts
    const klendIxs = (await buildRepayWithCollateralIxs(kaminoMarket, debtReserve, collReserve, owner, obligation, referrer, currentSlot, budgetAndPriorityFeeIxs, scopeRefreshIx, [
        {
            preActionIxs: [],
            swapIxs: [],
            lookupTables: [],
            quote: {},
        },
    ], isClosingPosition, repayAmountLamports, inputAmountLamports, useV2Ixs))[0];
    const uniqueKlendAccounts = (0, utils_1.uniqueAccountsWithProgramIds)(klendIxs.instructions);
    const swapQuoteInputs = {
        inputAmountLamports,
        inputMint: collTokenMint,
        outputMint: debtTokenMint,
    };
    const swapQuote = await quoter(swapQuoteInputs, uniqueKlendAccounts);
    const swapQuotePxDebtToColl = swapQuote.priceAInB;
    const collSwapInLamports = flashRepayAmountLamports
        .div(debtReserve.getMintFactor())
        .div(swapQuotePxDebtToColl)
        .mul(collReserve.getMintFactor())
        .ceil();
    return {
        swapInputs: {
            inputAmountLamports: collSwapInLamports,
            minOutAmountLamports: flashRepayAmountLamports,
            inputMint: collTokenMint,
            outputMint: debtTokenMint,
        },
        flashLoanInfo: klendIxs.flashLoanInfo,
        initialInputs: {
            debtRepayAmountLamports: repayAmountLamports,
            flashRepayAmountLamports,
            maxCollateralWithdrawLamports: maxWithdrawableCollLamports,
            swapQuote,
            currentSlot,
            klendAccounts: uniqueKlendAccounts,
        },
    };
}
async function getRepayWithCollIxs({ repayAmount, isClosingPosition, budgetAndPriorityFeeIxs, collTokenMint, currentSlot, debtTokenMint, kaminoMarket, owner, obligation, quoter, swapper, referrer, scopeRefreshIx, useV2Ixs, logger = console.log, }) {
    const { swapInputs, initialInputs } = await getRepayWithCollSwapInputs({
        collTokenMint,
        currentSlot,
        debtTokenMint,
        kaminoMarket,
        owner,
        obligation,
        quoter,
        referrer,
        repayAmount,
        isClosingPosition,
        budgetAndPriorityFeeIxs,
        scopeRefreshIx,
        useV2Ixs,
    });
    const { debtRepayAmountLamports, flashRepayAmountLamports, maxCollateralWithdrawLamports, swapQuote } = initialInputs;
    const { inputAmountLamports: collSwapInLamports } = swapInputs;
    const collReserve = kaminoMarket.getExistingReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getExistingReserveByMint(debtTokenMint);
    // the client should use these values to prevent this input, but the tx may succeed, so we don't want to fail
    // there is also a chance that the tx will consume debt token from the user's ata which they would not expect
    if (collSwapInLamports.greaterThan(maxCollateralWithdrawLamports)) {
        logger(`Collateral swap in amount ${collSwapInLamports} exceeds max withdrawable collateral ${maxCollateralWithdrawLamports}, tx may fail with slippage`);
        swapInputs.inputAmountLamports = maxCollateralWithdrawLamports;
    }
    const actualSwapInLamports = decimal_js_1.default.min(collSwapInLamports, maxCollateralWithdrawLamports);
    logger(`Expected to swap in: ${actualSwapInLamports.div(collReserve.getMintFactor())} ${collReserve.symbol}, for: ${flashRepayAmountLamports.div(debtReserve.getMintFactor())} ${debtReserve.symbol}, quoter px: ${swapQuote.priceAInB} ${debtReserve.symbol}/${collReserve.symbol}, required px: ${flashRepayAmountLamports
        .div(debtReserve.getMintFactor())
        .div(actualSwapInLamports.div(collReserve.getMintFactor()))} ${debtReserve.symbol}/${collReserve.symbol}`);
    const swapResponses = await swapper(swapInputs, initialInputs.klendAccounts, swapQuote);
    const repayWithCollateralIxs = await buildRepayWithCollateralIxs(kaminoMarket, debtReserve, collReserve, owner, obligation, referrer, currentSlot, budgetAndPriorityFeeIxs, scopeRefreshIx, swapResponses, isClosingPosition, debtRepayAmountLamports, swapInputs.inputAmountLamports, useV2Ixs);
    return repayWithCollateralIxs.map((ixs, index) => {
        return {
            ixs: ixs.instructions,
            lookupTables: swapResponses[index].lookupTables,
            swapInputs,
            flashLoanInfo: ixs.flashLoanInfo,
            initialInputs,
            quote: swapResponses[index].quote.quoteResponse,
        };
    });
}
async function buildRepayWithCollateralIxs(market, debtReserve, collReserve, owner, obligation, referrer, currentSlot, budgetAndPriorityFeeIxs, scopeRefreshIx, swapQuoteIxsArray, isClosingPosition, debtRepayAmountLamports, collWithdrawLamports, useV2Ixs) {
    // 1. Create atas & budget txns
    const budgetIxs = budgetAndPriorityFeeIxs || (0, utils_1.getComputeBudgetAndPriorityFeeIxs)(1_400_000);
    const atas = [
        { mint: collReserve.getLiquidityMint(), tokenProgram: collReserve.getLiquidityTokenProgram() },
        { mint: debtReserve.getLiquidityMint(), tokenProgram: debtReserve.getLiquidityTokenProgram() },
    ];
    const atasAndIxs = await (0, utils_1.createAtasIdempotent)(owner, atas);
    const [, { ata: debtTokenAta }] = atasAndIxs;
    // 2. Flash borrow & repay the debt to repay amount needed
    const { flashBorrowIx, flashRepayIx } = (0, leverage_1.getFlashLoanInstructions)({
        borrowIxIndex: atasAndIxs.length + (scopeRefreshIx.length > 0 ? 1 : 0),
        userTransferAuthority: owner,
        lendingMarketAuthority: await market.getLendingMarketAuthority(),
        lendingMarketAddress: market.getAddress(),
        reserve: debtReserve,
        amountLamports: debtRepayAmountLamports,
        destinationAta: debtTokenAta,
        // TODO(referrals): once we support referrals, we will have to replace the placeholder args below:
        referrerAccount: (0, kit_1.none)(),
        referrerTokenState: (0, kit_1.none)(),
        programId: market.programId,
    });
    const requestElevationGroup = !isClosingPosition && obligation.state.elevationGroup !== 0;
    const maxWithdrawLtvCheck = (0, exports.getMaxWithdrawLtvCheck)(obligation, debtRepayAmountLamports, debtReserve, collWithdrawLamports, collReserve);
    // 3. Repay using the flash borrowed funds & withdraw collateral to swap and pay the flash loan
    let repayAndWithdrawAction;
    if (maxWithdrawLtvCheck === MaxWithdrawLtvCheck.MAX_LTV) {
        repayAndWithdrawAction = await classes_1.KaminoAction.buildRepayAndWithdrawTxns(market, isClosingPosition ? utils_1.U64_MAX : debtRepayAmountLamports.toString(), debtReserve.getLiquidityMint(), isClosingPosition ? utils_1.U64_MAX : collWithdrawLamports.toString(), collReserve.getLiquidityMint(), owner, currentSlot, obligation, useV2Ixs, undefined, 0, false, requestElevationGroup, undefined, referrer);
    }
    else {
        repayAndWithdrawAction = await classes_1.KaminoAction.buildRepayAndWithdrawV2Txns(market, isClosingPosition ? utils_1.U64_MAX : debtRepayAmountLamports.toString(), debtReserve.getLiquidityMint(), isClosingPosition ? utils_1.U64_MAX : collWithdrawLamports.toString(), collReserve.getLiquidityMint(), owner, currentSlot, obligation, undefined, 0, false, requestElevationGroup, undefined, referrer);
    }
    // 4. Swap collateral to debt to repay flash loan
    return swapQuoteIxsArray.map((swapQuoteIxs) => {
        const { preActionIxs, swapIxs } = swapQuoteIxs;
        const swapInstructions = (0, utils_1.removeBudgetIxs)(swapIxs);
        const ixs = [
            ...scopeRefreshIx,
            ...atasAndIxs.map((x) => x.createAtaIx),
            flashBorrowIx,
            ...preActionIxs,
            ...classes_1.KaminoAction.actionToIxs(repayAndWithdrawAction),
            ...swapInstructions,
            flashRepayIx,
            ...budgetIxs,
        ];
        const res = {
            flashLoanInfo: {
                flashBorrowReserve: debtReserve.address,
                flashLoanFee: debtReserve.getFlashLoanFee(),
            },
            instructions: ixs,
        };
        return res;
    });
}
const getMaxWithdrawLtvCheck = (obligation, repayAmountLamports, debtReserve, collWithdrawAmount, collReserve) => {
    const [finalLtv, finalMaxLtv] = calculatePostOperationLtv(obligation, repayAmountLamports, debtReserve, collWithdrawAmount, collReserve);
    if (finalLtv.lte(finalMaxLtv)) {
        return MaxWithdrawLtvCheck.MAX_LTV;
    }
    return obligation.refreshedStats.userTotalBorrowBorrowFactorAdjusted.gte(obligation.refreshedStats.borrowLimit)
        ? MaxWithdrawLtvCheck.LIQUIDATION_THRESHOLD
        : MaxWithdrawLtvCheck.MAX_LTV;
};
exports.getMaxWithdrawLtvCheck = getMaxWithdrawLtvCheck;
function calculatePostOperationLtv(obligation, repayAmountLamports, debtReserve, collWithdrawAmount, collReserve) {
    const repayValue = repayAmountLamports
        .div(debtReserve.getMintFactor())
        .mul(debtReserve.getOracleMarketPrice())
        .mul(debtReserve.getBorrowFactor());
    const collWithdrawValue = collWithdrawAmount.div(collReserve.getMintFactor()).mul(collReserve.getOracleMarketPrice());
    // Calculate new borrow value and deposit value
    const newBorrowBfValue = decimal_js_1.default.max(new decimal_js_1.default(0), obligation.refreshedStats.userTotalBorrowBorrowFactorAdjusted.sub(repayValue));
    const newDepositValue = decimal_js_1.default.max(new decimal_js_1.default(0), obligation.refreshedStats.userTotalDeposit.sub(collWithdrawValue));
    const newMaxBorrowableValue = decimal_js_1.default.max(new decimal_js_1.default(0), obligation.refreshedStats.borrowLimit.sub(collWithdrawValue.mul(collReserve.stats.loanToValue)));
    const newMaxLtv = newMaxBorrowableValue.div(newDepositValue);
    // return final ltv and final max ltv
    return [newBorrowBfValue.div(newDepositValue), newMaxLtv];
}
function getMaxCollateralFromRepayAmount(repayAmount, debtReserve, collReserve) {
    // sanity check: we have extra collateral to swap, but we want to ensure we don't quote for way more than needed and get a bad px
    return repayAmount
        .mul(debtReserve.getOracleMarketPrice())
        .div(collReserve.getOracleMarketPrice())
        .mul('1.1')
        .mul(collReserve.getMintFactor())
        .ceil();
}
//# sourceMappingURL=repay_with_collateral_operations.js.map