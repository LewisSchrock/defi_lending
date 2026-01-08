"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getScopeRefreshIxForObligationAndReserves = exports.getSetupIxs = exports.WITHDRAW_SLOT_OFFSET = void 0;
exports.getDepositWithLeverageSwapInputs = getDepositWithLeverageSwapInputs;
exports.getDepositWithLeverageIxs = getDepositWithLeverageIxs;
exports.getWithdrawWithLeverageSwapInputs = getWithdrawWithLeverageSwapInputs;
exports.getWithdrawWithLeverageIxs = getWithdrawWithLeverageIxs;
exports.buildWithdrawWithLeverageIxs = buildWithdrawWithLeverageIxs;
exports.getAdjustLeverageSwapInputs = getAdjustLeverageSwapInputs;
exports.getAdjustLeverageIxs = getAdjustLeverageIxs;
const kit_1 = require("@solana/kit");
const decimal_js_1 = __importDefault(require("decimal.js"));
const classes_1 = require("../classes");
const instructions_1 = require("./instructions");
const classes_2 = require("../classes");
const utils_1 = require("../utils");
const calcs_1 = require("./calcs");
const CreationParameters_1 = require("@kamino-finance/kliquidity-sdk/dist/utils/CreationParameters");
const token_1 = require("@solana-program/token");
const token_2022_1 = require("@solana-program/token-2022");
const consts_1 = require("../utils/consts");
exports.WITHDRAW_SLOT_OFFSET = 150; // Offset for the withdraw slot to underestimate the exchange rate
async function getDepositWithLeverageSwapInputs({ owner, kaminoMarket, debtTokenMint, collTokenMint, depositAmount, priceDebtToColl, slippagePct, obligation, referrer, currentSlot, targetLeverage, selectedTokenMint, obligationTypeTagOverride, scopeRefreshIx, budgetAndPriorityFeeIxs, quoteBufferBps, quoter, useV2Ixs, elevationGroupOverride, }) {
    const collReserve = kaminoMarket.getExistingReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getExistingReserveByMint(debtTokenMint);
    const solTokenReserve = kaminoMarket.getReserveByMint(utils_1.WRAPPED_SOL_MINT);
    const flashLoanFee = collReserve.getFlashLoanFee() || new decimal_js_1.default(0);
    const selectedTokenIsCollToken = selectedTokenMint === collTokenMint;
    const depositTokenIsSol = !solTokenReserve ? false : selectedTokenMint === solTokenReserve.getLiquidityMint();
    const calcs = (0, calcs_1.depositLeverageCalcs)({
        depositAmount: depositAmount,
        depositTokenIsCollToken: selectedTokenIsCollToken,
        depositTokenIsSol,
        priceDebtToColl,
        targetLeverage,
        slippagePct,
        flashLoanFee,
    });
    console.log('Ops Calcs', (0, classes_1.toJson)(calcs));
    const obligationType = checkObligationType(obligationTypeTagOverride, collTokenMint, debtTokenMint, kaminoMarket);
    // Build the repay & withdraw collateral tx to get the number of accounts
    const klendIxs = (await buildDepositWithLeverageIxs(kaminoMarket, debtReserve, collReserve, owner, obligation ? obligation : obligationType, referrer, currentSlot, depositTokenIsSol, scopeRefreshIx, calcs, budgetAndPriorityFeeIxs, [
        {
            preActionIxs: [],
            swapIxs: [],
            lookupTables: [],
            quote: {
                priceAInB: new decimal_js_1.default(0), // not used
                quoteResponse: undefined,
            },
        },
    ], useV2Ixs, elevationGroupOverride))[0];
    const uniqueKlendAccounts = (0, utils_1.uniqueAccountsWithProgramIds)(klendIxs.instructions);
    const swapInputAmount = (0, classes_2.numberToLamportsDecimal)(calcs.swapDebtTokenIn, debtReserve.stats.decimals).ceil();
    const swapInputsForQuote = {
        inputAmountLamports: swapInputAmount.mul(new decimal_js_1.default(1).add(quoteBufferBps.div(CreationParameters_1.FullBPS))),
        inputMint: debtTokenMint,
        outputMint: collTokenMint,
    };
    const swapQuote = await quoter(swapInputsForQuote, uniqueKlendAccounts);
    const quotePriceCalcs = (0, calcs_1.depositLeverageCalcs)({
        depositAmount: depositAmount,
        depositTokenIsCollToken: selectedTokenIsCollToken,
        depositTokenIsSol,
        priceDebtToColl: swapQuote.priceAInB,
        targetLeverage,
        slippagePct,
        flashLoanFee,
    });
    const swapInputAmountQuotePrice = (0, classes_2.numberToLamportsDecimal)(quotePriceCalcs.swapDebtTokenIn, debtReserve.stats.decimals).ceil();
    return {
        swapInputs: {
            inputAmountLamports: swapInputAmountQuotePrice,
            minOutAmountLamports: (0, classes_2.numberToLamportsDecimal)(quotePriceCalcs.flashBorrowInCollToken, collReserve.stats.decimals),
            inputMint: debtTokenMint,
            outputMint: collTokenMint,
        },
        flashLoanInfo: klendIxs.flashLoanInfo,
        initialInputs: {
            calcs: quotePriceCalcs,
            swapQuote,
            currentSlot,
            obligation: obligation ? obligation : obligationType,
            klendAccounts: uniqueKlendAccounts,
        },
    };
}
async function getDepositWithLeverageIxs({ owner, kaminoMarket, debtTokenMint, collTokenMint, depositAmount, priceDebtToColl, slippagePct, obligation, referrer, currentSlot, targetLeverage, selectedTokenMint, obligationTypeTagOverride, scopeRefreshIx, budgetAndPriorityFeeIxs, quoteBufferBps, quoter, swapper, elevationGroupOverride, useV2Ixs, }) {
    const { swapInputs, initialInputs } = await getDepositWithLeverageSwapInputs({
        owner,
        kaminoMarket,
        debtTokenMint,
        collTokenMint,
        depositAmount,
        priceDebtToColl,
        slippagePct,
        obligation,
        referrer,
        currentSlot,
        targetLeverage,
        selectedTokenMint,
        obligationTypeTagOverride,
        scopeRefreshIx,
        budgetAndPriorityFeeIxs,
        quoteBufferBps,
        quoter,
        useV2Ixs,
    });
    const depositSwapper = swapper;
    const swapsArray = await depositSwapper(swapInputs, initialInputs.klendAccounts, initialInputs.swapQuote);
    // Strategy lookup table logic removed
    const collReserve = kaminoMarket.getReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getReserveByMint(debtTokenMint);
    const solTokenReserve = kaminoMarket.getReserveByMint(utils_1.WRAPPED_SOL_MINT);
    const depositTokenIsSol = !solTokenReserve ? false : selectedTokenMint === solTokenReserve.getLiquidityMint();
    const depositWithLeverageIxs = await buildDepositWithLeverageIxs(kaminoMarket, debtReserve, collReserve, owner, initialInputs.obligation, referrer, currentSlot, depositTokenIsSol, scopeRefreshIx, initialInputs.calcs, budgetAndPriorityFeeIxs, swapsArray.map((swap) => {
        return {
            preActionIxs: [],
            swapIxs: swap.swapIxs,
            lookupTables: swap.lookupTables,
            quote: swap.quote,
        };
    }), useV2Ixs, elevationGroupOverride);
    return depositWithLeverageIxs.map((depositWithLeverageIxs, index) => {
        return {
            ixs: depositWithLeverageIxs.instructions,
            flashLoanInfo: depositWithLeverageIxs.flashLoanInfo,
            lookupTables: swapsArray[index].lookupTables,
            swapInputs,
            initialInputs,
            quote: swapsArray[index].quote.quoteResponse,
        };
    });
}
async function buildDepositWithLeverageIxs(market, debtReserve, collReserve, owner, obligation, referrer, currentSlot, depositTokenIsSol, scopeRefreshIx, calcs, budgetAndPriorityFeeIxs, swapQuoteIxsArray, useV2Ixs, elevationGroupOverride) {
    const collTokenMint = collReserve.getLiquidityMint();
    const debtTokenMint = debtReserve.getLiquidityMint();
    const [[collTokenAta]] = await Promise.all([
        (0, token_2022_1.findAssociatedTokenPda)({
            owner: owner.address,
            mint: collTokenMint,
            tokenProgram: collReserve.getLiquidityTokenProgram(),
        }),
    ]);
    // 1. Create atas & budget ixs
    const { budgetIxs, createAtasIxs } = await (0, exports.getSetupIxs)(owner, collTokenMint, collReserve, debtTokenMint, debtReserve, budgetAndPriorityFeeIxs);
    const fillWsolAtaIxs = [];
    if (depositTokenIsSol) {
        fillWsolAtaIxs.push(...(0, utils_1.getTransferWsolIxs)(owner, await (0, utils_1.getAssociatedTokenAddress)(utils_1.WRAPPED_SOL_MINT, owner.address), (0, kit_1.lamports)(BigInt((0, classes_2.numberToLamportsDecimal)(calcs.initDepositInSol, utils_1.SOL_DECIMALS).ceil().toString()))));
    }
    // 2. Flash borrow & repay the collateral amount needed for given leverage
    // if user deposits coll, then we borrow the diff, else we borrow the entire amount
    const { flashBorrowIx, flashRepayIx } = (0, instructions_1.getFlashLoanInstructions)({
        borrowIxIndex: createAtasIxs.length + fillWsolAtaIxs.length + (scopeRefreshIx.length > 0 ? 1 : 0),
        userTransferAuthority: owner,
        lendingMarketAuthority: await market.getLendingMarketAuthority(),
        lendingMarketAddress: market.getAddress(),
        reserve: collReserve,
        amountLamports: (0, classes_2.numberToLamportsDecimal)(calcs.flashBorrowInCollToken, collReserve.stats.decimals),
        destinationAta: collTokenAta,
        // TODO(referrals): once we support referrals, we will have to replace the placeholder args below:
        referrerAccount: (0, kit_1.none)(),
        referrerTokenState: (0, kit_1.none)(),
        programId: market.programId,
    });
    // 3. Deposit initial tokens + borrowed tokens into reserve
    const kaminoDepositAndBorrowAction = await classes_1.KaminoAction.buildDepositAndBorrowTxns(market, (0, classes_2.numberToLamportsDecimal)(calcs.collTokenToDeposit, collReserve.stats.decimals).floor().toString(), collTokenMint, (0, classes_2.numberToLamportsDecimal)(calcs.debtTokenToBorrow, debtReserve.stats.decimals).ceil().toString(), debtTokenMint, owner, obligation, useV2Ixs, undefined, 0, false, elevationGroupOverride === 0 ? false : true, // emode
    { skipInitialization: true, skipLutCreation: true }, // to be checked and created in a setup tx in the UI
    referrer, currentSlot);
    return swapQuoteIxsArray.map((swapQuoteIxs) => {
        // 4. Swap
        const { swapIxs } = swapQuoteIxs;
        const swapInstructions = (0, utils_1.removeBudgetIxs)(swapIxs);
        const flashBorrowReserve = collReserve;
        const flashLoanInfo = {
            flashBorrowReserve: flashBorrowReserve.address,
            flashLoanFee: flashBorrowReserve.getFlashLoanFee(),
        };
        return {
            flashLoanInfo,
            instructions: [
                ...scopeRefreshIx,
                ...createAtasIxs,
                ...fillWsolAtaIxs,
                ...[flashBorrowIx],
                ...classes_1.KaminoAction.actionToIxs(kaminoDepositAndBorrowAction),
                ...swapInstructions,
                ...[flashRepayIx],
                ...budgetIxs,
            ],
        };
    });
}
async function getWithdrawWithLeverageSwapInputs({ owner, kaminoMarket, debtTokenMint, collTokenMint, deposited, borrowed, obligation, referrer, currentSlot, withdrawAmount, priceCollToDebt, slippagePct, isClosingPosition, selectedTokenMint, budgetAndPriorityFeeIxs, scopeRefreshIx, quoteBufferBps, quoter, useV2Ixs, userSolBalanceLamports, }) {
    const collReserve = kaminoMarket.getReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getReserveByMint(debtTokenMint);
    const flashLoanFee = debtReserve.getFlashLoanFee() || new decimal_js_1.default(0);
    const selectedTokenIsCollToken = selectedTokenMint === collTokenMint;
    const inputTokenIsSol = selectedTokenMint === utils_1.WRAPPED_SOL_MINT;
    const calcs = (0, calcs_1.withdrawLeverageCalcs)(kaminoMarket, collReserve, debtReserve, priceCollToDebt, withdrawAmount, deposited, borrowed, currentSlot, isClosingPosition, selectedTokenIsCollToken, selectedTokenMint, obligation, flashLoanFee, slippagePct);
    const klendIxs = (await buildWithdrawWithLeverageIxs(kaminoMarket, debtReserve, collReserve, owner, obligation, referrer, currentSlot, isClosingPosition, inputTokenIsSol, scopeRefreshIx, calcs, budgetAndPriorityFeeIxs, [
        {
            preActionIxs: [],
            swapIxs: [],
            lookupTables: [],
            quote: {
                priceAInB: new decimal_js_1.default(0), // not used
                quoteResponse: undefined,
            },
        },
    ], useV2Ixs, userSolBalanceLamports))[0];
    const uniqueKlendAccounts = (0, utils_1.uniqueAccountsWithProgramIds)(klendIxs.instructions);
    const swapInputAmount = (0, classes_2.numberToLamportsDecimal)(calcs.collTokenSwapIn, collReserve.getMintDecimals()).ceil();
    const swapInputsForQuote = {
        inputAmountLamports: swapInputAmount.mul(new decimal_js_1.default(1).add(quoteBufferBps.div(CreationParameters_1.FullBPS))),
        inputMint: collTokenMint,
        outputMint: debtTokenMint,
    };
    const swapQuote = await quoter(swapInputsForQuote, uniqueKlendAccounts);
    const calcsQuotePrice = (0, calcs_1.withdrawLeverageCalcs)(kaminoMarket, collReserve, debtReserve, swapQuote.priceAInB, withdrawAmount, deposited, borrowed, currentSlot, isClosingPosition, selectedTokenIsCollToken, selectedTokenMint, obligation, flashLoanFee, slippagePct);
    const swapInputAmountQuotePrice = (0, classes_2.numberToLamportsDecimal)(calcsQuotePrice.collTokenSwapIn, collReserve.getMintDecimals()).ceil();
    return {
        swapInputs: {
            inputAmountLamports: swapInputAmountQuotePrice,
            minOutAmountLamports: calcsQuotePrice.repayAmount,
            inputMint: collTokenMint,
            outputMint: debtTokenMint,
        },
        flashLoanInfo: klendIxs.flashLoanInfo,
        initialInputs: {
            calcs: calcsQuotePrice,
            swapQuote,
            currentSlot,
            obligation,
            klendAccounts: uniqueKlendAccounts,
        },
    };
}
async function getWithdrawWithLeverageIxs({ owner, kaminoMarket, debtTokenMint, collTokenMint, obligation, deposited, borrowed, referrer, currentSlot, withdrawAmount, priceCollToDebt, slippagePct, isClosingPosition, selectedTokenMint, budgetAndPriorityFeeIxs, scopeRefreshIx, quoteBufferBps, quoter, swapper, useV2Ixs, userSolBalanceLamports, }) {
    const collReserve = kaminoMarket.getReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getReserveByMint(debtTokenMint);
    const inputTokenIsSol = selectedTokenMint === utils_1.WRAPPED_SOL_MINT;
    const { swapInputs, initialInputs } = await getWithdrawWithLeverageSwapInputs({
        owner,
        kaminoMarket,
        debtTokenMint,
        collTokenMint,
        deposited,
        borrowed,
        obligation,
        referrer,
        currentSlot,
        withdrawAmount,
        priceCollToDebt,
        slippagePct,
        isClosingPosition,
        selectedTokenMint,
        budgetAndPriorityFeeIxs,
        scopeRefreshIx,
        quoteBufferBps,
        quoter,
        useV2Ixs,
        userSolBalanceLamports,
    });
    const withdrawSwapper = swapper;
    const swapsArray = await withdrawSwapper(swapInputs, initialInputs.klendAccounts, initialInputs.swapQuote);
    // Strategy lookup table logic removed
    const withdrawWithLeverageIxs = await buildWithdrawWithLeverageIxs(kaminoMarket, debtReserve, collReserve, owner, obligation, referrer, currentSlot, isClosingPosition, inputTokenIsSol, scopeRefreshIx, initialInputs.calcs, budgetAndPriorityFeeIxs, swapsArray.map((swap) => {
        return {
            preActionIxs: [],
            swapIxs: swap.swapIxs,
            lookupTables: swap.lookupTables,
            quote: swap.quote,
        };
    }), useV2Ixs, userSolBalanceLamports);
    // Send ixs and lookup tables
    return withdrawWithLeverageIxs.map((ixs, index) => {
        return {
            ixs: ixs.instructions,
            flashLoanInfo: ixs.flashLoanInfo,
            lookupTables: swapsArray[index].lookupTables,
            swapInputs,
            initialInputs: initialInputs,
            quote: swapsArray[index].quote.quoteResponse,
        };
    });
}
async function buildWithdrawWithLeverageIxs(market, debtReserve, collReserve, owner, obligation, referrer, currentSlot, isClosingPosition, depositTokenIsSol, scopeRefreshIx, calcs, budgetAndPriorityFeeIxs, swapQuoteIxsArray, useV2Ixs, userSolBalanceLamports) {
    const collTokenMint = collReserve.getLiquidityMint();
    const debtTokenMint = debtReserve.getLiquidityMint();
    const debtTokenAta = await (0, utils_1.getAssociatedTokenAddress)(debtTokenMint, owner.address, debtReserve.getLiquidityTokenProgram());
    // 1. Create atas & budget txns & user metadata
    const { budgetIxs, createAtasIxs } = await (0, exports.getSetupIxs)(owner, collTokenMint, collReserve, debtTokenMint, debtReserve, budgetAndPriorityFeeIxs);
    const closeWsolAtaIxs = [];
    if (depositTokenIsSol || debtTokenMint === utils_1.WRAPPED_SOL_MINT) {
        const wsolAta = await (0, utils_1.getAssociatedTokenAddress)(utils_1.WRAPPED_SOL_MINT, owner.address);
        closeWsolAtaIxs.push((0, token_2022_1.getCloseAccountInstruction)({
            owner,
            destination: owner.address,
            account: wsolAta,
        }, { programAddress: token_1.TOKEN_PROGRAM_ADDRESS }));
    }
    // TODO: Mihai/Marius check if we can improve this logic and not convert any SOL
    // This is here so that we have enough wsol to repay in case the kAB swapped to sol after estimates is not enough
    const fillWsolAtaIxs = [];
    if (debtTokenMint === utils_1.WRAPPED_SOL_MINT) {
        const halfSolBalance = userSolBalanceLamports / consts_1.LAMPORTS_PER_SOL / 2;
        const balanceToWrap = halfSolBalance < 0.1 ? halfSolBalance : 0.1;
        fillWsolAtaIxs.push(...(0, utils_1.getTransferWsolIxs)(owner, await (0, utils_1.getAssociatedTokenAddress)(utils_1.WRAPPED_SOL_MINT, owner.address), (0, kit_1.lamports)(BigInt((0, classes_2.numberToLamportsDecimal)(balanceToWrap, utils_1.SOL_DECIMALS).ceil().toString()))));
    }
    // 2. Prepare the flash borrow and flash repay amounts and ixs
    // We borrow exactly how much we need to repay
    // and repay that + flash amount fee
    const { flashBorrowIx, flashRepayIx } = (0, instructions_1.getFlashLoanInstructions)({
        borrowIxIndex: createAtasIxs.length + fillWsolAtaIxs.length + (scopeRefreshIx.length > 0 ? 1 : 0),
        userTransferAuthority: owner,
        lendingMarketAuthority: await market.getLendingMarketAuthority(),
        lendingMarketAddress: market.getAddress(),
        reserve: debtReserve,
        amountLamports: (0, classes_2.numberToLamportsDecimal)(calcs.repayAmount, debtReserve.stats.decimals),
        destinationAta: debtTokenAta,
        referrerAccount: (0, kit_1.none)(),
        referrerTokenState: (0, kit_1.none)(),
        programId: market.programId,
    });
    // 3. Repay borrowed tokens and Withdraw tokens from reserve that will be swapped to repay flash loan
    const repayAndWithdrawAction = await classes_1.KaminoAction.buildRepayAndWithdrawTxns(market, isClosingPosition ? utils_1.U64_MAX : (0, classes_2.numberToLamportsDecimal)(calcs.repayAmount, debtReserve.stats.decimals).floor().toString(), debtTokenMint, isClosingPosition
        ? utils_1.U64_MAX
        : (0, classes_2.numberToLamportsDecimal)(calcs.depositTokenWithdrawAmount, collReserve.stats.decimals).ceil().toString(), collTokenMint, owner, currentSlot, obligation, useV2Ixs, undefined, 0, false, false, { skipInitialization: true, skipLutCreation: true }, // to be checked and created in a setup tx in the UI (won't be the case for withdraw anyway as this would be created in deposit)
    referrer);
    return swapQuoteIxsArray.map((swapQuoteIxs) => {
        const swapInstructions = (0, utils_1.removeBudgetIxs)(swapQuoteIxs.swapIxs);
        return {
            flashLoanInfo: {
                flashLoanFee: debtReserve.getFlashLoanFee(),
                flashBorrowReserve: debtReserve.address,
            },
            instructions: [
                ...scopeRefreshIx,
                ...createAtasIxs,
                ...fillWsolAtaIxs,
                ...[flashBorrowIx],
                ...classes_1.KaminoAction.actionToIxs(repayAndWithdrawAction),
                ...swapInstructions,
                ...[flashRepayIx],
                ...closeWsolAtaIxs,
                ...budgetIxs,
            ],
        };
    });
}
async function getAdjustLeverageSwapInputs({ owner, kaminoMarket, debtTokenMint, collTokenMint, obligation, depositedLamports, borrowedLamports, referrer, currentSlot, targetLeverage, priceCollToDebt, priceDebtToColl, slippagePct, budgetAndPriorityFeeIxs, scopeRefreshIx, quoteBufferBps, quoter, useV2Ixs, withdrawSlotOffset, userSolBalanceLamports, }) {
    const collReserve = kaminoMarket.getReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getReserveByMint(debtTokenMint);
    const deposited = (0, classes_1.lamportsToNumberDecimal)(depositedLamports, collReserve.stats.decimals);
    const borrowed = (0, classes_1.lamportsToNumberDecimal)(borrowedLamports, debtReserve.stats.decimals);
    // Getting current flash loan fee
    const currentLeverage = obligation.refreshedStats.leverage;
    const isDepositViaLeverage = targetLeverage.gte(new decimal_js_1.default(currentLeverage));
    let flashLoanFee;
    if (isDepositViaLeverage) {
        flashLoanFee = collReserve.getFlashLoanFee() || new decimal_js_1.default(0);
    }
    else {
        flashLoanFee = debtReserve.getFlashLoanFee() || new decimal_js_1.default(0);
    }
    const { adjustDepositPosition, adjustBorrowPosition } = (0, calcs_1.calcAdjustAmounts)({
        currentDepositPosition: deposited,
        currentBorrowPosition: borrowed,
        targetLeverage: targetLeverage,
        priceCollToDebt: priceCollToDebt,
        flashLoanFee: new decimal_js_1.default(flashLoanFee),
    });
    const isDeposit = adjustDepositPosition.gte(0) && adjustBorrowPosition.gte(0);
    if (isDepositViaLeverage !== isDeposit) {
        throw new Error('Invalid target leverage');
    }
    if (isDeposit) {
        const calcs = (0, calcs_1.adjustDepositLeverageCalcs)(debtReserve, adjustDepositPosition, adjustBorrowPosition, priceDebtToColl, flashLoanFee, slippagePct);
        // Build the repay & withdraw collateral tx to get the number of accounts
        const klendIxs = (await buildIncreaseLeverageIxs(owner, kaminoMarket, collTokenMint, debtTokenMint, obligation, referrer, currentSlot, calcs, scopeRefreshIx, [
            {
                preActionIxs: [],
                swapIxs: [],
                lookupTables: [],
                quote: {
                    priceAInB: new decimal_js_1.default(0), // not used
                    quoteResponse: undefined,
                },
            },
        ], budgetAndPriorityFeeIxs, useV2Ixs))[0];
        const uniqueKlendAccounts = (0, utils_1.uniqueAccountsWithProgramIds)(klendIxs.instructions);
        const swapInputAmount = (0, classes_2.numberToLamportsDecimal)(calcs.borrowAmount, debtReserve.stats.decimals).ceil();
        const swapInputsForQuote = {
            inputAmountLamports: swapInputAmount.mul(new decimal_js_1.default(1).add(quoteBufferBps.div(CreationParameters_1.FullBPS))),
            inputMint: debtTokenMint,
            outputMint: collTokenMint,
        };
        const swapQuote = await quoter(swapInputsForQuote, uniqueKlendAccounts);
        const { adjustDepositPosition: adjustDepositPositionQuotePrice, adjustBorrowPosition: adjustBorrowPositionQuotePrice, } = (0, calcs_1.calcAdjustAmounts)({
            currentDepositPosition: deposited,
            currentBorrowPosition: borrowed,
            targetLeverage: targetLeverage,
            priceCollToDebt: new decimal_js_1.default(1).div(swapQuote.priceAInB),
            flashLoanFee: new decimal_js_1.default(flashLoanFee),
        });
        const calcsQuotePrice = (0, calcs_1.adjustDepositLeverageCalcs)(debtReserve, adjustDepositPositionQuotePrice, adjustBorrowPositionQuotePrice, swapQuote.priceAInB, flashLoanFee, slippagePct);
        const swapInputAmountQuotePrice = (0, classes_2.numberToLamportsDecimal)(calcsQuotePrice.borrowAmount, debtReserve.getMintDecimals()).ceil();
        return {
            swapInputs: {
                inputAmountLamports: swapInputAmountQuotePrice,
                minOutAmountLamports: (0, classes_2.numberToLamportsDecimal)(calcsQuotePrice.adjustDepositPosition, collReserve.stats.decimals),
                inputMint: debtTokenMint,
                outputMint: collTokenMint,
            },
            flashLoanInfo: klendIxs.flashLoanInfo,
            initialInputs: {
                calcs: calcsQuotePrice,
                swapQuote,
                currentSlot,
                obligation: obligation,
                klendAccounts: uniqueKlendAccounts,
                isDeposit: isDeposit,
            },
        };
    }
    else {
        const calcs = (0, calcs_1.adjustWithdrawLeverageCalcs)(adjustDepositPosition, adjustBorrowPosition, flashLoanFee, slippagePct);
        const klendIxs = (await buildDecreaseLeverageIxs(owner, kaminoMarket, collTokenMint, debtTokenMint, obligation, referrer, currentSlot, calcs, scopeRefreshIx, [
            {
                preActionIxs: [],
                swapIxs: [],
                lookupTables: [],
                quote: {
                    priceAInB: new decimal_js_1.default(0), // not used
                    quoteResponse: undefined,
                },
            },
        ], budgetAndPriorityFeeIxs, useV2Ixs, withdrawSlotOffset, userSolBalanceLamports))[0];
        const uniqueKlendAccounts = (0, utils_1.uniqueAccountsWithProgramIds)(klendIxs.instructions);
        const swapInputAmount = (0, classes_2.numberToLamportsDecimal)(calcs.withdrawAmountWithSlippageAndFlashLoanFee, collReserve.state.liquidity.mintDecimals.toNumber()).ceil();
        const swapInputsForQuote = {
            inputAmountLamports: swapInputAmount.mul(new decimal_js_1.default(1).add(quoteBufferBps.div(CreationParameters_1.FullBPS))),
            inputMint: collTokenMint,
            outputMint: debtTokenMint,
        };
        const swapQuote = await quoter(swapInputsForQuote, uniqueKlendAccounts);
        const { adjustDepositPosition: adjustDepositPositionQuotePrice, adjustBorrowPosition: adjustBorrowPositionQuotePrice, } = (0, calcs_1.calcAdjustAmounts)({
            currentDepositPosition: deposited,
            currentBorrowPosition: borrowed,
            targetLeverage: targetLeverage,
            priceCollToDebt: swapQuote.priceAInB,
            flashLoanFee: new decimal_js_1.default(flashLoanFee),
        });
        const calcsQuotePrice = (0, calcs_1.adjustWithdrawLeverageCalcs)(adjustDepositPositionQuotePrice, adjustBorrowPositionQuotePrice, flashLoanFee, slippagePct);
        const swapInputAmountQuotePrice = (0, classes_2.numberToLamportsDecimal)(calcsQuotePrice.withdrawAmountWithSlippageAndFlashLoanFee, collReserve.getMintDecimals()).ceil();
        return {
            swapInputs: {
                inputAmountLamports: swapInputAmountQuotePrice,
                minOutAmountLamports: (0, classes_2.numberToLamportsDecimal)(calcsQuotePrice.adjustBorrowPosition.abs(), debtReserve.stats.decimals),
                inputMint: collTokenMint,
                outputMint: debtTokenMint,
            },
            flashLoanInfo: klendIxs.flashLoanInfo,
            initialInputs: {
                calcs: calcsQuotePrice,
                swapQuote,
                currentSlot,
                obligation,
                klendAccounts: uniqueKlendAccounts,
                isDeposit,
            },
        };
    }
}
async function getAdjustLeverageIxs({ owner, kaminoMarket, debtTokenMint, collTokenMint, obligation, depositedLamports, borrowedLamports, referrer, currentSlot, targetLeverage, priceCollToDebt, priceDebtToColl, slippagePct, budgetAndPriorityFeeIxs, scopeRefreshIx, quoteBufferBps, quoter, swapper, useV2Ixs, withdrawSlotOffset, userSolBalanceLamports, }) {
    const { swapInputs, initialInputs } = await getAdjustLeverageSwapInputs({
        owner,
        kaminoMarket,
        debtTokenMint,
        collTokenMint,
        obligation,
        depositedLamports,
        borrowedLamports,
        referrer,
        currentSlot,
        targetLeverage,
        priceCollToDebt,
        priceDebtToColl,
        slippagePct,
        budgetAndPriorityFeeIxs,
        scopeRefreshIx,
        quoteBufferBps,
        quoter,
        useV2Ixs,
        userSolBalanceLamports,
    });
    // leverage increased so we need to deposit and borrow more
    if (initialInputs.isDeposit) {
        const depositSwapper = swapper;
        const swapsArray = await depositSwapper(swapInputs, initialInputs.klendAccounts, initialInputs.swapQuote);
        const increaseLeverageIxs = await buildIncreaseLeverageIxs(owner, kaminoMarket, collTokenMint, debtTokenMint, obligation, referrer, currentSlot, initialInputs.calcs, scopeRefreshIx, swapsArray.map((swap) => {
            return {
                preActionIxs: [],
                swapIxs: swap.swapIxs,
                lookupTables: swap.lookupTables,
                quote: swap.quote,
            };
        }), budgetAndPriorityFeeIxs, useV2Ixs);
        return increaseLeverageIxs.map((ixs, index) => {
            return {
                ixs: ixs.instructions,
                flashLoanInfo: ixs.flashLoanInfo,
                lookupTables: swapsArray[index].lookupTables,
                swapInputs,
                initialInputs,
                quote: swapsArray[index].quote.quoteResponse,
            };
        });
    }
    else {
        console.log('Decreasing leverage');
        const withdrawSwapper = swapper;
        // 5. Get swap ixs
        const swapsArray = await withdrawSwapper(swapInputs, initialInputs.klendAccounts, initialInputs.swapQuote);
        const decreaseLeverageIxs = await buildDecreaseLeverageIxs(owner, kaminoMarket, collTokenMint, debtTokenMint, obligation, referrer, currentSlot, initialInputs.calcs, scopeRefreshIx, swapsArray.map((swap) => {
            return {
                preActionIxs: [],
                swapIxs: swap.swapIxs,
                lookupTables: swap.lookupTables,
                quote: swap.quote,
            };
        }), budgetAndPriorityFeeIxs, useV2Ixs, withdrawSlotOffset, userSolBalanceLamports);
        return decreaseLeverageIxs.map((ixs, index) => {
            return {
                ixs: ixs.instructions,
                flashLoanInfo: ixs.flashLoanInfo,
                lookupTables: swapsArray[index].lookupTables,
                swapInputs,
                initialInputs,
                quote: swapsArray[index].quote.quoteResponse,
            };
        });
    }
}
/**
 * Deposit and borrow tokens if leverage increased
 */
