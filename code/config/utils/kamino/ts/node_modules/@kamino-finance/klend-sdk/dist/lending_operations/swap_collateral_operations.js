"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getSwapCollIxs = getSwapCollIxs;
const classes_1 = require("../classes");
const leverage_1 = require("../leverage");
const utils_1 = require("../utils");
const kit_1 = require("@solana/kit");
const decimal_js_1 = __importDefault(require("decimal.js"));
const token_1 = require("@solana-program/token");
const token_2022_1 = require("@solana-program/token-2022");
/**
 * Constructs instructions needed to partially/fully swap the given source collateral for some other collateral type.
 */
async function getSwapCollIxs(inputs) {
    const [args, context] = extractArgsAndContext(inputs);
    // Conceptually, we need to construct the following ixs:
    //  0. any set-up, like budgeting and ATAs
    //  1. `flash-borrowed target coll = targetCollReserve.flashBorrow()`
    //  2. `targetCollReserve.deposit(flash-borrowed target coll)`
    //  3. `sourceCollReserve.withdraw(requested amount to be coll-swapped)`
    //  4. `externally-swapped target coll = externalDex.swap(withdrawn current coll)`
    //  5. `flashRepay(externally-swapped target coll)`
    // However, there is a cyclic dependency:
    //  - To construct 4. (specifically, to query the external swap quote), we need to know all accounts used by Kamino's
    //    own ixs.
    //  - To construct 1. (i.e. flash-borrow), we need to know the target collateral swap-out from 4.
    // Construct the Klend's own ixs with a fake swap-out (only to learn the klend accounts used):
    const fakeKlendIxs = await getKlendIxs(args, FAKE_TARGET_COLL_SWAP_OUT_AMOUNT, context, inputs.scopeRefreshIx);
    const klendAccounts = (0, utils_1.uniqueAccountsWithProgramIds)(listIxs(fakeKlendIxs));
    // Construct the external swap ixs (and learn the actual swap-out amount):
    const externalSwapIxsArray = await getExternalSwapIxs(args, klendAccounts, context);
    return Promise.all(externalSwapIxsArray.map(async (externalSwapIxs) => {
        // We now have the full information needed to simulate the end-state, so let's check that the operation is legal:
        context.logger(`Expected to swap ${args.sourceCollSwapAmount} ${context.sourceCollReserve.symbol} collateral into ${externalSwapIxs.swapOutAmount} ${context.targetCollReserve.symbol} collateral`);
        checkResultingObligationValid(args, externalSwapIxs.swapOutAmount, context);
        // Construct the Klend's own ixs with an actual swap-out amount:
        const klendIxs = await getKlendIxs(args, externalSwapIxs.swapOutAmount, context, inputs.scopeRefreshIx);
        return {
            ixs: listIxs(klendIxs, externalSwapIxs.ixs),
            lookupTables: externalSwapIxs.luts,
            useV2Ixs: context.useV2Ixs,
            simulationDetails: {
                flashLoan: {
                    targetCollFlashBorrowedAmount: klendIxs.simulationDetails.targetCollFlashBorrowedAmount,
                    targetCollFlashRepaidAmount: externalSwapIxs.swapOutAmount,
                },
                externalSwap: {
                    sourceCollSwapInAmount: args.sourceCollSwapAmount, // repeated `/inputs.sourceCollSwapAmount`, only for clarity
                    targetCollSwapOutAmount: externalSwapIxs.swapOutAmount, // repeated `../flashLoan.targetCollFlashRepaidAmount`, only for clarity
                    quoteResponse: externalSwapIxs.simulationDetails.quoteResponse,
                },
            },
        };
    }));
}
function extractArgsAndContext(inputs) {
    if (inputs.sourceCollTokenMint === inputs.targetCollTokenMint) {
        throw new Error(`Cannot swap from/to the same collateral`);
    }
    if (inputs.sourceCollSwapAmount.lte(0)) {
        throw new Error(`Cannot swap a negative amount`);
    }
    return [
        {
            sourceCollSwapAmount: inputs.sourceCollSwapAmount,
            isClosingSourceColl: inputs.isClosingSourceColl,
            newElevationGroup: inputs.market.getExistingElevationGroup(inputs.newElevationGroup, 'Newly-requested'),
        },
        {
            budgetAndPriorityFeeIxs: inputs.budgetAndPriorityFeeIxs || (0, utils_1.getComputeBudgetAndPriorityFeeIxs)(utils_1.DEFAULT_MAX_COMPUTE_UNITS),
            sourceCollReserve: inputs.market.getExistingReserveByMint(inputs.sourceCollTokenMint, 'Current collateral'),
            targetCollReserve: inputs.market.getExistingReserveByMint(inputs.targetCollTokenMint, 'Target collateral'),
            logger: console.log,
            market: inputs.market,
            obligation: inputs.obligation,
            owner: inputs.owner,
            quoter: inputs.quoter,
            swapper: inputs.swapper,
            referrer: inputs.referrer,
            scopeRefreshIx: inputs.scopeRefreshIx,
            currentSlot: inputs.currentSlot,
            useV2Ixs: inputs.useV2Ixs,
        },
    ];
}
const FAKE_TARGET_COLL_SWAP_OUT_AMOUNT = new decimal_js_1.default(1); // see the lengthy `getSwapCollIxs()` impl comment
async function getKlendIxs(args, targetCollSwapOutAmount, context, scopeRefreshIx) {
    const { ataCreationIxs, targetCollAta } = await getAtaCreationIxs(context);
    const setupIxs = [...ataCreationIxs];
    if (scopeRefreshIx) {
        setupIxs.unshift(...scopeRefreshIx);
    }
    const targetCollFlashBorrowedAmount = calculateTargetCollFlashBorrowedAmount(targetCollSwapOutAmount, context);
    const { targetCollFlashBorrowIx, targetCollFlashRepayIx } = await getTargetCollFlashLoanIxs(targetCollFlashBorrowedAmount, setupIxs.length, targetCollAta, context);
    const depositTargetCollIxs = await getDepositTargetCollIxs(targetCollFlashBorrowedAmount, context);
    const withdrawSourceCollIxs = await getWithdrawSourceCollIxs(args, depositTargetCollIxs.removesElevationGroup, context);
    const cleanupIxs = [...(await getAtaCloseIxs(context)), ...context.budgetAndPriorityFeeIxs];
    return {
        setupIxs,
        flashLoanInfo: {
            flashBorrowReserve: context.targetCollReserve.address,
            flashLoanFee: context.targetCollReserve.getFlashLoanFee(),
        },
        targetCollFlashBorrowIx,
        depositTargetCollIxs: depositTargetCollIxs.ixs,
        withdrawSourceCollIxs,
        targetCollFlashRepayIx,
        cleanupIxs,
        simulationDetails: {
            targetCollFlashBorrowedAmount,
        },
    };
}
function calculateTargetCollFlashBorrowedAmount(targetCollFlashRepaidAmount, context) {
    const { protocolFees, referrerFees } = context.targetCollReserve.calculateFees(targetCollFlashRepaidAmount.mul(context.targetCollReserve.getMintFactor()), context.targetCollReserve.getFlashLoanFee(), classes_1.FeeCalculation.Inclusive, // denotes that the amount parameter above means "to be repaid" (not "borrowed")
    context.market.state.referralFeeBps, (0, kit_1.isSome)(context.referrer));
    const targetCollFlashLoanFee = protocolFees.add(referrerFees).div(context.targetCollReserve.getMintFactor());
    return targetCollFlashRepaidAmount.sub(targetCollFlashLoanFee);
}
async function getAtaCreationIxs(context) {
    const atasAndAtaCreationIxs = await (0, utils_1.createAtasIdempotent)(context.owner, [
        {
            mint: context.sourceCollReserve.getLiquidityMint(),
            tokenProgram: context.sourceCollReserve.getLiquidityTokenProgram(),
        },
        {
            mint: context.targetCollReserve.getLiquidityMint(),
            tokenProgram: context.targetCollReserve.getLiquidityTokenProgram(),
        },
    ]);
    return {
        ataCreationIxs: atasAndAtaCreationIxs.map((tuple) => tuple.createAtaIx),
        targetCollAta: atasAndAtaCreationIxs[1].ata,
    };
}
async function getAtaCloseIxs(context) {
    const ataCloseIxs = [];
    if (context.sourceCollReserve.getLiquidityMint() === utils_1.WRAPPED_SOL_MINT ||
        context.targetCollReserve.getLiquidityMint() === utils_1.WRAPPED_SOL_MINT) {
        const owner = context.owner;
        const wsolAta = await (0, utils_1.getAssociatedTokenAddress)(utils_1.WRAPPED_SOL_MINT, owner.address);
        ataCloseIxs.push((0, token_2022_1.getCloseAccountInstruction)({ account: wsolAta, owner, destination: owner.address }, { programAddress: token_1.TOKEN_PROGRAM_ADDRESS }));
    }
    return ataCloseIxs;
}
async function getTargetCollFlashLoanIxs(targetCollAmount, flashBorrowIxIndex, destinationAta, context) {
    const { flashBorrowIx: targetCollFlashBorrowIx, flashRepayIx: targetCollFlashRepayIx } = (0, leverage_1.getFlashLoanInstructions)({
        borrowIxIndex: flashBorrowIxIndex,
        userTransferAuthority: context.owner,
        lendingMarketAuthority: await context.market.getLendingMarketAuthority(),
        lendingMarketAddress: context.market.getAddress(),
        reserve: context.targetCollReserve,
        amountLamports: targetCollAmount.mul(context.targetCollReserve.getMintFactor()),
        destinationAta,
        // TODO(referrals): once we support referrals, we will have to replace the placeholder args below:
        referrerAccount: (0, kit_1.none)(),
        referrerTokenState: (0, kit_1.none)(),
        programId: context.market.programId,
    });
    return { targetCollFlashBorrowIx, targetCollFlashRepayIx };
}
async function getDepositTargetCollIxs(targetCollAmount, context) {
    const removesElevationGroup = mustRemoveElevationGroupBeforeDeposit(context);
    const depositCollAction = await classes_1.KaminoAction.buildDepositTxns(context.market, targetCollAmount.mul(context.targetCollReserve.getMintFactor()).toString(), // in lamports
    context.targetCollReserve.getLiquidityMint(), context.owner, context.obligation, context.useV2Ixs, undefined, // we create the scope refresh ix outside of KaminoAction
    0, // no extra compute budget
    false, // we do not need ATA ixs here (we construct and close them ourselves)
    removesElevationGroup, // we may need to (temporarily) remove the elevation group; the same or a different one will be set on withdraw, if requested
    { skipInitialization: true, skipLutCreation: true }, // we are dealing with an existing obligation, no need to create user metadata
    context.referrer, context.currentSlot, removesElevationGroup ? 0 : undefined // only applicable when removing the group
    );
    return {
        ixs: classes_1.KaminoAction.actionToIxs(depositCollAction),
        removesElevationGroup,
    };
}
function mustRemoveElevationGroupBeforeDeposit(context) {
    if (context.obligation.deposits.has(context.targetCollReserve.address)) {
        return false; // the target collateral already was a reserve in the obligation, so we do not affect any potential elevation group
    }
    const currentElevationGroupId = context.obligation.state.elevationGroup;
    if (currentElevationGroupId == 0) {
        return false; // simply nothing to remove
    }
    if (!context.targetCollReserve.state.config.elevationGroups.includes(currentElevationGroupId)) {
        return true; // the target collateral reserve is NOT in the obligation's group - must remove the group
    }
    const currentElevationGroup = context.market.getElevationGroup(currentElevationGroupId);
    if (context.obligation.deposits.size >= currentElevationGroup.maxReservesAsCollateral) {
        return true; // the obligation is already at its elevation group's deposits count limit - must remove the group
    }
    return false; // the obligation has some elevation group and the new collateral can be added to it
}
async function getWithdrawSourceCollIxs(args, depositRemovedElevationGroup, context) {
    const withdrawnSourceCollLamports = args.isClosingSourceColl
        ? utils_1.U64_MAX
        : args.sourceCollSwapAmount.mul(context.sourceCollReserve.getMintFactor()).toString();
    const requestedElevationGroup = elevationGroupIdToRequestAfterWithdraw(args, depositRemovedElevationGroup, context);
    const withdrawCollAction = await classes_1.KaminoAction.buildWithdrawTxns(context.market, withdrawnSourceCollLamports, context.sourceCollReserve.getLiquidityMint(), context.owner, context.obligation, context.useV2Ixs, undefined, // we create the scope refresh ix outside of KaminoAction
    0, // no extra compute budget
    false, // we do not need ATA ixs here (we construct and close them ourselves)
    requestedElevationGroup !== undefined, // the `elevationGroupIdToRequestAfterWithdraw()` has already decided on this
    { skipInitialization: true, skipLutCreation: true }, // we are dealing with an existing obligation, no need to create user metadata
    context.referrer, context.currentSlot, requestedElevationGroup, context.obligation.deposits.has(context.targetCollReserve.address) // if our obligation already had the target coll...
        ? undefined // ... then we need no customizations here, but otherwise...
        : {
            addedDepositReserves: [context.targetCollReserve.address], // ... we need to inform our infra that the obligation now has one more reserve that needs refreshing.
        });
    return classes_1.KaminoAction.actionToIxs(withdrawCollAction);
}
function elevationGroupIdToRequestAfterWithdraw(args, depositRemovedElevationGroup, context) {
    const obligationInitialElevationGroup = context.obligation.state.elevationGroup;
    const requestedElevationGroupId = args.newElevationGroup?.elevationGroup ?? 0;
    if (requestedElevationGroupId === 0) {
        // the user doesn't want any elevation group, and...
        if (obligationInitialElevationGroup === 0) {
            return undefined; // ... he already didn't have it - fine!
        }
        if (depositRemovedElevationGroup) {
            return undefined; // ... our deposit already forced us to remove it - fine!
        }
        return 0; // ... but he *did have one*, and our deposit didn't need to remove it - so we remove it now, just to satisfy him
    }
    else {
        // the user wants some elevation group, and...
        if (depositRemovedElevationGroup) {
            return requestedElevationGroupId; // ...our deposit forced us to remove it - so we now request the new one, whatever it is
        }
        if (obligationInitialElevationGroup === requestedElevationGroupId) {
            return undefined; // ...and he already had exactly this one - fine!
        }
        return requestedElevationGroupId; // ...and he had some different one - so we request the new one
    }
}
async function getExternalSwapIxs(args, klendAccounts, context) {
    const externalSwapInputs = {
        inputAmountLamports: args.sourceCollSwapAmount.mul(context.sourceCollReserve.getMintFactor()),
        inputMint: context.sourceCollReserve.getLiquidityMint(),
        outputMint: context.targetCollReserve.getLiquidityMint(),
    };
    const externalSwapQuote = await context.quoter(externalSwapInputs, klendAccounts);
    const externalSwapIxsAndLuts = await context.swapper(externalSwapInputs, klendAccounts, externalSwapQuote);
    // Note: we can ignore the returned `preActionIxs` field - we do not request any of them from the swapper.
    return externalSwapIxsAndLuts.map((externalSwapIxsAndLuts) => {
        const swapOutAmount = externalSwapIxsAndLuts.quote.priceAInB.mul(args.sourceCollSwapAmount);
        return {
            swapOutAmount,
            ixs: externalSwapIxsAndLuts.swapIxs,
            luts: externalSwapIxsAndLuts.lookupTables,
            simulationDetails: {
                quoteResponse: externalSwapIxsAndLuts.quote.quoteResponse,
            },
        };
    });
}
function checkResultingObligationValid(args, targetCollAmount, context) {
    // The newly-requested elevation group must have its conditions satisfied:
    if (args.newElevationGroup !== null) {
        // Note: we cannot use the existing `isLoanEligibleForElevationGroup()`, since it operates on a `KaminoObligation`,
        // and our instance is stale (we want to assert on the state *after* potential changes).
        // Let's start with the (simpler) debt reserve - it cannot change during a coll-swap:
        const debtReserveAddresses = [...context.obligation.borrows.keys()];
        if (debtReserveAddresses.length > 1) {
            throw new Error(`The obligation with ${debtReserveAddresses.length} debt reserves cannot request any elevation group`);
        }
        if (debtReserveAddresses.length == 1) {
            const debtReserveAddress = debtReserveAddresses[0];
            if (args.newElevationGroup.debtReserve !== debtReserveAddress) {
                throw new Error(`The obligation with debt reserve ${debtReserveAddress} cannot request elevation group ${args.newElevationGroup.elevationGroup}`);
            }
        }
        // Now the coll reserves: this requires first finding out the resulting set of deposits:
        const collReserveAddresses = new Set([
            ...context.obligation.deposits.keys(),
            context.targetCollReserve.address,
        ]);
        if (args.isClosingSourceColl) {
            collReserveAddresses.delete(context.sourceCollReserve.address);
        }
        if (collReserveAddresses.size > args.newElevationGroup.maxReservesAsCollateral) {
            throw new Error(`The obligation with ${collReserveAddresses.size} collateral reserves cannot request elevation group ${args.newElevationGroup.elevationGroup}`);
        }
        for (const collReserveAddress of [...collReserveAddresses]) {
            if (!args.newElevationGroup.collateralReserves.has(collReserveAddress)) {
                throw new Error(`The obligation with collateral reserve ${collReserveAddress} cannot request elevation group ${args.newElevationGroup.elevationGroup}`);
            }
        }
    }
    // The LTV cannot be exceeded:
    const effectiveWithdrawAmount = args.isClosingSourceColl
        ? context.obligation.getDepositAmountByReserve(context.sourceCollReserve)
        : args.sourceCollSwapAmount;
    const resultingStats = context.obligation.getPostSwapCollObligationStats({
        withdrawAmountLamports: effectiveWithdrawAmount.mul(context.sourceCollReserve.getMintFactor()),
        withdrawReserveAddress: context.sourceCollReserve.address,
        depositAmountLamports: targetCollAmount.mul(context.targetCollReserve.getMintFactor()),
        depositReserveAddress: context.targetCollReserve.address,
        market: context.market,
        newElevationGroup: args.newElevationGroup?.elevationGroup ?? 0,
        slot: context.currentSlot,
    });
    const maxLtv = resultingStats.borrowLimit.div(resultingStats.userTotalCollateralDeposit);
    if (resultingStats.loanToValue > maxLtv) {
        throw new Error(`Swapping collateral ${effectiveWithdrawAmount} ${context.sourceCollReserve.symbol} into ${targetCollAmount} ${context.targetCollReserve.symbol} would result in the obligation's LTV ${resultingStats.loanToValue} exceeding its max LTV ${maxLtv}`);
    }
}
function listIxs(klendIxs, externalSwapIxs) {
    return [
        ...klendIxs.setupIxs,
        klendIxs.targetCollFlashBorrowIx,
        ...klendIxs.depositTargetCollIxs,
        ...klendIxs.withdrawSourceCollIxs,
        ...(externalSwapIxs || []),
        klendIxs.targetCollFlashRepayIx,
        ...klendIxs.cleanupIxs,
    ];
}
//# sourceMappingURL=swap_collateral_operations.js.map