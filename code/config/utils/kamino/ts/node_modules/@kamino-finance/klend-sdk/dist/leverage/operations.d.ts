import { Address, Instruction, Slot, Option, TransactionSigner } from '@solana/kit';
import { KaminoMarket, KaminoObligation, KaminoReserve } from '../classes';
import { ObligationType, ScopePriceRefreshConfig } from '../utils';
import { AdjustLeverageInitialInputs, AdjustLeverageIxsResponse, AdjustLeverageProps, AdjustLeverageSwapInputsProps, DepositLeverageInitialInputs, DepositWithLeverageProps, DepositWithLeverageSwapInputsProps, DepositLeverageIxsResponse, SwapInputs, SwapIxs, WithdrawLeverageCalcsResult, WithdrawLeverageInitialInputs, WithdrawLeverageIxsResponse, WithdrawWithLeverageProps, WithdrawWithLeverageSwapInputsProps, LeverageIxsOutput, FlashLoanInfo } from './types';
export declare const WITHDRAW_SLOT_OFFSET = 150;
export declare function getDepositWithLeverageSwapInputs<QuoteResponse>({ owner, kaminoMarket, debtTokenMint, collTokenMint, depositAmount, priceDebtToColl, slippagePct, obligation, referrer, currentSlot, targetLeverage, selectedTokenMint, obligationTypeTagOverride, scopeRefreshIx, budgetAndPriorityFeeIxs, quoteBufferBps, quoter, useV2Ixs, elevationGroupOverride, }: DepositWithLeverageSwapInputsProps<QuoteResponse>): Promise<{
    flashLoanInfo: FlashLoanInfo;
    swapInputs: SwapInputs;
    initialInputs: DepositLeverageInitialInputs<QuoteResponse>;
}>;
export declare function getDepositWithLeverageIxs<QuoteResponse>({ owner, kaminoMarket, debtTokenMint, collTokenMint, depositAmount, priceDebtToColl, slippagePct, obligation, referrer, currentSlot, targetLeverage, selectedTokenMint, obligationTypeTagOverride, scopeRefreshIx, budgetAndPriorityFeeIxs, quoteBufferBps, quoter, swapper, elevationGroupOverride, useV2Ixs, }: DepositWithLeverageProps<QuoteResponse>): Promise<Array<DepositLeverageIxsResponse<QuoteResponse>>>;
export declare function getWithdrawWithLeverageSwapInputs<QuoteResponse>({ owner, kaminoMarket, debtTokenMint, collTokenMint, deposited, borrowed, obligation, referrer, currentSlot, withdrawAmount, priceCollToDebt, slippagePct, isClosingPosition, selectedTokenMint, budgetAndPriorityFeeIxs, scopeRefreshIx, quoteBufferBps, quoter, useV2Ixs, userSolBalanceLamports, }: WithdrawWithLeverageSwapInputsProps<QuoteResponse>): Promise<{
    swapInputs: SwapInputs;
    flashLoanInfo: FlashLoanInfo;
    initialInputs: WithdrawLeverageInitialInputs<QuoteResponse>;
}>;
export declare function getWithdrawWithLeverageIxs<QuoteResponse>({ owner, kaminoMarket, debtTokenMint, collTokenMint, obligation, deposited, borrowed, referrer, currentSlot, withdrawAmount, priceCollToDebt, slippagePct, isClosingPosition, selectedTokenMint, budgetAndPriorityFeeIxs, scopeRefreshIx, quoteBufferBps, quoter, swapper, useV2Ixs, userSolBalanceLamports, }: WithdrawWithLeverageProps<QuoteResponse>): Promise<Array<WithdrawLeverageIxsResponse<QuoteResponse>>>;
export declare function buildWithdrawWithLeverageIxs<QuoteResponse>(market: KaminoMarket, debtReserve: KaminoReserve, collReserve: KaminoReserve, owner: TransactionSigner, obligation: KaminoObligation, referrer: Option<Address>, currentSlot: Slot, isClosingPosition: boolean, depositTokenIsSol: boolean, scopeRefreshIx: Instruction[], calcs: WithdrawLeverageCalcsResult, budgetAndPriorityFeeIxs: Instruction[] | undefined, swapQuoteIxsArray: SwapIxs<QuoteResponse>[], useV2Ixs: boolean, userSolBalanceLamports: number): Promise<LeverageIxsOutput[]>;
export declare function getAdjustLeverageSwapInputs<QuoteResponse>({ owner, kaminoMarket, debtTokenMint, collTokenMint, obligation, depositedLamports, borrowedLamports, referrer, currentSlot, targetLeverage, priceCollToDebt, priceDebtToColl, slippagePct, budgetAndPriorityFeeIxs, scopeRefreshIx, quoteBufferBps, quoter, useV2Ixs, withdrawSlotOffset, userSolBalanceLamports, }: AdjustLeverageSwapInputsProps<QuoteResponse>): Promise<{
    swapInputs: SwapInputs;
    flashLoanInfo: FlashLoanInfo;
    initialInputs: AdjustLeverageInitialInputs<QuoteResponse>;
}>;
export declare function getAdjustLeverageIxs<QuoteResponse>({ owner, kaminoMarket, debtTokenMint, collTokenMint, obligation, depositedLamports, borrowedLamports, referrer, currentSlot, targetLeverage, priceCollToDebt, priceDebtToColl, slippagePct, budgetAndPriorityFeeIxs, scopeRefreshIx, quoteBufferBps, quoter, swapper, useV2Ixs, withdrawSlotOffset, userSolBalanceLamports, }: AdjustLeverageProps<QuoteResponse>): Promise<Array<AdjustLeverageIxsResponse<QuoteResponse>>>;
export declare const getSetupIxs: (owner: TransactionSigner, collTokenMint: Address, collReserve: KaminoReserve, debtTokenMint: Address, debtReserve: KaminoReserve, budgetAndPriorityFeeIxs: Instruction[] | undefined) => Promise<{
    budgetIxs: Instruction<string, readonly (import("@solana/kit").AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>[];
    createAtasIxs: Instruction<string, readonly (import("@solana/kit").AccountMeta<string> | import("@solana/kit").AccountLookupMeta<string, string>)[]>[];
}>;
export declare const getScopeRefreshIxForObligationAndReserves: (market: KaminoMarket, collReserve: KaminoReserve, debtReserve: KaminoReserve, obligation: KaminoObligation | ObligationType | undefined, scopeRefreshConfig: ScopePriceRefreshConfig | undefined) => Promise<Instruction[]>;
//# sourceMappingURL=operations.d.ts.map