async function buildIncreaseLeverageIxs(owner, kaminoMarket, collTokenMint, debtTokenMint, obligation, referrer, currentSlot, calcs, scopeRefreshIx, swapQuoteIxsArray, budgetAndPriorityFeeIxs, useV2Ixs) {
    const collReserve = kaminoMarket.getExistingReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getExistingReserveByMint(debtTokenMint);
    const collTokenAta = await (0, utils_1.getAssociatedTokenAddress)(collTokenMint, owner.address, collReserve.getLiquidityTokenProgram());
    // 1. Create atas & budget txns
    const { budgetIxs, createAtasIxs } = await (0, exports.getSetupIxs)(owner, collTokenMint, collReserve, debtTokenMint, debtReserve, budgetAndPriorityFeeIxs);
    // 2. Create borrow flash loan instruction
    const { flashBorrowIx, flashRepayIx } = (0, instructions_1.getFlashLoanInstructions)({
        borrowIxIndex: createAtasIxs.length + (scopeRefreshIx.length > 0 ? 1 : 0), // TODO: how about user metadata ixs
        userTransferAuthority: owner,
        lendingMarketAuthority: await kaminoMarket.getLendingMarketAuthority(),
        lendingMarketAddress: kaminoMarket.getAddress(),
        reserve: collReserve,
        amountLamports: (0, classes_2.numberToLamportsDecimal)(calcs.adjustDepositPosition, collReserve.stats.decimals),
        destinationAta: collTokenAta,
        // TODO(referrals): once we support referrals, we will have to replace the placeholder args below:
        referrerAccount: (0, kit_1.none)(),
        referrerTokenState: (0, kit_1.none)(),
        programId: kaminoMarket.programId,
    });
    const depositAction = await classes_1.KaminoAction.buildDepositTxns(kaminoMarket, (0, classes_2.numberToLamportsDecimal)(calcs.adjustDepositPosition, collReserve.stats.decimals).floor().toString(), collTokenMint, owner, obligation, useV2Ixs, undefined, 0, false, false, { skipInitialization: true, skipLutCreation: true }, referrer, currentSlot);
    // 4. Borrow tokens in borrow token reserve that will be swapped to repay flash loan
    const borrowAction = await classes_1.KaminoAction.buildBorrowTxns(kaminoMarket, (0, classes_2.numberToLamportsDecimal)(calcs.borrowAmount, debtReserve.stats.decimals).ceil().toString(), debtTokenMint, owner, obligation, useV2Ixs, undefined, 0, false, false, { skipInitialization: true, skipLutCreation: true }, // to be checked and create in a setup tx in the UI (won't be the case for adjust anyway as this would be created in deposit)
    referrer, currentSlot);
    return swapQuoteIxsArray.map((swapQuoteIxs) => {
        const swapInstructions = (0, utils_1.removeBudgetIxs)(swapQuoteIxs.swapIxs);
        const ixs = [
            ...scopeRefreshIx,
            ...createAtasIxs,
            ...[flashBorrowIx],
            ...classes_1.KaminoAction.actionToIxs(depositAction),
            ...classes_1.KaminoAction.actionToIxs(borrowAction),
            ...swapInstructions,
            ...[flashRepayIx],
            ...budgetIxs,
        ];
        const flashBorrowReserve = collReserve;
        const res = {
            flashLoanInfo: {
                flashBorrowReserve: flashBorrowReserve.address,
                flashLoanFee: flashBorrowReserve.getFlashLoanFee(),
            },
            instructions: ixs,
        };
        return res;
    });
}
/**
 * Withdraw and repay tokens if leverage decreased
 */
