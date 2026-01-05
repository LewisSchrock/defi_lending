import { KaminoMarket, KaminoObligation, KaminoReserve } from '../classes';
import { SwapInputs, SwapQuote, SwapIxsProvider, SwapQuoteProvider, FlashLoanInfo } from '../leverage';
import { AddressLookupTable } from '@solana-program/address-lookup-table';
import { Account, Address, Instruction, Option, Slot, TransactionSigner } from '@solana/kit';
import Decimal from 'decimal.js';
export type RepayWithCollIxsResponse<QuoteResponse> = {
    ixs: Instruction[];
    lookupTables: Account<AddressLookupTable>[];
    flashLoanInfo: FlashLoanInfo;
    swapInputs: SwapInputs;
    initialInputs: RepayWithCollInitialInputs<QuoteResponse>;
    quote?: QuoteResponse;
};
export type RepayWithCollInitialInputs<QuoteResponse> = {
    debtRepayAmountLamports: Decimal;
    flashRepayAmountLamports: Decimal;
    /**
     * The amount of collateral available to withdraw, if this is less than the swap input amount, then the swap may fail due to slippage, or tokens may be debited from the user's ATA, so the caller needs to check this
     */
    maxCollateralWithdrawLamports: Decimal;
    /**
     * The quote from the provided quoter
     */
    swapQuote: SwapQuote<QuoteResponse>;
    currentSlot: Slot;
    klendAccounts: Array<Address>;
};
interface RepayWithCollSwapInputsProps<QuoteResponse> {
    kaminoMarket: KaminoMarket;
    debtTokenMint: Address;
    collTokenMint: Address;
    owner: TransactionSigner;
    obligation: KaminoObligation;
    referrer: Option<Address>;
    currentSlot: Slot;
    repayAmount: Decimal;
    isClosingPosition: boolean;
    budgetAndPriorityFeeIxs?: Instruction[];
    scopeRefreshIx: Instruction[];
    useV2Ixs: boolean;
    quoter: SwapQuoteProvider<QuoteResponse>;
}
export declare enum MaxWithdrawLtvCheck {
    MAX_LTV = 0,
    LIQUIDATION_THRESHOLD = 1
}
export declare function getRepayWithCollSwapInputs<QuoteResponse>({ collTokenMint, currentSlot, debtTokenMint, kaminoMarket, owner, obligation, quoter, referrer, repayAmount, isClosingPosition, budgetAndPriorityFeeIxs, scopeRefreshIx, useV2Ixs, }: RepayWithCollSwapInputsProps<QuoteResponse>): Promise<{
    swapInputs: SwapInputs;
    flashLoanInfo: FlashLoanInfo;
    initialInputs: RepayWithCollInitialInputs<QuoteResponse>;
}>;
interface RepayWithCollIxsProps<QuoteResponse> extends RepayWithCollSwapInputsProps<QuoteResponse> {
    swapper: SwapIxsProvider<QuoteResponse>;
    logger?: (msg: string, ...extra: any[]) => void;
}
export declare function getRepayWithCollIxs<QuoteResponse>({ repayAmount, isClosingPosition, budgetAndPriorityFeeIxs, collTokenMint, currentSlot, debtTokenMint, kaminoMarket, owner, obligation, quoter, swapper, referrer, scopeRefreshIx, useV2Ixs, logger, }: RepayWithCollIxsProps<QuoteResponse>): Promise<Array<RepayWithCollIxsResponse<QuoteResponse>>>;
export declare const getMaxWithdrawLtvCheck: (obligation: KaminoObligation, repayAmountLamports: Decimal, debtReserve: KaminoReserve, collWithdrawAmount: Decimal, collReserve: KaminoReserve) => MaxWithdrawLtvCheck;
export declare function getMaxCollateralFromRepayAmount(repayAmount: Decimal, debtReserve: KaminoReserve, collReserve: KaminoReserve): Decimal;
export {};
//# sourceMappingURL=repay_with_collateral_operations.d.ts.map