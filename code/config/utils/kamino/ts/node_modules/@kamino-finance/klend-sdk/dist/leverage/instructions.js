"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getRepayFlashLoanInstruction = exports.getBorrowFlashLoanInstruction = exports.getFlashLoanInstructions = void 0;
const lib_1 = require("../lib");
const bn_js_1 = __importDefault(require("bn.js"));
const sysvars_1 = require("@solana/sysvars");
const getFlashLoanInstructions = (args) => {
    const flashBorrowIx = (0, exports.getBorrowFlashLoanInstruction)({
        userTransferAuthority: args.userTransferAuthority,
        lendingMarketAuthority: args.lendingMarketAuthority,
        lendingMarketAddress: args.lendingMarketAddress,
        reserve: args.reserve,
        amountLamports: args.amountLamports,
        destinationAta: args.destinationAta,
        referrerAccount: args.referrerAccount,
        referrerTokenState: args.referrerTokenState,
        programId: args.programId,
    });
    const flashRepayIx = (0, exports.getRepayFlashLoanInstruction)({
        borrowIxIndex: args.borrowIxIndex,
        userTransferAuthority: args.userTransferAuthority,
        lendingMarketAuthority: args.lendingMarketAuthority,
        lendingMarketAddress: args.lendingMarketAddress,
        reserve: args.reserve,
        amountLamports: args.amountLamports,
        userSourceLiquidity: args.destinationAta,
        referrerAccount: args.referrerAccount,
        referrerTokenState: args.referrerTokenState,
        programId: args.programId,
    });
    return { flashBorrowIx, flashRepayIx };
};
exports.getFlashLoanInstructions = getFlashLoanInstructions;
const getBorrowFlashLoanInstruction = ({ userTransferAuthority, lendingMarketAuthority, lendingMarketAddress, reserve, amountLamports, destinationAta, referrerAccount, referrerTokenState, programId, }) => {
    const args = {
        liquidityAmount: new bn_js_1.default(amountLamports.floor().toString()),
    };
    const accounts = {
        userTransferAuthority,
        lendingMarketAuthority,
        lendingMarket: lendingMarketAddress,
        reserve: reserve.address,
        reserveLiquidityMint: reserve.getLiquidityMint(),
        reserveSourceLiquidity: reserve.state.liquidity.supplyVault,
        userDestinationLiquidity: destinationAta,
        referrerAccount,
        referrerTokenState,
        reserveLiquidityFeeReceiver: reserve.state.liquidity.feeVault,
        sysvarInfo: sysvars_1.SYSVAR_INSTRUCTIONS_ADDRESS,
        tokenProgram: reserve.getLiquidityTokenProgram(),
    };
    return (0, lib_1.flashBorrowReserveLiquidity)(args, accounts, undefined, programId);
};
exports.getBorrowFlashLoanInstruction = getBorrowFlashLoanInstruction;
const getRepayFlashLoanInstruction = ({ borrowIxIndex, userTransferAuthority, lendingMarketAuthority, lendingMarketAddress, reserve, amountLamports, userSourceLiquidity, referrerAccount, referrerTokenState, programId, }) => {
    const args = {
        borrowInstructionIndex: borrowIxIndex,
        liquidityAmount: new bn_js_1.default(amountLamports.floor().toString()),
    };
    const accounts = {
        userTransferAuthority,
        lendingMarketAuthority: lendingMarketAuthority,
        lendingMarket: lendingMarketAddress,
        reserve: reserve.address,
        reserveLiquidityMint: reserve.getLiquidityMint(),
        reserveDestinationLiquidity: reserve.state.liquidity.supplyVault,
        userSourceLiquidity: userSourceLiquidity,
        referrerAccount: referrerAccount,
        referrerTokenState: referrerTokenState,
        reserveLiquidityFeeReceiver: reserve.state.liquidity.feeVault,
        sysvarInfo: sysvars_1.SYSVAR_INSTRUCTIONS_ADDRESS,
        tokenProgram: reserve.getLiquidityTokenProgram(),
    };
    return (0, lib_1.flashRepayReserveLiquidity)(args, accounts, undefined, programId);
};
exports.getRepayFlashLoanInstruction = getRepayFlashLoanInstruction;
//# sourceMappingURL=instructions.js.map