async function buildDecreaseLeverageIxs(owner, kaminoMarket, collTokenMint, debtTokenMint, obligation, referrer, currentSlot, calcs, scopeRefreshIx, swapQuoteIxsArray, budgetAndPriorityFeeIxs, useV2Ixs, withdrawSlotOffset = exports.WITHDRAW_SLOT_OFFSET, userSolBalanceLamports) {
    const collReserve = kaminoMarket.getExistingReserveByMint(collTokenMint);
    const debtReserve = kaminoMarket.getExistingReserveByMint(debtTokenMint);
    const [debtTokenAta] = await (0, token_2022_1.findAssociatedTokenPda)({
        owner: owner.address,
        mint: debtTokenMint,
        tokenProgram: debtReserve.getLiquidityTokenProgram(),
    });
    // 1. Create atas & budget txns
    const { budgetIxs, createAtasIxs } = await (0, exports.getSetupIxs)(owner, collTokenMint, collReserve, debtTokenMint, debtReserve, budgetAndPriorityFeeIxs);
    // TODO: Mihai/Marius check if we can improve this logic and not convert any SOL
    // This is here so that we have enough wsol to repay in case the kAB swapped to sol after estimates is not enough
    const closeWsolAtaIxs = [];
    const fillWsolAtaIxs = [];
    if (debtTokenMint === utils_1.WRAPPED_SOL_MINT) {
        const wsolAta = await (0, utils_1.getAssociatedTokenAddress)(utils_1.WRAPPED_SOL_MINT, owner.address);
        closeWsolAtaIxs.push((0, token_2022_1.getCloseAccountInstruction)({
            owner,
            account: wsolAta,
            destination: owner.address,
        }, { programAddress: token_1.TOKEN_PROGRAM_ADDRESS }));
        const halfSolBalance = userSolBalanceLamports / consts_1.LAMPORTS_PER_SOL / 2;
        const balanceToWrap = halfSolBalance < 0.1 ? halfSolBalance : 0.1;
        fillWsolAtaIxs.push(...(0, utils_1.getTransferWsolIxs)(owner, wsolAta, (0, kit_1.lamports)(BigInt((0, classes_2.numberToLamportsDecimal)(balanceToWrap, debtReserve.stats.decimals).ceil().toString()))));
    }
    // 3. Flash borrow & repay amount to repay (debt)
    const { flashBorrowIx, flashRepayIx } = (0, instructions_1.getFlashLoanInstructions)({
        borrowIxIndex: createAtasIxs.length + fillWsolAtaIxs.length + (scopeRefreshIx.length > 0 ? 1 : 0),
        userTransferAuthority: owner,
        lendingMarketAuthority: await kaminoMarket.getLendingMarketAuthority(),
        lendingMarketAddress: kaminoMarket.getAddress(),
        reserve: debtReserve,
        amountLamports: (0, classes_2.numberToLamportsDecimal)(decimal_js_1.default.abs(calcs.adjustBorrowPosition), debtReserve.stats.decimals),
        destinationAta: debtTokenAta,
        // TODO(referrals): once we support referrals, we will have to replace the placeholder args below:
        referrerAccount: (0, kit_1.none)(),
        referrerTokenState: (0, kit_1.none)(),
        programId: kaminoMarket.programId,
    });
    // 4. Actually do the repay of the flash borrowed amounts
    const repayAction = await classes_1.KaminoAction.buildRepayTxns(kaminoMarket, (0, classes_2.numberToLamportsDecimal)(decimal_js_1.default.abs(calcs.adjustBorrowPosition), debtReserve.stats.decimals).floor().toString(), debtTokenMint, owner, obligation, useV2Ixs, undefined, currentSlot, undefined, 0, false, false, { skipInitialization: true, skipLutCreation: true }, // to be checked and create in a setup tx in the UI (won't be the case for adjust anyway as this would be created in deposit)
    referrer);
    const withdrawSlot = currentSlot - BigInt(withdrawSlotOffset);
    // 6. Withdraw collateral (a little bit more to be able to pay for the slippage on swap)
    const withdrawAction = await classes_1.KaminoAction.buildWithdrawTxns(kaminoMarket, (0, classes_2.numberToLamportsDecimal)(calcs.withdrawAmountWithSlippageAndFlashLoanFee, collReserve.stats.decimals).ceil().toString(), collTokenMint, owner, obligation, useV2Ixs, undefined, 0, false, false, { skipInitialization: true, skipLutCreation: true }, // to be checked and create in a setup tx in the UI (won't be the case for adjust anyway as this would be created in deposit)
    referrer, withdrawSlot);
    return swapQuoteIxsArray.map((swapQuoteIxs) => {
        const swapInstructions = (0, utils_1.removeBudgetIxs)(swapQuoteIxs.swapIxs);
        const ixs = [
            ...scopeRefreshIx,
            ...createAtasIxs,
            ...fillWsolAtaIxs,
            ...[flashBorrowIx],
            ...classes_1.KaminoAction.actionToIxs(repayAction),
            ...classes_1.KaminoAction.actionToIxs(withdrawAction),
            ...swapInstructions,
            ...[flashRepayIx],
            ...closeWsolAtaIxs,
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
const getSetupIxs = async (owner, collTokenMint, collReserve, debtTokenMint, debtReserve, budgetAndPriorityFeeIxs) => {
    const budgetIxs = budgetAndPriorityFeeIxs || (0, utils_1.getComputeBudgetAndPriorityFeeIxs)(3000000);
    const mintsWithTokenPrograms = getTokenMintsWithTokenPrograms(collTokenMint, collReserve, debtTokenMint, debtReserve);
    const createAtasIxs = (await (0, utils_1.createAtasIdempotent)(owner, mintsWithTokenPrograms)).map((x) => x.createAtaIx);
    return {
        budgetIxs,
        createAtasIxs,
    };
};
exports.getSetupIxs = getSetupIxs;
const getScopeRefreshIxForObligationAndReserves = async (market, collReserve, debtReserve, obligation, scopeRefreshConfig) => {
    const allReserves = obligation && (0, classes_1.isKaminoObligation)(obligation)
        ? [
            ...new Set([
                ...obligation.getDeposits().map((x) => x.reserveAddress),
                ...obligation.getBorrows().map((x) => x.reserveAddress),
                collReserve.address,
                debtReserve.address,
            ]),
        ]
        : [...new Set([collReserve.address, debtReserve.address])];
    const scopeRefreshIxs = [];
    const scopeTokensMap = (0, classes_1.getTokenIdsForScopeRefresh)(market, allReserves);
    if (scopeTokensMap.size > 0 && scopeRefreshConfig) {
        for (const [configPubkey, config] of scopeRefreshConfig.scopeConfigurations) {
            const tokenIds = scopeTokensMap.get(config.oraclePrices);
            if (tokenIds && tokenIds.length > 0) {
                const refreshIx = await scopeRefreshConfig.scope.refreshPriceListIx({ config: configPubkey }, tokenIds);
                if (refreshIx) {
                    scopeRefreshIxs.push(refreshIx);
                }
            }
        }
    }
    return scopeRefreshIxs;
};
exports.getScopeRefreshIxForObligationAndReserves = getScopeRefreshIxForObligationAndReserves;
const checkObligationType = (obligationTypeTag, collTokenMint, debtTokenMint, kaminoMarket) => {
    let obligationType;
    if (obligationTypeTag === utils_1.ObligationTypeTag.Multiply) {
        // multiply
        obligationType = new utils_1.MultiplyObligation(collTokenMint, debtTokenMint, kaminoMarket.programId);
    }
    else if (obligationTypeTag === utils_1.ObligationTypeTag.Leverage) {
        // leverage
        obligationType = new utils_1.LeverageObligation(collTokenMint, debtTokenMint, kaminoMarket.programId);
    }
    else {
        throw Error('Obligation type tag not supported for leverage, please use 1 - multiply or 3 - leverage');
    }
    return obligationType;
};
const getTokenMintsWithTokenPrograms = (collTokenMint, collReserve, debtTokenMint, debtReserve) => {
    return [
        {
            mint: collTokenMint,
            tokenProgram: collReserve.getLiquidityTokenProgram(),
        },
        {
            mint: debtTokenMint,
            tokenProgram: debtReserve.getLiquidityTokenProgram(),
        },
        {
            mint: collReserve.getCTokenMint(),
            tokenProgram: token_1.TOKEN_PROGRAM_ADDRESS,
        },
    ];
};
//# sourceMappingURL=operations.js.map